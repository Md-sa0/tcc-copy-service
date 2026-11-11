from uuid import UUID

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from src.models import AuthSession, User
from src.services.passwords import verify_password


async def test_registration_hashes_password_and_sets_hardened_session(stack):
    client, app, _, _ = stack
    async with app.state.sessions() as session:
        user = await session.scalar(select(User).where(User.email == "test@example.com"))
        auth_session = await session.scalar(
            select(AuthSession).where(AuthSession.user_id == user.id)
        )
        assert user.password_hash != "test-account-password"
        assert verify_password("test-account-password", user.password_hash)
        assert auth_session.token_hash != client.cookies["copylab_session"]
        assert auth_session.csrf_token_hash != client.cookies["copylab_csrf"]

    assert client.cookies["copylab_session"]
    assert client.cookies["copylab_csrf"]
    session_cookie = next(cookie for cookie in client.cookies.jar if cookie.name == "copylab_session")
    assert "HttpOnly" in session_cookie._rest
    assert (await client.get("/api/v1/auth/me")).json()["email"] == "test@example.com"


async def test_registration_requires_long_password_and_rejects_duplicate(stack):
    client, _, _, _ = stack
    weak = await client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert weak.status_code == 422
    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": "TEST@example.com", "password": "another-long-password"},
    )
    assert duplicate.status_code == 409


async def test_login_is_case_insensitive_and_logout_revokes_session(stack):
    client, _, _, _ = stack
    await client.post("/api/v1/auth/logout")
    client.headers.pop("X-CSRF-Token", None)
    denied = await client.get("/api/v1/products")
    assert denied.status_code == 401
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "Test@Example.com", "password": "test-account-password"},
    )
    assert login.status_code == 200
    client.headers["X-CSRF-Token"] = client.cookies["copylab_csrf"]
    assert (await client.get("/api/v1/auth/me")).status_code == 200
    wrong = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "incorrect-password"},
    )
    assert wrong.status_code == 401
    await client.post("/api/v1/auth/logout")
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_login_failures_are_scoped_to_email_and_cleared_on_success(stack):
    client, _, _, cache = stack
    await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "another-account-password"},
    )

    for email, password in [
        ("other@example.com", "incorrect-password"),
        ("other@example.com", "incorrect-password"),
        ("test@example.com", "incorrect-password"),
    ]:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 401

    failure_keys = await cache.keys("auth:login:failed:*")
    assert len(failure_keys) == 2
    assert sorted([int(await cache.get(key)) for key in failure_keys]) == [1, 2]

    success = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "test-account-password"},
    )
    assert success.status_code == 200
    remaining = await cache.keys("auth:login:failed:*")
    assert len(remaining) == 1
    assert int(await cache.get(remaining[0])) == 2


async def test_login_success_is_not_blocked_by_previous_failures(stack):
    client, _, _, cache = stack
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401

    [failure_key] = await cache.keys("auth:login:failed:*")
    await cache.set(failure_key, 100, ex=900)
    success = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "test-account-password"},
    )
    assert success.status_code == 200
    assert await cache.get(failure_key) is None


async def test_csrf_token_is_required_for_authenticated_mutations(stack, product_payload):
    client, _, _, _ = stack
    csrf = client.headers.pop("X-CSRF-Token")
    response = await client.post("/api/v1/products", json=product_payload)
    client.headers["X-CSRF-Token"] = csrf
    assert response.status_code == 403


async def test_public_accounts_cannot_access_each_others_data(stack, product_payload):
    owner_client, app, _, _ = stack
    created = await owner_client.post("/api/v1/products", json=product_payload)
    assert created.status_code == 201
    original_copy = (
        await owner_client.post(
            "/api/v1/copies/generate",
            json={"product_id": created.json()["id"]},
        )
    ).json()["copy"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as other_client:
        registration = await other_client.post(
            "/api/v1/auth/register",
            json={"email": "other@example.com", "password": "another-account-password"},
        )
        assert registration.status_code == 201
        other_client.headers["X-CSRF-Token"] = other_client.cookies["copylab_csrf"]
        assert (await other_client.get("/api/v1/products")).json()["total"] == 0
        assert (
            await other_client.get(f"/api/v1/products/{created.json()['id']}")
        ).status_code == 404
        revision_attempt = await other_client.post(
            f"/api/v1/copies/{original_copy['id']}/revisions",
            json={
                "instagram_copy": original_copy["instagram_copy"],
                "whatsapp_copy": original_copy["whatsapp_copy"],
                "seo_copy": original_copy["seo_copy"],
            },
        )
        assert revision_attempt.status_code == 404
        assert (await other_client.get("/api/v1/copies")).json()["total"] == 0
        assert (await other_client.get("/api/v1/metrics/requests")).json()["total"] > 0
        assert (await other_client.get("/api/v1/settings/provider")).json()["configured"] is False
        same_sku = await other_client.post("/api/v1/products", json=product_payload)
        assert same_sku.status_code == 201

    async with app.state.sessions() as session:
        users = list(await session.scalars(select(User)))
        assert {user.email for user in users} == {"test@example.com", "other@example.com"}
        assert all(isinstance(user.id, UUID) for user in users)


def test_scrypt_hashes_use_unique_salts():
    from src.services.passwords import hash_password

    first = hash_password("a sufficiently long password")
    second = hash_password("a sufficiently long password")
    assert first != second
    assert verify_password("a sufficiently long password", first)
    assert not verify_password("a different password", first)

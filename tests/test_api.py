import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from redis.exceptions import ConnectionError as RedisConnectionError

from src.services.llm import GenerationError


async def create(client, payload):
    response = await client.post("/api/v1/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_catalog_crud_and_validation(stack, product_payload):
    client, _, provider, _ = stack
    bad = await client.post("/api/v1/products", json={"sku": "MISSING"})
    assert bad.status_code == 422
    assert bad.headers["X-Cache-Status"] == "BYPASS"
    assert provider.calls == 0
    product = await create(client, product_payload)
    assert (await client.post("/api/v1/products", json=product_payload)).status_code == 409
    assert (await client.get("/api/v1/products", params={"sku": "TEST-01"})).json()["total"] == 1
    assert (await client.get("/api/v1/products", params={"q": "%"})).json()["total"] == 0
    updated = await client.put(
        f"/api/v1/products/{product['id']}", json={**product_payload, "name": "Novo nome"}
    )
    assert updated.json()["name"] == "Novo nome"
    assert (await client.delete(f"/api/v1/products/{product['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/products/{product['id']}")).status_code == 404


async def test_generation_cache_persistence_and_metrics(stack, product_payload):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    payload = {"product_id": product["id"], "tone_of_voice": "persuasivo"}
    first = await client.post("/api/v1/copies/generate", json=payload)
    assert first.status_code == 200, first.text
    second = await client.post("/api/v1/copies/generate", json=payload)
    assert second.status_code == 200
    assert first.headers["X-Cache-Status"] == "MISS"
    assert second.headers["X-Cache-Status"] == "HIT"
    assert first.json()["copy"] == second.json()["copy"]
    assert provider.calls == 1
    digest = first.json()["copy"]["input_hash"]
    assert 0 < await cache.ttl(f"copy:sha256:{digest}") <= 86400
    assert (await client.get("/api/v1/copies")).json()["total"] == 1
    summary = (await client.get("/api/v1/metrics/summary")).json()
    assert summary["cache_hit_ratio"] == 0.5
    assert summary["tokens_used"] == 120
    assert summary["estimated_tokens_saved"] == 120
    assert summary["estimated_token_savings_percent"] == 50
    history = (await client.get("/api/v1/metrics/requests", params={"kind": "generation"})).json()
    assert history["total"] == 2
    assert all(row["input_hash"] == digest for row in history["items"])
    assert all(row["request_id"] for row in history["items"])


async def test_same_hash_concurrency_calls_provider_once(stack, product_payload):
    client, _, provider, _ = stack
    product = await create(client, product_payload)
    results = await asyncio.gather(
        *(client.post("/api/v1/copies/generate", json={"product_id": product["id"]}) for _ in range(5))
    )
    assert [r.status_code for r in results] == [200] * 5, [r.text for r in results]
    assert provider.calls == 1
    assert sum(r.json()["cache_status"] == "MISS" for r in results) == 1


async def test_edit_tone_and_cache_expiration(stack, product_payload):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    payload = {"product_id": product["id"]}
    first = (await client.post("/api/v1/copies/generate", json=payload)).json()["copy"]
    tone = (
        await client.post("/api/v1/copies/generate", json={**payload, "tone_of_voice": "institucional"})
    ).json()["copy"]
    assert first["input_hash"] != tone["input_hash"]
    await client.put(f"/api/v1/products/{product['id']}", json={**product_payload, "name": "Fone revisado"})
    edited = (await client.post("/api/v1/copies/generate", json=payload)).json()["copy"]
    assert edited["input_hash"] != first["input_hash"]
    await cache.delete(f"copy:sha256:{edited['input_hash']}")
    expired = await client.post("/api/v1/copies/generate", json=payload)
    assert expired.json()["cache_status"] == "MISS"
    assert provider.calls == 4
    assert (await client.get("/api/v1/copies")).json()["total"] == 4
    assert (await client.get(f"/api/v1/copies/{first['id']}")).json()["input_snapshot"]["product"][
        "name"
    ] == product_payload["name"]


async def test_errors_are_audited_without_llm_calls(stack, product_payload):
    client, _, provider, _ = stack
    assert (await client.post("/api/v1/copies/generate", json={})).status_code == 422
    assert (await client.post("/api/v1/copies/generate", json={"product_id": "bad-uuid"})).status_code == 422
    assert (
        await client.post("/api/v1/copies/generate", json={"product_id": str(uuid4())})
    ).status_code == 404
    summary = (await client.get("/api/v1/metrics/summary")).json()
    assert summary["errors"] == 3 and summary["cache_hit_ratio"] is None
    assert provider.calls == 0


async def test_cache_outage_is_controlled(stack, product_payload, monkeypatch):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    monkeypatch.setattr(cache, "get", AsyncMock(side_effect=RedisConnectionError()))
    result = await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    assert result.status_code == 503
    assert provider.calls == 0


async def test_provider_failure_releases_lock(stack, product_payload, monkeypatch):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    monkeypatch.setattr(provider, "generate", AsyncMock(side_effect=GenerationError("Transitório", 503)))
    result = await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    assert result.status_code == 503
    assert await cache.keys("lock:*") == []
    assert (await client.get("/api/v1/copies")).json()["total"] == 0


async def test_corrupted_cache_regenerates_valid_content(stack, product_payload):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    payload = {"product_id": product["id"]}
    first = (await client.post("/api/v1/copies/generate", json=payload)).json()["copy"]
    await cache.setex(f"copy:sha256:{first['input_hash']}", 30, '{"broken":true}')
    response = await client.post("/api/v1/copies/generate", json=payload)
    assert response.status_code == 200 and response.json()["cache_status"] == "MISS"
    assert provider.calls == 2


async def test_cache_write_failure_preserves_durable_copy(stack, product_payload, monkeypatch):
    client, _, _, cache = stack
    product = await create(client, product_payload)
    monkeypatch.setattr(cache, "setex", AsyncMock(side_effect=RedisConnectionError()))
    response = await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    assert response.status_code == 200
    assert (await client.get("/api/v1/copies")).json()["total"] == 1


async def test_provider_timeout_returns_504_without_lock_leak(stack, product_payload, monkeypatch):
    client, _, provider, cache = stack
    product = await create(client, product_payload)
    monkeypatch.setattr(provider, "generate", AsyncMock(side_effect=TimeoutError()))
    response = await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    assert response.status_code == 504
    assert await cache.keys("lock:*") == []
    assert (await client.get("/api/v1/copies")).json()["total"] == 0


async def test_auth_and_deletion_cascade(stack, product_payload):
    client, app, _, _ = stack
    app.state.settings.api_key = SecretStr("test-secret")
    assert (await client.get("/api/v1/products")).status_code == 401
    assert (await client.get("/health")).status_code == 200
    client.headers["X-API-Key"] = "test-secret"
    product = await create(client, product_payload)
    await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    await client.delete(f"/api/v1/products/{product['id']}")
    assert (await client.get("/api/v1/copies")).json()["total"] == 0
    assert (
        await client.post("/api/v1/copies/generate", json={"product_id": product["id"]})
    ).status_code == 404


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "   "),
        ("name", 123),
        ("sku", "bad sku"),
        ("key_benefits", []),
        ("key_benefits", ["x", " x "]),
        ("technical_attributes", {}),
        ("technical_attributes", {"cor": 10}),
        ("technical_attributes", {"cor": "azul", " cor ": "verde"}),
        ("extra", "unknown"),
    ],
)
async def test_strict_product_contract(stack, product_payload, field, value):
    client, _, provider, _ = stack
    result = await client.post("/api/v1/products", json={**product_payload, field: value})
    assert result.status_code == 422, result.text
    assert provider.calls == 0

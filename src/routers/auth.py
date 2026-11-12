import asyncio
import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session, require_authenticated_user
from src.models import AuthSession, User
from src.services.passwords import hash_password, token_hash, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticação"])
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
LOGIN_FAILURE_WINDOW_SECONDS = 15 * 60
_DUMMY_PASSWORD_HASH = hash_password("password-check-for-unknown-accounts")
_INCREMENT_LOGIN_FAILURES = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""
logger = logging.getLogger(__name__)


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if (
            not separator
            or not local
            or not domain
            or "." not in domain
            or any(character.isspace() for character in normalized)
        ):
            raise ValueError("Informe um endereço de e-mail válido.")
        return normalized


class Registration(Credentials):
    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value) < 12:
            raise ValueError("Use uma senha com pelo menos 12 caracteres.")
        return value


async def rate_limit(request: Request, action: str, limit: int, window: int) -> None:
    client = request.client.host if request.client else "unknown"
    identity = hashlib.sha256(f"{action}:{client}".encode()).hexdigest()
    key = f"auth:rate:{identity}"
    try:
        count = await request.app.state.cache.incr(key)
        if count == 1:
            await request.app.state.cache.expire(key, window)
    except RedisError as exc:
        raise HTTPException(503, "Autenticação temporariamente indisponível.") from exc
    if count > limit:
        raise HTTPException(429, "Muitas tentativas. Aguarde antes de tentar novamente.")


def login_failure_key(request: Request, email: str) -> str:
    client = request.client.host if request.client else "unknown"
    identity = hashlib.sha256(f"{email}:{client}".encode()).hexdigest()
    return f"auth:login:failed:{identity}"


async def record_login_failure(request: Request, email: str) -> int:
    try:
        return int(
            await request.app.state.cache.eval(
                _INCREMENT_LOGIN_FAILURES,
                1,
                login_failure_key(request, email),
                LOGIN_FAILURE_WINDOW_SECONDS,
            )
        )
    except RedisError:
        logger.warning("login_failure_counter_unavailable")
        return 0


async def clear_login_failures(request: Request, email: str) -> None:
    try:
        await request.app.state.cache.delete(login_failure_key(request, email))
    except RedisError:
        logger.warning("login_failure_counter_clear_failed")


def login_failure_delay(failures: int) -> float:
    if failures < 4:
        return 0
    return min(2.0, 0.25 * (failures - 3))


def validate_request_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        if request.headers.get("sec-fetch-site") == "cross-site":
            raise HTTPException(403, "Origem não autorizada.")
        return
    allowed = set(request.app.state.settings.cors_origins)
    if origin not in allowed:
        raise HTTPException(403, "Origem não autorizada.")


def set_session_cookies(response: Response, session_token: str, csrf_token: str, request: Request):
    secure = (
        request.app.state.settings.app_env == "production"
        or request.url.scheme == "https"
    )
    response.set_cookie(
        "copylab_session",
        session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "copylab_csrf",
        csrf_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=False,
        secure=secure,
        samesite="lax",
        path="/",
    )


async def create_session(user: User, request: Request, response: Response, session: AsyncSession):
    raw_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=token_hash(raw_token),
        csrf_token_hash=token_hash(csrf_token),
        expires_at=datetime.now(UTC) + timedelta(seconds=SESSION_TTL_SECONDS),
    )
    session.add(auth_session)
    await session.commit()
    set_session_cookies(response, raw_token, csrf_token, request)
    return {"id": str(user.id), "email": user.email}


@router.post("/register", status_code=201)
async def register(
    payload: Registration,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    validate_request_origin(request)
    await rate_limit(request, "register", 10, 3600)
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Já existe uma conta com este e-mail.") from exc
    account = await create_session(user, request, response, session)
    return {"user": account}


@router.post("/login")
async def login(
    payload: Credentials,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    validate_request_origin(request)
    user = await session.scalar(select(User).where(User.email == payload.email))
    password_hash = user.password_hash if user and user.is_active else _DUMMY_PASSWORD_HASH
    valid = verify_password(payload.password, password_hash)
    if user is None or not user.is_active or not valid:
        failures = await record_login_failure(request, payload.email)
        delay = login_failure_delay(failures)
        if delay:
            await asyncio.sleep(delay)
        raise HTTPException(401, "E-mail ou senha incorretos.")
    await clear_login_failures(request, payload.email)
    account = await create_session(user, request, response, session)
    return {"user": account}


@router.get("/me")
async def me(user: Annotated[User, Depends(require_authenticated_user)]):
    return {"id": str(user.id), "email": user.email}


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    user: Annotated[User, Depends(require_authenticated_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    auth_session = request.state.auth_session
    await session.delete(auth_session)
    await session.commit()
    secure = (
        request.app.state.settings.app_env == "production"
        or request.url.scheme == "https"
    )
    response.delete_cookie("copylab_session", path="/", secure=secure, httponly=True, samesite="lax")
    response.delete_cookie("copylab_csrf", path="/", secure=secure, httponly=False, samesite="lax")

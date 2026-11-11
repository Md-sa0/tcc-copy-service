import hmac
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AuthSession, User
from src.services.passwords import token_hash


async def get_session(request: Request):
    async with request.app.state.sessions() as session:
        yield session


async def require_authenticated_user(
    request: Request, session: AsyncSession = Depends(get_session)
) -> User:
    raw_token = request.cookies.get("copylab_session")
    if not raw_token:
        raise HTTPException(401, "Faça login para continuar.")
    auth_session = await session.scalar(
        select(AuthSession).where(AuthSession.token_hash == token_hash(raw_token))
    )
    if auth_session is None:
        raise HTTPException(401, "Sessão inválida ou expirada.")
    expires_at = auth_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        await session.delete(auth_session)
        await session.commit()
        raise HTTPException(401, "Sessão inválida ou expirada.")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        csrf_cookie = request.cookies.get("copylab_csrf", "")
        csrf_header = request.headers.get("x-csrf-token", "")
        if (
            not csrf_cookie
            or not csrf_header
            or not hmac.compare_digest(csrf_cookie, csrf_header)
            or not hmac.compare_digest(
                token_hash(csrf_cookie), auth_session.csrf_token_hash
            )
        ):
            raise HTTPException(403, "Token de segurança inválido. Atualize a página.")
    user = await session.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Conta indisponível.")
    request.state.user = user
    request.state.user_id = user.id
    request.state.auth_session = auth_session
    return user

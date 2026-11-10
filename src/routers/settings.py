import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session
from src.models import ProviderCredential
from src.services.llm import OpenAICompatibleProvider

router = APIRouter(prefix="/settings", tags=["Settings"])


class ProviderConfigInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    api_key: SecretStr = Field(min_length=1, max_length=4096)
    base_url: str = Field(min_length=10, max_length=500)
    model: str = Field(min_length=1, max_length=200)


def encryption_fernet(request: Request) -> Fernet:
    value = request.app.state.settings.settings_encryption_key.get_secret_value()
    if not value:
        raise HTTPException(
            503,
            "Configure SETTINGS_ENCRYPTION_KEY no .env antes de salvar a chave do provedor.",
        )
    try:
        return Fernet(value.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise HTTPException(503, "SETTINGS_ENCRYPTION_KEY inválida.") from exc


def require_same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    allowed = request.app.state.settings.cors_origins
    local_origins = {
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
    }
    if (
        not origin
        or "*" in allowed
        or (origin not in allowed and origin not in local_origins)
    ):
        raise HTTPException(403, "Origem não autorizada para alterar configurações.")


async def validate_provider_url(value: str) -> str:
    parsed = urlsplit(value.strip())
    try:
        invalid_authority = (
            parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
        )
    except ValueError as exc:
        raise HTTPException(422, "URL do provedor inválida.") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or invalid_authority
        or parsed.query
        or parsed.fragment
    ):
        raise HTTPException(422, "Informe uma URL HTTPS pública do provedor.")

    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise HTTPException(422, "A URL deve apontar para um host público.")
    try:
        addresses = await asyncio.to_thread(
            socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM
        )
    except OSError as exc:
        raise HTTPException(422, "Não foi possível verificar o host do provedor.") from exc
    if not addresses or any(
        not ipaddress.ip_address(row[4][0]).is_global for row in addresses
    ):
        raise HTTPException(422, "A URL deve apontar somente para endereços públicos.")
    return value.strip().rstrip("/")


@router.get("/provider")
async def provider_status(request: Request, session: AsyncSession = Depends(get_session)):
    credential = await session.get(ProviderCredential, 1)
    return {
        "configured": credential is not None
        and request.app.state.provider_config_error is None,
        "locked": request.app.state.provider_config_error is not None,
        "provider": request.app.state.runtime_provider,
        "model": request.app.state.runtime_model_name,
        "base_url": credential.base_url if credential else None,
        "error": request.app.state.provider_config_error,
    }


@router.put("/provider")
async def update_provider(
    payload: ProviderConfigInput,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    require_same_origin(request)
    fernet = encryption_fernet(request)
    base_url = await validate_provider_url(payload.base_url)
    api_key = payload.api_key.get_secret_value().strip()
    model = payload.model.strip()
    if not api_key or not model:
        raise HTTPException(422, "Informe a chave e o modelo do provedor.")

    encrypted_key = fernet.encrypt(api_key.encode("utf-8")).decode("ascii")
    credential = await session.get(ProviderCredential, 1)
    if credential is None:
        credential = ProviderCredential(
            id=1,
            encrypted_api_key=encrypted_key,
            base_url=base_url,
            model=model,
        )
        session.add(credential)
    else:
        credential.encrypted_api_key = encrypted_key
        credential.base_url = base_url
        credential.model = model
    await session.commit()

    provider = OpenAICompatibleProvider(
        api_key=api_key,
        base_url=base_url,
        model=model,
    )
    await request.app.state.provider_manager.replace(provider)
    request.app.state.provider_config_error = None
    request.app.state.runtime_provider = "openai-compatible"
    request.app.state.runtime_model_name = model
    return {
        "configured": True,
        "locked": False,
        "provider": "openai-compatible",
        "model": model,
        "base_url": base_url,
        "error": None,
    }

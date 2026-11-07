import secrets

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def authenticate(request: Request, key: str | None = Security(api_key_header)):
    expected = request.app.state.settings.api_key.get_secret_value()
    if expected and not secrets.compare_digest(key or "", expected):
        raise HTTPException(401, "Chave de acesso inválida")


async def get_session(request: Request):
    async with request.app.state.sessions() as session:
        yield session

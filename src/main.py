import asyncio
import logging
from contextlib import asynccontextmanager

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.core.cache import create_cache
from src.core.config import Settings, get_settings
from src.core.database import create_database
from src.core.dependencies import authenticate
from src.core.middleware import TelemetryMiddleware
from src.models import ProviderCredential
from src.routers import copies, metrics, products, settings as settings_router
from src.services.llm import MockProvider, OpenAICompatibleProvider
from src.services.provider_manager import ProviderManager


def create_app(settings: Settings | None = None, *, sessions=None, cache=None, provider=None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        engine = None
        if sessions is None:
            engine, app.state.sessions = create_database(settings.database_url)
        else:
            app.state.sessions = sessions
        app.state.cache = cache if cache is not None else create_cache(settings.redis_url)
        async with app.state.sessions() as session:
            app.state.database_kind = session.bind.dialect.name
        app.state.cache_kind = (
            "simulado" if type(app.state.cache).__module__.startswith("fakeredis") else "redis"
        )
        provider_instance = provider if provider is not None else MockProvider()
        app.state.runtime_provider = "mock"
        app.state.runtime_model_name = settings.model_name
        app.state.provider_config_error = None
        async with app.state.sessions() as session:
            credential = await session.get(ProviderCredential, 1)
            if credential is not None:
                encryption_key = settings.settings_encryption_key.get_secret_value()
                if not encryption_key:
                    app.state.provider_config_error = (
                        "A chave criptografada do provedor não pode ser carregada. "
                        "Configure SETTINGS_ENCRYPTION_KEY no .env e reinicie a API."
                    )
                else:
                    try:
                        api_key = Fernet(encryption_key.encode("ascii")).decrypt(
                            credential.encrypted_api_key.encode("ascii")
                        ).decode("utf-8")
                        provider_instance = OpenAICompatibleProvider(
                            api_key=api_key,
                            base_url=credential.base_url,
                            model=credential.model,
                        )
                        app.state.runtime_provider = "openai-compatible"
                        app.state.runtime_model_name = credential.model
                    except (ValueError, UnicodeEncodeError, InvalidToken) as exc:
                        app.state.provider_config_error = (
                            "A chave criptografada não pôde ser descriptografada. "
                            "Verifique SETTINGS_ENCRYPTION_KEY."
                        )
                        logging.error("provider_configuration_decryption_failed")
        app.state.provider_manager = ProviderManager(provider_instance)
        try:
            yield
        finally:
            await app.state.provider_manager.close()
            await app.state.cache.aclose()
            if engine is not None:
                await engine.dispose()

    app = FastAPI(title="CopyLab · Retail Content API", version="2.0.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(TelemetryMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "X-API-Key"],
        expose_headers=["X-Process-Time", "X-Cache-Status", "X-Request-ID"],
    )
    api = APIRouter(prefix="/api/v1", dependencies=[Depends(authenticate)])
    api.include_router(products.router)
    api.include_router(copies.router)
    api.include_router(metrics.router)
    api.include_router(settings_router.router)
    app.include_router(api)

    @app.get("/health", tags=["Operação"])
    async def health():
        return {
            "status": "online",
            "provider": app.state.runtime_provider,
            "model": app.state.runtime_model_name,
            "database": app.state.database_kind,
            "cache": app.state.cache_kind,
        }

    @app.get("/health/ready", tags=["Operação"])
    async def ready():
        try:
            async with asyncio.timeout(4), app.state.sessions() as session:
                await session.execute(text("SELECT 1 FROM products LIMIT 1"))
                await app.state.cache.ping()
        except Exception as exc:
            raise HTTPException(503, "Dependências indisponíveis ou migrações pendentes") from exc
        return {"status": "ready"}

    return app


app = create_app()

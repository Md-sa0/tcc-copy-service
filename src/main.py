import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.core.cache import create_cache
from src.core.config import Settings, get_settings
from src.core.database import create_database
from src.core.dependencies import authenticate
from src.core.middleware import TelemetryMiddleware
from src.routers import copies, metrics, products
from src.services.llm import GeminiProvider, MockProvider


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
        app.state.provider = (
            provider
            if provider is not None
            else (GeminiProvider(settings) if settings.llm_provider == "gemini" else MockProvider())
        )
        try:
            yield
        finally:
            await app.state.provider.close()
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
    app.include_router(api)

    @app.get("/health", tags=["Operação"])
    async def health():
        return {"status": "online", "provider": settings.llm_provider, "model": settings.model_name}

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

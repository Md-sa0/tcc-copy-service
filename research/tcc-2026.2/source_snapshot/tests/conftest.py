import os

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import Settings
from src.main import create_app
from src.models import Base
from src.services.llm import MockProvider


class CountingProvider(MockProvider):
    def __init__(self):
        self.calls = 0

    async def generate(self, snapshot):
        self.calls += 1
        result = await super().generate(snapshot)
        result.tokens = 120
        return result


@pytest.fixture
async def stack(tmp_path):
    # Dedicated CI databases only; never default to the user's application database.
    db_url = os.getenv("TEST_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    engine = create_async_engine(db_url)
    if db_url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def enable_fk(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    if os.getenv("TEST_REDIS_URL"):
        from src.core.cache import create_cache

        cache = create_cache(os.environ["TEST_REDIS_URL"])
        await cache.flushdb()
    else:
        cache = FakeRedis(decode_responses=True)
    settings = Settings(_env_file=None, app_env="test", llm_provider="mock", api_key="", retry_base_seconds=0)
    provider = CountingProvider()
    app = create_app(settings, sessions=sessions, cache=cache, provider=provider)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield client, app, provider, cache
    await engine.dispose()


@pytest.fixture
def product_payload():
    return {
        "sku": "TEST-01",
        "name": "Fone Bluetooth",
        "category": "Eletrônicos",
        "target_audience": "Estudantes",
        "technical_attributes": {"cor": "azul", "autonomia": "24 horas"},
        "key_benefits": ["Sem fios", "Portátil"],
    }

import pytest

from src.core.database import create_database


@pytest.mark.parametrize("scheme", ["postgres://", "postgresql://"])
async def test_create_database_accepts_render_postgres_url(scheme):
    engine, _ = create_database(f"{scheme}user:password@localhost/copy")
    try:
        assert engine.url.drivername == "postgresql+asyncpg"
    finally:
        await engine.dispose()

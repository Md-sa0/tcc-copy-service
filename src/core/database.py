from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def create_database(url: str):
    parsed_url = make_url(url)
    if parsed_url.drivername in {"postgres", "postgresql"}:
        parsed_url = parsed_url.set(drivername="postgresql+asyncpg")
    engine = create_async_engine(parsed_url, pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)

"""Isolated browser QA server. SQLite + FakeRedis, never the production data stack."""

import argparse
import asyncio
from pathlib import Path

import uvicorn
from fakeredis.aioredis import FakeRedis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.staticfiles import StaticFiles

from src.core.config import Settings
from src.main import create_app
from src.models import Base


async def main(port: int = 8000, serve_frontend: bool = False):
    frontend_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
    if serve_frontend and not (frontend_dist / "index.html").is_file():
        raise SystemExit("Frontend ainda não compilado. Execute npm ci e npm run build na pasta frontend.")
    Path("artifacts").mkdir(exist_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///artifacts/ui-preview.db")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    app = create_app(
        Settings(_env_file=None, app_env="test", llm_provider="mock", api_key=""),
        sessions=async_sessionmaker(engine, expire_on_commit=False),
        cache=FakeRedis(decode_responses=True),
    )
    if serve_frontend:
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    print(f"Demonstração local: http://localhost:{port}", flush=True)
    print("SQLite + cache simulado + IA simulada. Ctrl+C para encerrar.", flush=True)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    try:
        await server.serve()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--serve-frontend", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.port, args.serve_frontend))

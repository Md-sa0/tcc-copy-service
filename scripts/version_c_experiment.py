"""Equivalent authenticated-route comparison; no external network or real tokens."""
import asyncio
import csv
import json
import platform
import random
import socket
import statistics
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import httpx
from cryptography.fernet import Fernet
from fakeredis.aioredis import FakeRedis
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config import Settings
from src.main import create_app
from src.models import Base
from src.schemas.copies import GenerateResponse
from src.services.llm import MockProvider, OpenAICompatibleProvider

OUT = Path("research/version-c")
CATALOG = [
    {"sku": f"C-{i}", "name": name, "category": category,
     "target_audience": "Consumidores adultos", "technical_attributes": {"material": material},
     "key_benefits": ["Uso diário", "Transporte prático"]}
    for i, (name, category, material) in enumerate([
        ("Fone portátil", "Eletrônicos", "plástico"),
        ("Necessaire", "Cosméticos", "tecido"),
        ("Camiseta", "Vestuário", "algodão"),
        ("Garrafa", "Casa", "aço"),
        ("Estojo", "Papelaria", "tecido"),
    ])
]


async def collect(round_id, arm, commit):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        body = json.loads(request.content)
        content = await MockProvider().generate(json.loads(body["messages"][1]["content"]))
        return httpx.Response(200, json={
            "choices": [{"message": {"content": content.content.model_dump_json()}}],
            "usage": {"total_tokens": 0},
        })

    class TransportProvider(OpenAICompatibleProvider):
        def __init__(self, *, api_key, base_url, model):
            self.model = model
            self.client = httpx.AsyncClient(base_url=base_url.rstrip("/") + "/",
                                           transport=httpx.MockTransport(handler))

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        engine = create_async_engine(f"sqlite+aiosqlite:///{Path(tmp)/'experiment.db'}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        settings = Settings(_env_file=None, app_env="test",
                            settings_encryption_key=SecretStr(Fernet.generate_key().decode()))
        app = create_app(settings, sessions=sessions, cache=FakeRedis(decode_responses=True))
        try:
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post("/api/v1/auth/register", json={
                        "email": "experiment@example.test", "password": "experiment-local-only-2026"})
                    assert response.status_code == 201
                    client.headers["X-CSRF-Token"] = client.cookies["copylab_csrf"]
                    with patch("src.routers.settings.socket.getaddrinfo", return_value=[
                        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
                    ]):
                        response = await client.put("/api/v1/settings/provider", json={
                            "api_key": "fictional-experiment-key", "base_url": "https://mock.example/v1",
                            "model": "mock-deterministic-v1"}, headers={"Origin": "http://127.0.0.1:8080"})
                        assert response.status_code == 200
                    products = []
                    for item in CATALOG:
                        response = await client.post("/api/v1/products", json=item)
                        assert response.status_code == 201
                        products.append(response.json())
                    with patch("src.services.generation.OpenAICompatibleProvider", TransportProvider):
                        # One unmeasured warm-up per arm, followed by cache reset.
                        response = await client.post("/api/v1/copies/generate", json={
                            "product_id": products[0]["id"], "tone_of_voice": "persuasivo"})
                        assert response.status_code == 200
                        await app.state.cache.flushdb()
                        calls = 0
                        for product in products:
                            for repetition in range(5):
                                before = calls
                                started = time.perf_counter_ns()
                                response = await client.post("/api/v1/copies/generate", json={
                                    "product_id": product["id"], "tone_of_voice": "persuasivo",
                                    "force_regenerate": arm == "forced"})
                                elapsed = (time.perf_counter_ns() - started) / 1e6
                                valid = False
                                try:
                                    output = GenerateResponse.model_validate(response.json())
                                    valid = str(output.generated_copy.product_id) == product["id"]
                                except ValueError:
                                    pass
                                rows.append({"round": round_id, "arm": arm, "sku": product["sku"],
                                             "repetition": repetition, "elapsed_ms": elapsed,
                                             "http_status": response.status_code,
                                             "cache_status": response.headers.get("X-Cache-Status"),
                                             "provider_calls": calls-before, "contract_valid": valid,
                                             "code_commit": commit})
        finally:
            await engine.dispose()
    return rows


async def main():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    rng = random.Random(20261112)
    rows, order = [], []
    for round_id in range(1, 4):
        arms = ["reuse", "forced"]
        rng.shuffle(arms)
        order.append(arms)
        for arm in arms:
            rows.extend(await collect(round_id, arm, commit))
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT/"observations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"code_commit": commit, "timestamp_utc": datetime.now(UTC).isoformat(),
               "python": platform.python_version(), "platform": platform.platform(), "seed": 20261112,
               "order": order, "catalog": CATALOG, "provider": "MockTransport + MockProvider (80 ms programmed)",
               "database": "SQLite file per arm/round", "cache": "FakeRedis per arm/round",
               "timer": "perf_counter_ns around awaited authenticated HTTPX ASGI request including telemetry; excludes setup and client-side validation",
               "forced_semantics": "force_regenerate bypasses reads, acquires lock, calls provider, persists and refreshes cache",
               "warmup": "one unmeasured generation per arm/round, then flush cache; excluded from call counts",
               "real_tokens": 0, "arms": {}}
    for arm in ["reuse", "forced"]:
        subset = [r for r in rows if r["arm"] == arm]
        summary["arms"][arm] = {"n": len(subset), "mean_ms": statistics.mean(r["elapsed_ms"] for r in subset),
                                "provider_calls": sum(r["provider_calls"] for r in subset),
                                "hits": sum(r["cache_status"] == "HIT" for r in subset),
                                "valid": sum(r["contract_valid"] for r in subset),
                                "http_200": sum(r["http_status"] == 200 for r in subset)}
    summary["reduction_percent"] = 100*(1-summary["arms"]["reuse"]["mean_ms"]/summary["arms"]["forced"]["mean_ms"])
    (OUT/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    assert all(r["http_status"] == 200 and r["contract_valid"] for r in rows)
    assert summary["arms"]["reuse"]["hits"] == 60
    assert summary["arms"]["reuse"]["provider_calls"] == 15
    assert summary["arms"]["forced"]["provider_calls"] == 75
    print(json.dumps(summary["arms"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())

"""Reproducible HTTP benchmark; outputs raw observations and per-run statistics."""

import argparse
import asyncio
import csv
import json
import math
import os
import platform
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx

from scripts.seed_data import PRODUCTS


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile_value
    left, right = math.floor(position), math.ceil(position)
    return ordered[left] + (ordered[right] - ordered[left]) * (position - left)


def summarize(rows: list[dict]) -> dict:
    valid = [row for row in rows if row["status_code"] == 200]
    hit = [row["client_latency_ms"] for row in valid if row["cache_status"] == "HIT"]
    miss = [row["client_latency_ms"] for row in valid if row["cache_status"] == "MISS"]
    used = sum(row["tokens_used"] for row in valid)
    saved = sum(row["estimated_tokens_saved"] for row in valid)
    result = {
        "requests": len(rows),
        "successful": len(valid),
        "errors": len(rows) - len(valid),
        "cache_hit_ratio": len(hit) / len(valid) if valid else None,
        "tokens_used": used,
        "estimated_tokens_saved": saved,
        "estimated_token_savings_percent": saved / (used + saved) * 100 if used + saved else None,
        "latency_savings_percent": (1 - statistics.mean(hit) / statistics.mean(miss)) * 100
        if hit and miss
        else None,
    }
    for name, values in (("hit", hit), ("miss", miss)):
        result[name] = {
            "n": len(values),
            "mean_ms": statistics.mean(values) if values else None,
            "median_ms": statistics.median(values) if values else None,
            "stdev_ms": statistics.stdev(values) if len(values) > 1 else None,
            "p95_ms": percentile(values, 0.95),
            "p99_ms": percentile(values, 0.99),
        }
    return result


async def run(args):
    run_id = uuid4().hex[:12]
    folder = Path(args.output) / run_id
    folder.mkdir(parents=True, exist_ok=False)
    headers = {"X-API-Key": os.getenv("API_KEY", "")}
    started = datetime.now(UTC).isoformat()
    async with httpx.AsyncClient(base_url=args.url.rstrip("/"), headers=headers, timeout=270) as client:
        health_response = await client.get("/health")
        health_response.raise_for_status()
        health = health_response.json()
        products = []
        for original in PRODUCTS:
            data = {**original, "technical_attributes": dict(original["technical_attributes"])}
            if not args.reuse_catalog:
                data["sku"] = f"{original['sku']}-{run_id}"
            existing = await client.get("/api/v1/products", params={"sku": data["sku"]})
            existing.raise_for_status()
            matches = existing.json()["items"]
            if matches:
                products.append(matches[0])
            else:
                response = await client.post("/api/v1/products", json=data)
                response.raise_for_status()
                products.append(response.json())
        if args.seed_only:
            (folder / "products.json").write_text(
                json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"10 produtos disponíveis. Arquivo: {folder}")
            return
        semaphore = asyncio.Semaphore(args.concurrency)
        observations = []

        async def request_copy(product, phase, repeat):
            async with semaphore:
                t0 = time.perf_counter()
                row = {
                    "run_id": run_id,
                    "phase": phase,
                    "repeat": repeat,
                    "sku": product["sku"],
                    "product_id": product["id"],
                    "status_code": 0,
                    "cache_status": "ERROR",
                    "client_latency_ms": 0.0,
                    "api_latency_ms": None,
                    "input_hash": "",
                    "request_id": "",
                    "model": health["model"],
                    "tokens_used": 0,
                    "estimated_tokens_saved": 0,
                    "error": "",
                }
                try:
                    response = await client.post(
                        "/api/v1/copies/generate",
                        json={"product_id": product["id"], "tone_of_voice": "persuasivo"},
                    )
                    row.update(
                        status_code=response.status_code,
                        cache_status=response.headers.get("X-Cache-Status", "BYPASS"),
                        api_latency_ms=float(response.headers.get("X-Process-Time", 0)) * 1000,
                        request_id=response.headers.get("X-Request-ID", ""),
                    )
                    if response.status_code == 200:
                        body = response.json()
                        row.update(input_hash=body["copy"]["input_hash"], model=body["copy"]["model_name"])
                        key = "estimated_tokens_saved" if body["cache_status"] == "HIT" else "tokens_used"
                        row[key] = body["copy"]["tokens_used"]
                    else:
                        row["error"] = f"HTTP {response.status_code}"
                except httpx.HTTPError as exc:
                    row["error"] = type(exc).__name__
                row["client_latency_ms"] = round((time.perf_counter() - t0) * 1000, 3)
                observations.append(row)
                if args.pause:
                    await asyncio.sleep(args.pause)

        # Barrier: all first-generation requests finish before any warm-cache request starts.
        await asyncio.gather(*(request_copy(p, "cold", 0) for p in products))
        for repeat in range(1, args.repeats + 1):
            await asyncio.gather(*(request_copy(p, "warm", repeat) for p in products))
        summary = summarize(observations)
        metadata = {
            "run_id": run_id,
            "started_at": started,
            "finished_at": datetime.now(UTC).isoformat(),
            "provider": health["provider"],
            "model": health["model"],
            "python": platform.python_version(),
            "concurrency": args.concurrency,
            "warm_repeats": args.repeats,
            "pause_seconds": args.pause,
            "fresh_products": not args.reuse_catalog,
            "summary": summary,
            "limitations": "Tokens economizados são estimados; mock não representa inferência real. Cold/warm são fases, não rótulos presumidos de cache.",
        }
        with (folder / "requests.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=observations[0].keys())
            writer.writeheader()
            writer.writerows(observations)
        (folder / "results.json").write_text(
            json.dumps({**metadata, "observations": observations}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        table = [
            "# Benchmark CopyLab",
            "",
            f"Execução: `{run_id}` · Provedor: `{health['provider']}` · Modelo: `{health['model']}`",
            "",
            "| Cache observado | n | Média (ms) | Mediana (ms) | p95 (ms) | p99 (ms) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
        for status in ("miss", "hit"):
            values = summary[status]
            formatted = [str(values["n"])] + [
                f"{values[k]:.3f}" if values[k] is not None else "—"
                for k in ("mean_ms", "median_ms", "p95_ms", "p99_ms")
            ]
            table.append(f"| {status.upper()} | " + " | ".join(formatted) + " |")
        table.extend(
            [
                "",
                f"Falhas: {summary['errors']}. Consulte requests.csv para cada observação.",
                "",
                metadata["limitations"],
            ]
        )
        (folder / "report.md").write_text("\n".join(table), encoding="utf-8")
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        print(f"Artefatos: {folder.resolve()}")
        if summary["errors"]:
            raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8080")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--pause", type=float, default=0.25)
    parser.add_argument("--output", default="artifacts/benchmarks")
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument(
        "--reuse-catalog", action="store_true", help="Reutiliza SKUs; a primeira rodada poderá ter cache hit"
    )
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 50 or not 1 <= args.repeats <= 100 or args.pause < 0:
        parser.error("concorrência: 1..50; repetições: 1..100; pausa >= 0")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

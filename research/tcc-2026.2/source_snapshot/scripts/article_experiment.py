"""Isolated, reproducible application experiment. No network LLM or user database.

Run: .venv/Scripts/python.exe -m scripts.article_experiment
The mock's intentional 80 ms wait is NOT a measurement of Gemini latency.
"""
import asyncio
import argparse
import csv
import hashlib
import importlib.metadata
import json
import logging
import platform
import random
import statistics
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from scripts.seed_data import PRODUCTS
from seed_and_benchmark import percentile
from src.core.config import Settings
from src.main import create_app
from src.models import Base, GeneratedCopy, Product
from src.schemas.copies import GenerateResponse
from src.services.hashing import canonical_input
from src.services.llm import MockProvider


class CountedMock(MockProvider):
    def __init__(self):
        self.calls = 0

    async def generate(self, snapshot):
        self.calls += 1
        return await super().generate(snapshot)


def stats(rows):
    values = [r['latency_ms'] for r in rows]
    return dict(n=len(values), mean_ms=statistics.mean(values),
                median_ms=statistics.median(values), stdev_ms=statistics.stdev(values),
                p95_ms=percentile(values, .95), minimum_ms=min(values), maximum_ms=max(values))


async def main(seed: int = 20261106, rounds: int = 3, allow_dirty: bool = False):
    git_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    git_status = subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()
    if git_status and not allow_dirty:
        raise SystemExit('A coleta exige checkout limpo. Use um worktree da tag ou --allow-dirty apenas para diagnóstico.')
    output = Path('artifacts/article-experiment') / datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True, exist_ok=False)
    rows, baselines, batches, persistence = [], [], [], []
    tones = ['persuasivo', 'descontraído', 'institucional', 'promocional']
    with tempfile.TemporaryDirectory(prefix='copylab-article-') as temp:
        for run in range(1, rounds + 1):
            db = Path(temp) / f'run-{run}.db'
            engine = create_async_engine(f'sqlite+aiosqlite:///{db.as_posix()}')

            @event.listens_for(engine.sync_engine, 'connect')
            def foreign_keys(connection, _):
                connection.execute('PRAGMA foreign_keys=ON')

            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            sessions = async_sessionmaker(engine, expire_on_commit=False)
            cache = FakeRedis(decode_responses=True)
            provider = CountedMock()
            settings = Settings(_env_file=None, app_env='test', llm_provider='mock', api_key='')
            app = create_app(settings, sessions=sessions, cache=cache, provider=provider)
            async with app.router.lifespan_context(app):
                logging.getLogger().setLevel(logging.ERROR)
                async with AsyncClient(transport=ASGITransport(app=app), base_url='http://experiment') as client:
                    products = []
                    for payload in PRODUCTS:
                        response = await client.post('/api/v1/products', json=payload)
                        response.raise_for_status()
                        products.append(response.json())
                    warm = await client.post('/api/v1/copies/generate', json={'product_id': products[0]['id']})
                    warm.raise_for_status()
                    await cache.flushdb()  # Dedicated FakeRedis instance only.
                    baseline_provider = CountedMock()
                    async with sessions() as session:
                        warm_product = await session.get(Product, UUID(products[0]['id']))
                        await baseline_provider.generate(canonical_input(warm_product, 'persuasivo', settings))
                    measured_start = provider.calls
                    cases = [(i, tone) for i in range(len(products)) for tone in tones]
                    rng = random.Random(seed + run)
                    rng.shuffle(cases)
                    for case, (index, tone) in enumerate(cases):
                        async with sessions() as session:
                            product = await session.get(Product, UUID(products[index]['id']))
                            snapshot = canonical_input(product, tone, settings)
                        async def measure_baseline():
                            before = baseline_provider.calls
                            started = time.perf_counter_ns()
                            result = await baseline_provider.generate(snapshot)
                            elapsed = (time.perf_counter_ns()-started)/1_000_000
                            assert result.tokens == 0
                            baselines.append(dict(run=run, case=case, sku=products[index]['sku'],
                                tone=tone, condition='PROVIDER_ONLY', latency_ms=elapsed,
                                provider_calls=baseline_provider.calls-before, tokens=0,
                                position='before' if baseline_first else 'after'))
                        baseline_first = bool(rng.getrandbits(1))
                        if baseline_first:
                            await measure_baseline()
                        reference = None
                        for repeat in range(5):
                            calls_before = provider.calls
                            started = time.perf_counter_ns()
                            response = await client.post('/api/v1/copies/generate', json={
                                'product_id': products[index]['id'], 'tone_of_voice': tone})
                            elapsed = (time.perf_counter_ns() - started) / 1_000_000
                            response.raise_for_status()
                            GenerateResponse.model_validate(response.json())
                            body = response.json()
                            expected = 'MISS' if repeat == 0 else 'HIT'
                            assert body['cache_status'] == expected
                            if reference is None:
                                reference = body['copy']
                            assert body['copy'] == reference
                            assert body['copy']['tokens_used'] == 0
                            rows.append(dict(run=run, case=case, sku=products[index]['sku'],
                                             tone=tone, repeat=repeat, status=response.status_code,
                                             cache=expected, latency_ms=elapsed,
                                             header_latency_ms=float(response.headers['X-Process-Time'])*1000,
                                             provider_calls=provider.calls-calls_before,
                                             input_hash=body['copy']['input_hash'],
                                             copy_id=body['copy']['id'], tokens=0, valid=True))
                        if not baseline_first:
                            await measure_baseline()
                    assert provider.calls - measured_start == 40
                    for concurrency in (5, 10, 30):
                        await cache.flushdb()
                        before = provider.calls
                        started = time.perf_counter_ns()
                        results = await asyncio.gather(*(client.post('/api/v1/copies/generate', json={
                            'product_id': products[0]['id'], 'tone_of_voice': 'persuasivo'})
                            for _ in range(concurrency)))
                        ms = (time.perf_counter_ns()-started)/1_000_000
                        contents = [r.json() for r in results]
                        assert all(r.status_code == 200 for r in results)
                        assert provider.calls-before == 1
                        assert len({r['copy']['id'] for r in contents}) == 1
                        assert sum(r['cache_status']=='MISS' for r in contents) == 1
                        batches.append(dict(run=run, concurrency=concurrency, requests=len(results),
                                            provider_calls=provider.calls-before, makespan_ms=ms,
                                            misses=1, hits=concurrency-1, errors=0))
                    async with sessions() as session:
                        count_before = await session.scalar(select(func.count()).select_from(GeneratedCopy))
            await engine.dispose()
            # Reopen connection to same temporary file; not a container/reboot durability test.
            engine2 = create_async_engine(f'sqlite+aiosqlite:///{db.as_posix()}')
            async with async_sessionmaker(engine2)() as session:
                count_after = await session.scalar(select(func.count()).select_from(GeneratedCopy))
            assert count_before == count_after
            persistence.append(dict(run=run, count_before=count_before, count_after=count_after))
            await engine2.dispose()
    miss = [r for r in rows if r['cache']=='MISS']
    hit = [r for r in rows if r['cache']=='HIT']
    summary = dict(miss=stats(miss), hit=stats(hit), requests=len(rows), errors=0,
                   provider_calls=sum(r['provider_calls'] for r in rows), tokens_real=0,
                   latency_reduction_mean_percent=100*(1-statistics.mean(r['latency_ms'] for r in hit)/statistics.mean(r['latency_ms'] for r in miss)),
                   baseline=stats(baselines), baseline_provider_calls=len(baselines),
                   by_run=[dict(run=run, miss=stats([r for r in miss if r['run']==run]),
                                hit=stats([r for r in hit if r['run']==run]),
                                baseline=stats([r for r in baselines if r['run']==run])) for run in range(1,rounds+1)],
                   concurrency=batches, sqlite_reopen=persistence)
    l, m, h = summary['baseline']['mean_ms'], summary['miss']['mean_ms'], summary['hit']['mean_ms']
    overhead = m-l
    summary['break_even'] = dict(provider_mean_ms=l, overhead_ms=overhead, hit_mean_ms=h,
        threshold_ratio=overhead/(m-h), reference='direct provider, not an equivalent HTTP endpoint',
        hypothetical_1500_ms_ratio=overhead/(1500+overhead-h),
        model='T(p)=(1-p)*(L+O)+p*H; beneficial relative to L if p>O/(L+O-H)')
    with (output/'observations.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (output/'baseline.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=list(baselines[0])); writer.writeheader(); writer.writerows(baselines)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    (output/'products.json').write_text(json.dumps(PRODUCTS,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=dict(timestamp_utc=datetime.now(UTC).isoformat(), platform=platform.platform(), python=platform.python_version(),
                  transport='httpx ASGITransport in-process; no TCP or browser', database='SQLite temporary files',
                  cache='FakeRedis; no Redis server', provider='MockProvider; intentional asyncio.sleep(0.08); zero real LLM tokens',
                  rounds=rounds, products=10, tones=tones, warmups_excluded=rounds*2, seed_base=seed,
                  baseline='direct MockProvider.generate(snapshot); snapshot preparation outside timer; before/after cached group randomized',
                  sequential_repeat_order='MISS followed by four HIT; product/tone case order shuffled per run',
                  versions={p:importlib.metadata.version(p) for p in ['fastapi','pydantic','sqlalchemy','httpx','fakeredis','redis','aiosqlite','google-genai']},
                  git_head=git_head, git_dirty=bool(git_status),
                  git_tags=subprocess.check_output(['git','tag','--points-at','HEAD'],text=True).splitlines(),
                  source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('src').rglob('*.py'))},
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output),'summary':summary},indent=2))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=20261106)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--allow-dirty', action='store_true', help='Diagnóstico; não usar na coleta do artigo')
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error('--rounds deve ser positivo')
    asyncio.run(main(args.seed, args.rounds, args.allow_dirty))

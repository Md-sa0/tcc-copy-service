import asyncio
import logging
import time
from uuid import uuid4

from fastapi import HTTPException, Request
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError

from src.models import GeneratedCopy, Product
from src.schemas.copies import CopyRead, GenerateResponse
from src.services.hashing import canonical_input, input_hash
from src.services.llm import GenerationError

logger = logging.getLogger(__name__)
RELEASE_LOCK = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def read_cached(cache, key: str) -> CopyRead | None:
    value = await cache.get(key)
    if value is None:
        return None
    try:
        return CopyRead.model_validate_json(value)
    except ValidationError:
        await cache.delete(key)
        return None


def hit(request: Request, copy: CopyRead) -> GenerateResponse:
    request.state.cache_status = "HIT"
    request.state.tokens_saved = copy.tokens_used
    return GenerateResponse(copy=copy, cache_status="HIT")


async def generate_copy(request: Request, session, payload) -> GenerateResponse:
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(404, "Produto não encontrado")
    settings = request.app.state.settings
    snapshot = canonical_input(product, payload.tone_of_voice, settings)
    digest = input_hash(snapshot)
    request.state.input_hash = digest
    request.state.model_name = settings.model_name
    cache = request.app.state.cache
    key = f"copy:sha256:{digest}"
    lock_key = f"lock:{key}"
    owner = str(uuid4())
    acquired = False
    # Release the read transaction before potentially waiting on the remote provider.
    await session.rollback()
    try:
        cached = await read_cached(cache, key)
        if cached:
            return hit(request, cached)
        deadline = time.monotonic() + settings.generation_timeout_seconds + 5
        while not acquired:
            acquired = await cache.set(lock_key, owner, nx=True, ex=settings.generation_timeout_seconds + 15)
            if acquired:
                break
            if time.monotonic() >= deadline:
                raise HTTPException(
                    503, "Geração em andamento; tente novamente", headers={"Retry-After": "5"}
                )
            await asyncio.sleep(0.1)
            cached = await read_cached(cache, key)
            if cached:
                return hit(request, cached)

        # Another worker can have completed between our first GET and lock acquisition.
        cached = await read_cached(cache, key)
        if cached:
            return hit(request, cached)
        request.state.cache_status = "MISS"
        started = time.perf_counter()
        # Bounds the whole critical section; the Redis lease exceeds this timeout.
        async with asyncio.timeout(settings.generation_timeout_seconds):
            result = await request.app.state.provider.generate(snapshot)
            request.state.tokens_used = result.tokens
            row = GeneratedCopy(
                product_id=payload.product_id,
                input_hash=digest,
                tone_of_voice=payload.tone_of_voice,
                input_snapshot=snapshot,
                instagram_copy=result.content.instagram.model_dump(),
                whatsapp_copy=result.content.whatsapp.model_dump(),
                seo_copy=result.content.ecommerce_seo.model_dump(),
                model_name=settings.model_name,
                inference_time_ms=(time.perf_counter() - started) * 1000,
                tokens_used=result.tokens,
            )
            session.add(row)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                raise HTTPException(409, "O produto foi removido durante a geração") from exc
            await session.refresh(row)
            output = CopyRead.model_validate(row)
            try:
                await cache.setex(key, settings.cache_ttl_seconds, output.model_dump_json())
            except RedisError:
                # SQL is the durable source of truth; a failed cache write must not hide saved content.
                logger.warning("cache_write_failed", extra={"input_hash": digest})
            return GenerateResponse(copy=output, cache_status="MISS")
    except RedisError as exc:
        raise HTTPException(
            503, "Cache indisponível; geração suspensa para evitar chamadas duplicadas"
        ) from exc
    except TimeoutError as exc:
        raise HTTPException(504, "Tempo limite da geração excedido") from exc
    except GenerationError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    finally:
        if acquired:
            try:
                await cache.eval(RELEASE_LOCK, 1, lock_key, owner)
            except RedisError:
                logger.warning("cache_lock_release_failed")

import asyncio
import logging
import time
from uuid import uuid4

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.models import GeneratedCopy, Product, ProviderCredential
from src.schemas.copies import CopyRead, GenerateResponse
from src.services.hashing import canonical_input, input_hash
from src.services.llm import GenerationError, OpenAICompatibleProvider

logger = logging.getLogger(__name__)
RELEASE_LOCK = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


async def read_cached(cache, key: str, snapshot: dict) -> CopyRead | None:
    value = await cache.get(key)
    if value is None:
        return None
    try:
        cached = CopyRead.model_validate_json(value)
        if (
            cached.input_snapshot == snapshot
            and cached.input_hash == input_hash(snapshot)
            and str(cached.product_id) == snapshot["product_id"]
            and cached.tone_of_voice == snapshot["tone_of_voice"]
            and cached.model_name == snapshot["model"]
        ):
            return cached
        await cache.delete(key)
        return None
    except ValidationError:
        await cache.delete(key)
        return None


def hit(request: Request, copy: CopyRead) -> GenerateResponse:
    request.state.cache_status = "HIT"
    request.state.tokens_saved = copy.tokens_used
    return GenerateResponse(copy=copy, cache_status="HIT")


async def generate_copy(request: Request, session, payload) -> GenerateResponse:
    try:
        async with asyncio.timeout(request.app.state.settings.generation_timeout_seconds):
            return await _generate_copy(request, session, payload)
    except TimeoutError as exc:
        raise HTTPException(504, "Tempo limite da geração excedido") from exc


async def _generate_copy(request: Request, session, payload) -> GenerateResponse:
    owner_id = request.state.user.id
    product = await session.scalar(
        select(Product).where(Product.id == payload.product_id, Product.owner_id == owner_id)
    )
    if product is None:
        raise HTTPException(404, "Produto não encontrado")
    credential = await session.scalar(
        select(ProviderCredential).where(ProviderCredential.owner_id == owner_id)
    )
    settings = request.app.state.settings
    model_name = credential.model if credential else request.app.state.runtime_model_name
    # Rollback expires ORM attributes even with expire_on_commit=False.
    # Copy every field used after the transaction before releasing it.
    credential_data = (
        (credential.encrypted_api_key, credential.base_url, credential.model)
        if credential is not None else None
    )
    snapshot = canonical_input(
        product,
        payload.tone_of_voice,
        settings,
        model_name,
        provider="openai-compatible" if credential_data else "mock",
        endpoint=credential_data[1] if credential_data else "",
    )
    digest = input_hash(snapshot)
    request.state.input_hash = digest
    request.state.model_name = model_name
    cache = request.app.state.cache
    key = f"copy:sha256:{digest}"
    lock_key = f"lock:{key}"
    owner = str(uuid4())
    acquired = False
    provider = None
    # Release the read transaction before potentially waiting on the remote provider.
    await session.rollback()
    try:
        if not payload.force_regenerate:
            cached = await read_cached(cache, key, snapshot)
            if cached:
                return hit(request, cached)
        while not acquired:
            acquired = await cache.set(lock_key, owner, nx=True, ex=settings.generation_timeout_seconds + 15)
            if acquired:
                break
            await asyncio.sleep(0.1)
            if not payload.force_regenerate:
                cached = await read_cached(cache, key, snapshot)
                if cached:
                    return hit(request, cached)

        # Another worker can have completed between our first GET and lock acquisition.
        if not payload.force_regenerate:
            cached = await read_cached(cache, key, snapshot)
            if cached:
                return hit(request, cached)
        request.state.cache_status = "MISS"
        started = time.perf_counter()
        if credential_data is not None:
            encryption_key = settings.settings_encryption_key.get_secret_value()
            if not encryption_key:
                raise HTTPException(
                    503,
                    "A chave criptografada do provedor não pode ser carregada. "
                    "Configure SETTINGS_ENCRYPTION_KEY.",
                )
            try:
                api_key = Fernet(encryption_key.encode("ascii")).decrypt(
                    credential_data[0].encode("ascii")
                ).decode("utf-8")
            except (ValueError, UnicodeEncodeError, InvalidToken) as exc:
                logger.error("provider_configuration_decryption_failed")
                raise HTTPException(
                    503, "A chave criptografada do provedor não pôde ser recuperada."
                ) from exc
            provider = OpenAICompatibleProvider(
                api_key=api_key,
                base_url=credential_data[1],
                model=credential_data[2],
            )
            result = await provider.generate(snapshot)
        else:
            result = await request.app.state.provider_manager.generate(snapshot)
        request.state.tokens_used = result.tokens
        row = GeneratedCopy(
            product_id=payload.product_id,
            input_hash=digest,
            tone_of_voice=payload.tone_of_voice,
            input_snapshot=snapshot,
            instagram_copy=result.content.instagram.model_dump(),
            whatsapp_copy=result.content.whatsapp.model_dump(),
            seo_copy=result.content.ecommerce_seo.model_dump(),
            model_name=model_name,
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
        request.state.tokens_used = exc.tokens_used
        raise HTTPException(exc.status_code, exc.message) from exc
    finally:
        try:
            if provider is not None:
                await provider.close()
        finally:
            if acquired:
                try:
                    await cache.eval(RELEASE_LOCK, 1, lock_key, owner)
                except RedisError:
                    logger.warning("cache_lock_release_failed")

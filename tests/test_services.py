import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from google.genai import errors
from pydantic import ValidationError

from seed_and_benchmark import percentile, summarize
from src.core.config import Settings
from src.models import Product
from src.schemas.copies import MarketingOutput
from src.schemas.products import ProductCreate
from src.services.hashing import canonical_input, input_hash
from src.services.llm import GeminiProvider, GenerationError, MockProvider


def test_hash_canonicalization_and_versions(product_payload):
    settings = Settings(_env_file=None, llm_provider="mock")
    product = Product(id=uuid4(), **ProductCreate.model_validate(product_payload).model_dump())
    initial = input_hash(canonical_input(product, "persuasivo", settings))
    product.technical_attributes = dict(reversed(list(product.technical_attributes.items())))
    product.key_benefits.reverse()
    assert input_hash(canonical_input(product, "persuasivo", settings)) == initial
    assert input_hash(canonical_input(product, "promocional", settings)) != initial
    settings.prompt_version = "v2"
    assert input_hash(canonical_input(product, "persuasivo", settings)) != initial
    assert len(initial) == 64


@pytest.mark.parametrize("code,attempts", [(429, 3), (503, 3), (400, 1), (401, 1)])
async def test_provider_retries_only_transient_errors(code, attempts):
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.settings = Settings(_env_file=None, llm_provider="mock", retry_base_seconds=0)
    call = AsyncMock(side_effect=errors.APIError(code, {"error": {"message": "test"}}))
    provider.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=call)))
    with pytest.raises(GenerationError):
        await provider.generate({})
    assert call.await_count == attempts


async def test_provider_recovers_and_validates_output(product_payload):
    result = await MockProvider().generate({"product": product_payload, "tone_of_voice": "persuasivo"})
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.settings = Settings(_env_file=None, llm_provider="mock", retry_base_seconds=0)
    response = SimpleNamespace(
        text=result.content.model_dump_json(), usage_metadata=SimpleNamespace(total_token_count=150)
    )
    call = AsyncMock(side_effect=[errors.APIError(429, {"error": {"message": "retry"}}), response])
    provider.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=call)))
    generated = await provider.generate({})
    assert generated.tokens == 150
    config = call.call_args.kwargs["config"]
    assert config.response_json_schema == MarketingOutput.model_json_schema()
    invalid = json.loads(response.text)
    invalid["ecommerce_seo"]["meta_title"] = "x" * 61
    call.side_effect = None
    call.return_value = SimpleNamespace(text=json.dumps(invalid), usage_metadata=None)
    with pytest.raises(GenerationError, match="contrato"):
        await provider.generate({})


def test_production_requires_credentials():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", llm_provider="mock", api_key="")


def test_benchmark_math():
    rows = [
        dict(
            status_code=200,
            cache_status="MISS",
            client_latency_ms=100,
            tokens_used=100,
            estimated_tokens_saved=0,
        ),
        dict(
            status_code=200,
            cache_status="HIT",
            client_latency_ms=10,
            tokens_used=0,
            estimated_tokens_saved=100,
        ),
        dict(
            status_code=503,
            cache_status="MISS",
            client_latency_ms=500,
            tokens_used=0,
            estimated_tokens_saved=0,
        ),
    ]
    summary = summarize(rows)
    assert summary["latency_savings_percent"] == 90
    assert summary["estimated_token_savings_percent"] == 50
    assert summary["errors"] == 1
    assert percentile([1, 2, 3, 4, 5], 0.95) == 4.8


@pytest.mark.parametrize("content", ['{"invalid":true}', None])
async def test_provider_preserves_usage_for_rejected_content(content):
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.settings = Settings(_env_file=None, llm_provider="mock")
    call = AsyncMock(
        return_value=SimpleNamespace(text=content, usage_metadata=SimpleNamespace(total_token_count=150))
    )
    provider.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=call)))
    with pytest.raises(GenerationError) as error:
        await provider.generate({})
    assert error.value.tokens_used == 150
    assert call.await_count == 1


@pytest.mark.parametrize(
    "value,expected", [(None, None), ("bad", None), ("NaN", None), ("-1", None), ("0.125", 125.0)]
)
def test_benchmark_missing_or_invalid_latency_is_not_zero(value, expected):
    from seed_and_benchmark import parse_api_latency

    assert parse_api_latency(value) == expected


def test_benchmark_invalid_success_and_zero_baseline():
    rows = [
        dict(
            status_code=200,
            cache_status=status,
            client_latency_ms=0,
            tokens_used=0,
            estimated_tokens_saved=0,
            error="",
        )
        for status in ("HIT", "MISS")
    ]
    rows.append({**rows[0], "error": "InvalidResponse:ValueError"})
    result = summarize(rows)
    assert result["errors"] == 1
    assert result["successful"] == 2
    assert result["latency_savings_percent"] is None

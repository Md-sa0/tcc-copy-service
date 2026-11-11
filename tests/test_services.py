from uuid import uuid4

import pytest
from pydantic import ValidationError

from seed_and_benchmark import percentile, summarize
from src.core.config import Settings
from src.models import Product
from src.schemas.products import ProductCreate
from src.services.hashing import canonical_input, input_hash


def test_hash_canonicalization_and_versions(product_payload):
    settings = Settings(_env_file=None)
    product = Product(id=uuid4(), **ProductCreate.model_validate(product_payload).model_dump())
    initial = input_hash(canonical_input(product, "persuasivo", settings))
    product.technical_attributes = dict(reversed(list(product.technical_attributes.items())))
    product.key_benefits.reverse()
    assert input_hash(canonical_input(product, "persuasivo", settings)) == initial
    assert input_hash(canonical_input(product, "promocional", settings)) != initial
    settings.prompt_version = "v2"
    assert input_hash(canonical_input(product, "persuasivo", settings)) != initial
    assert len(initial) == 64


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", cors_origins=["*"])


def test_provider_credentials_are_not_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "environment-provider-secret")
    monkeypatch.setenv("GEMINI_MODEL", "environment-model")
    settings = Settings(_env_file=None)

    assert settings.model_name == "mock-deterministic-v1"
    assert not hasattr(settings, "gemini_api_key")
    assert not hasattr(settings, "llm_provider")


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

import json
import socket

import httpx
import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from src.schemas.copies import GenerateResponse
from src.services.llm import MockProvider, OpenAICompatibleProvider


@pytest.fixture
def external_transport(stack, monkeypatch):
    _, app, _, _ = stack
    app.state.settings.settings_encryption_key = SecretStr(Fernet.generate_key().decode())
    real_getaddrinfo = socket.getaddrinfo
    monkeypatch.setattr("src.routers.settings.socket.getaddrinfo", lambda *a, **kw: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
    ] if a[0] in {"first.example", "second.example"} else real_getaddrinfo(*a, **kw))
    calls = []

    async def handler(request):
        calls.append(str(request.url))
        snapshot = json.loads(json.loads(request.content)["messages"][1]["content"])
        content = (await MockProvider().generate(snapshot)).content.model_dump()
        if getattr(app.state, "invalid_test_provider_response", False):
            content = {"unexpected": "invalid structured output"}
        return httpx.Response(200, json={
            "choices": [{"message": {"content": json.dumps(content)}}],
            "usage": {"total_tokens": 0},
        })

    class TransportProvider(OpenAICompatibleProvider):
        def __init__(self, *, api_key, base_url, model):
            self.model = model
            self.client = httpx.AsyncClient(
                base_url=base_url.rstrip("/") + "/", transport=httpx.MockTransport(handler),
            )

    monkeypatch.setattr("src.services.generation.OpenAICompatibleProvider", TransportProvider)
    return calls


async def configure(client, endpoint):
    response = await client.put("/api/v1/settings/provider", json={
        "api_key": "fictional-regression-key", "base_url": endpoint, "model": "same-model",
    }, headers={"Origin": "http://127.0.0.1:8080"})
    assert response.status_code == 200, response.text


async def test_authenticated_persisted_credential_miss_then_hit(stack, product_payload, external_transport):
    client, _, _, _ = stack
    await configure(client, "https://first.example/v1")
    product = (await client.post("/api/v1/products", json=product_payload)).json()
    payload = {"product_id": product["id"], "tone_of_voice": "persuasivo"}
    first = await client.post("/api/v1/copies/generate", json=payload)
    second = await client.post("/api/v1/copies/generate", json=payload)
    assert first.status_code == second.status_code == 200, first.text
    assert first.headers["X-Cache-Status"] == "MISS"
    assert second.headers["X-Cache-Status"] == "HIT"
    a = GenerateResponse.model_validate(first.json())
    b = GenerateResponse.model_validate(second.json())
    assert a.generated_copy == b.generated_copy
    assert len(external_transport) == 1
    assert "fictional-regression-key" not in first.text


async def test_endpoint_change_same_model_invalidates_cache(stack, product_payload, external_transport):
    client, _, _, _ = stack
    product = (await client.post("/api/v1/products", json=product_payload)).json()
    payload = {"product_id": product["id"], "tone_of_voice": "persuasivo"}
    await configure(client, "https://first.example/v1")
    first = await client.post("/api/v1/copies/generate", json=payload)
    await configure(client, "https://second.example/v1")
    second = await client.post("/api/v1/copies/generate", json=payload)
    assert first.status_code == second.status_code == 200
    a, b = GenerateResponse.model_validate(first.json()), GenerateResponse.model_validate(second.json())
    assert a.cache_status == b.cache_status == "MISS"
    assert a.generated_copy.id != b.generated_copy.id
    assert a.generated_copy.input_hash != b.generated_copy.input_hash
    assert a.generated_copy.model_name == b.generated_copy.model_name
    assert external_transport == ["https://first.example/v1/chat/completions", "https://second.example/v1/chat/completions"]


async def test_authenticated_invalid_provider_schema_is_controlled(stack, product_payload, external_transport):
    client, app, _, _ = stack
    await configure(client, "https://first.example/v1")
    product = (await client.post("/api/v1/products", json=product_payload)).json()
    payload = {"product_id": product["id"], "tone_of_voice": "persuasivo"}
    app.state.invalid_test_provider_response = True
    rejected = await client.post("/api/v1/copies/generate", json=payload)
    assert rejected.status_code == 502
    assert (await client.get("/api/v1/copies")).json()["total"] == 0
    app.state.invalid_test_provider_response = False
    recovered = await client.post("/api/v1/copies/generate", json=payload)
    assert recovered.status_code == 200
    assert recovered.headers["X-Cache-Status"] == "MISS"
    GenerateResponse.model_validate(recovered.json())
    assert len(external_transport) == 2


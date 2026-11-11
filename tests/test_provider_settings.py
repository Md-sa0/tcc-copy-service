import json
import socket
from uuid import UUID

import httpx
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import select

from src.models import ProviderCredential
from src.services.llm import TONE_INSTRUCTIONS, OpenAICompatibleProvider


async def test_provider_key_is_encrypted_and_never_returned(stack, monkeypatch):
    client, app, _, _ = stack
    app.state.settings.settings_encryption_key = SecretStr(
        Fernet.generate_key().decode("ascii")
    )
    monkeypatch.setattr(
        "src.routers.settings.socket.getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))
        ],
    )
    secret = "user-created-test-key-not-for-production"
    payload = {
        "api_key": secret,
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    }

    denied = await client.put(
        "/api/v1/settings/provider",
        json=payload,
        headers={"Origin": "https://attacker.example"},
    )
    assert denied.status_code == 403
    unsafe_url = await client.put(
        "/api/v1/settings/provider",
        json={**payload, "base_url": "https://localhost/v1"},
        headers={"Origin": "http://127.0.0.1:8080"},
    )
    assert unsafe_url.status_code == 422
    assert secret not in unsafe_url.text

    saved = await client.put(
        "/api/v1/settings/provider",
        json=payload,
        headers={"Origin": "http://127.0.0.1:8080"},
    )
    assert saved.status_code == 200, saved.text
    assert secret not in saved.text
    assert saved.json()["configured"] is True
    assert saved.json()["model"] == payload["model"]
    user = (await client.get("/api/v1/auth/me")).json()

    async with app.state.sessions() as session:
        credential = await session.scalar(
            select(ProviderCredential).where(ProviderCredential.owner_id == UUID(user["id"]))
        )
        assert credential is not None
        assert secret not in credential.encrypted_api_key
        first_ciphertext = credential.encrypted_api_key

    replacement = "new-user-authored-test-key-not-for-production"
    rotated = await client.put(
        "/api/v1/settings/provider",
        json={**payload, "api_key": replacement},
        headers={"Origin": "http://127.0.0.1:8080"},
    )
    assert rotated.status_code == 200
    assert replacement not in rotated.text
    async with app.state.sessions() as session:
        credential = await session.scalar(
            select(ProviderCredential).where(ProviderCredential.owner_id == UUID(user["id"]))
        )
        assert credential is not None
        assert credential.encrypted_api_key != first_ciphertext
        assert replacement not in credential.encrypted_api_key

    status = await client.get("/api/v1/settings/provider")
    assert status.status_code == 200
    assert secret not in status.text
    assert replacement not in status.text
    assert status.json()["provider"] == "openai-compatible"
    summary = await client.get("/api/v1/metrics/summary")
    assert summary.json()["provider"] == "openai-compatible"
    assert summary.json()["model_name"] == payload["model"]

    deleted = await client.delete(
        "/api/v1/settings/provider",
        headers={"Origin": "http://127.0.0.1:8080"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["configured"] is False
    assert deleted.json()["provider"] == "mock"
    async with app.state.sessions() as session:
        credential = await session.scalar(
            select(ProviderCredential).where(ProviderCredential.owner_id == UUID(user["id"]))
        )
        assert credential is None


async def test_locked_provider_key_can_be_deleted(stack):
    client, app, _, _ = stack
    user = (await client.get("/api/v1/auth/me")).json()
    async with app.state.sessions() as session:
        session.add(
            ProviderCredential(
                owner_id=UUID(user["id"]),
                encrypted_api_key="not-decryptable",
                base_url="https://api.openai.com/v1",
                model="gpt-4o-mini",
            )
        )
        await session.commit()

    status = await client.get("/api/v1/settings/provider")
    assert status.json()["locked"] is True

    denied = await client.delete(
        "/api/v1/settings/provider",
        headers={"Origin": "https://attacker.example"},
    )
    assert denied.status_code == 403

    deleted = await client.delete(
        "/api/v1/settings/provider",
        headers={"Origin": "http://127.0.0.1:8080"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["configured"] is False
    status = await client.get("/api/v1/settings/provider")
    assert status.json()["locked"] is False
    assert status.json()["provider"] == "mock"


async def test_openai_compatible_provider_parses_structured_response():
    content = {
        "instagram": {
            "hook": "Conheça o produto",
            "caption": "Legenda",
            "hashtags": ["#Produto"],
            "call_to_action": "Saiba mais",
        },
        "whatsapp": {"message": "Mensagem", "call_to_action": "Fale conosco"},
        "ecommerce_seo": {
            "meta_title": "Produto",
            "meta_description": "Descrição do produto",
            "bullet_points": ["Benefício"],
            "long_description": "Descrição completa",
        },
    }
    request_headers = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        request_headers.update(request.headers)
        body = json.loads(request.content)
        assert body["model"] == "gpt-4o-mini"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(content)}}],
                "usage": {"total_tokens": 23},
            },
        )

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        base_url="https://api.openai.com/v1/",
        headers={"Authorization": "Bearer test-key"},
        transport=httpx.MockTransport(handler),
    )
    try:
        result = await provider.generate(
            {
                "product": {"name": "Produto"},
                "tone_of_voice": "persuasivo",
                "temperature": 0.7,
            }
        )
    finally:
        await provider.close()

    assert request_headers["authorization"] == "Bearer test-key"
    assert result.content.instagram.hook == "Conheça o produto"
    assert result.tokens == 23


async def test_openai_compatible_provider_sends_selected_tone_instruction():
    content = {
        "instagram": {
            "hook": "Conheça o produto",
            "caption": "Legenda",
            "hashtags": ["#Produto"],
            "call_to_action": "Saiba mais",
        },
        "whatsapp": {"message": "Mensagem", "call_to_action": "Fale conosco"},
        "ecommerce_seo": {
            "meta_title": "Produto",
            "meta_description": "Descrição do produto",
            "bullet_points": ["Benefício"],
            "long_description": "Descrição completa",
        },
    }
    instructions = []
    requested_tones = []
    temperatures = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        instructions.append(body["messages"][0]["content"])
        temperatures.append(body["temperature"])
        snapshot = json.loads(body["messages"][1]["content"])
        requested_tones.append(snapshot["tone_of_voice"])
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(content)}}]},
        )

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        model="test-model",
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        base_url="https://api.openai.com/v1/",
        transport=httpx.MockTransport(handler),
    )
    try:
        for tone in TONE_INSTRUCTIONS:
            await provider.generate(
                {
                    "tone_of_voice": tone,
                    "temperature": 0.7,
                    "product": {"name": "Produto", "key_benefits": ["Benefício"]},
                }
            )
    finally:
        await provider.close()

    assert requested_tones == list(TONE_INSTRUCTIONS)
    assert temperatures == [0.7] * len(TONE_INSTRUCTIONS)
    for tone, instruction in zip(requested_tones, instructions, strict=True):
        assert f"tom de voz solicitado é {tone}" in instruction
        assert TONE_INSTRUCTIONS[tone] in instruction
        assert "450 a 800 caracteres" in instruction
        assert "250 a 500 caracteres" in instruction
        assert "500 a 900 caracteres" in instruction
        assert "textos próprios" in instruction

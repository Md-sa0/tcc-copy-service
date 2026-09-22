"""HTTP contract checks against a running full-stack deployment."""

import asyncio
import os

import httpx


async def run():
    async with httpx.AsyncClient(
        base_url=os.getenv("API_URL", "http://localhost:8080"),
        headers={"X-API-Key": os.getenv("API_KEY", "")},
        timeout=15,
    ) as client:
        for route, payload in (
            ("products", {"sku": "INCOMPLETO"}),
            ("copies/generate", {}),
            ("copies/generate", {"product_id": "uuid-inválido"}),
        ):
            response = await client.post(f"/api/v1/{route}", json=payload)
            assert response.status_code == 422, f"{route}: esperado 422, recebido {response.status_code}"
            assert response.headers["X-Cache-Status"] == "BYPASS"
            print(f"PASS: {route} → 422, sem consulta ao LLM")


if __name__ == "__main__":
    asyncio.run(run())

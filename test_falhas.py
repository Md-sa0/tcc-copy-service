"""HTTP contract checks against a running full-stack deployment."""

import asyncio
import os

import httpx


async def run():
    email = os.getenv("COPYLAB_EMAIL")
    password = os.getenv("COPYLAB_PASSWORD")
    if not email or not password:
        raise SystemExit("Defina COPYLAB_EMAIL e COPYLAB_PASSWORD de uma conta existente.")
    async with httpx.AsyncClient(
        base_url=os.getenv("API_URL", "http://localhost:8080"),
        timeout=15,
    ) as client:
        login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        login.raise_for_status()
        client.headers["X-CSRF-Token"] = client.cookies["copylab_csrf"]
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

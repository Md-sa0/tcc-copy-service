import asyncio
import json
import time
import httpx

API_URL = "http://127.0.0.1:8000/v1/generate-copy"

PRODUTO_TESTE = {
    "product_id": "SKU-BELLA-001",
    "name": "Sérum Facial Hidratante com Ácido Hialurónico",
    "category": "Cuidados com a Pele",
    "target_audience": "Pessoas que procuram hidratação profunda",
    "technical_attributes": {"volume": "30ml", "concentracao": "2%"},
    "key_benefits": ["Hidratação 24h", "Rápida absorção"],
    "tone_of_voice": "persuasive"
}

async def run_benchmark():
    results = []
    print("\nIniciando validação empírica de Cache (Miss vs Hit)...")

    async with httpx.AsyncClient(timeout=90.0) as client:
        # Rodada 1: Sem Cache (Chama a API do Gemini)
        print("\n[Chamada 1] Enviando produto (Cache Miss - consulta LLM)...")
        t0 = time.perf_counter()
        resp1 = await client.post(API_URL, json=PRODUTO_TESTE)
        t1 = round((time.perf_counter() - t0) * 1000, 2)
        data1 = resp1.json()
        print(f"-> Concluído em: {t1} ms | Cache Hit: {data1['telemetry'].get('cache_hit')}")

        results.append({
            "cenario": "Sem Cache (Cache Miss)",
            "tempo_total_ms": t1,
            "tempo_interno_api_ms": data1["telemetry"]["latency_ms"],
            "cache_hit": data1["telemetry"].get("cache_hit")
        })

        # Rodada 2: Com Cache (Pega direto da memória)
        print("\n[Chamada 2] Reenviando o mesmo produto (Cache Hit - memória)...")
        t2_start = time.perf_counter()
        resp2 = await client.post(API_URL, json=PRODUTO_TESTE)
        t2 = round((time.perf_counter() - t2_start) * 1000, 2)
        data2 = resp2.json()
        print(f"-> Concluído em: {t2} ms | Cache Hit: {data2['telemetry'].get('cache_hit')}")

        results.append({
            "cenario": "Com Cache (Cache Hit)",
            "tempo_total_ms": t2,
            "tempo_interno_api_ms": data2["telemetry"]["latency_ms"],
            "cache_hit": data2["telemetry"].get("cache_hit")
        })

    with open("resultado_cache.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\nComparativo gerado e salvo em 'resultado_cache.json' com sucesso!")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
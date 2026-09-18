import asyncio
import json
import httpx

API_URL = "http://127.0.0.1:8000/v1/generate-copy"

# Payload incompleto propositado (sem 'name' e sem 'key_benefits')
PAYLOAD_INVALIDO = {
    "product_id": "SKU-BELLA-TESTE-ERRO",
    "category": "Cuidados com a Pele",
    "target_audience": "Utilizadores que procuram hidratação",
    "technical_attributes": {
        "volume": "30ml"
    },
    "tone_of_voice": "persuasive"
}

async def testar_validacao_schema():
    print("\n--- Teste de Robustez do Esquema (HTTP 422) ---")
    print("A enviar payload com campos obrigatórios em falta...\n")

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(API_URL, json=PAYLOAD_INVALIDO)

        print(f"Código de Estado HTTP retornado: {response.status_code}")

        if response.status_code == 422:
            erro_detalhes = response.json()
            print("\n[SUCESSO] A API barrou o payload incorreto com o código HTTP 422.")
            print("Campos detetados como ausentes:")
            for erro in erro_detalhes.get("detail", []):
                campo = erro.get("loc", [])[-1]
                mensagem = erro.get("msg", "")
                print(f" - Campo: '{campo}' -> {mensagem}")

            with open("resultado_teste_falha.json", "w", encoding="utf-8") as f:
                json.dump(erro_detalhes, f, indent=2, ensure_ascii=False)
            print("\nRelatório de erro guardado em 'resultado_teste_falha.json'.")
        else:
            print(f"[FALHA] Esperava-se código 422, mas retornou {response.status_code}: {response.text}")

if __name__ == "__main__":
    asyncio.run(testar_validacao_schema())
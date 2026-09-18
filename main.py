import os
import time
import hashlib
import json
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI(
    title="Retail Marketing Copy Microservice",
    description="API com Structured Outputs e Cache em Memória",
    version="1.1.0"
)

# Cache em memória (dicionário SKU/Hash -> Dados)
CACHE_STORE: Dict[str, dict] = {}

class ProductInput(BaseModel):
    product_id: str = Field(..., description="Identificador do produto (SKU)")
    name: str = Field(..., description="Nome comercial")
    category: str = Field(..., description="Categoria")
    target_audience: str = Field(..., description="Público-alvo")
    technical_attributes: Dict[str, str] = Field(..., description="Atributos técnicos")
    key_benefits: List[str] = Field(..., description="Benefícios comprovados")
    tone_of_voice: Optional[str] = Field("persuasive", description="Tom pretendido")

class InstagramCopy(BaseModel):
    hook: str
    caption: str
    hashtags: List[str]
    call_to_action: str

class WhatsAppCopy(BaseModel):
    message: str
    call_to_action: str

class EcommerceCopy(BaseModel):
    meta_title: str
    meta_description: str
    bullet_points: List[str]
    long_description: str

class MarketingChannelsOutput(BaseModel):
    instagram: InstagramCopy
    whatsapp: WhatsAppCopy
    ecommerce_seo: EcommerceCopy

CANDIDATE_MODELS = [
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

def gerar_chave_cache(payload: ProductInput) -> str:
    raw_data = json.dumps(payload.model_dump(), sort_keys=True)
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

@app.post("/v1/generate-copy")
async def generate_product_copy(payload: ProductInput):
    start_time = time.perf_counter()
    cache_key = gerar_chave_cache(payload)

    # 1. Verificação de Cache Hit
    if cache_key in CACHE_STORE:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        cached_entry = CACHE_STORE[cache_key]
        return {
            "status": "success",
            "product_id": payload.product_id,
            "data": cached_entry["data"],
            "telemetry": {
                "latency_ms": latency_ms,
                "model": cached_entry["model"],
                "cache_hit": True
            }
        }

    # 2. Se for Cache Miss, chama o LLM
    prompt = f"""
    És um redator publicitário sénior especialista em retalho e comércio.
    Gera variações publicitárias multicanal estritamente baseadas nos dados fornecidos:
    - ID: {payload.product_id}
    - Nome: {payload.name}
    - Categoria: {payload.category}
    - Público-Alvo: {payload.target_audience}
    - Tom de Voz: {payload.tone_of_voice}
    - Atributos Técnicos: {payload.technical_attributes}
    - Benefícios: {payload.key_benefits}

    Não inventes propriedades não descritas. Cumpre integralmente o esquema JSON de saída.
    """

    last_error = None

    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=MarketingChannelsOutput,
                        temperature=0.2,
                    ),
                )

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                # Salva no Cache
                CACHE_STORE[cache_key] = {
                    "data": response.parsed,
                    "model": model_name
                }

                return {
                    "status": "success",
                    "product_id": payload.product_id,
                    "data": response.parsed,
                    "telemetry": {
                        "latency_ms": latency_ms,
                        "model": model_name,
                        "cache_hit": False
                    }
                }
            except Exception as exc:
                last_error = exc
                time.sleep(1.0)

    raise HTTPException(status_code=500, detail=f"Falha em todos os modelos: {str(last_error)}")

@app.get("/health")
def health():
    return {"status": "online", "cache_entries": len(CACHE_STORE)}
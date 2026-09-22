import hashlib
import json

from src.core.config import Settings
from src.models import Product
from src.schemas.products import ProductCreate


def canonical_input(product: Product, tone: str, settings: Settings) -> dict:
    attributes = ProductCreate.model_validate(product).model_dump()
    attributes["key_benefits"] = sorted(attributes["key_benefits"])
    return {
        "product_id": str(product.id),
        "product": attributes,
        "tone_of_voice": tone,
        "model": settings.model_name,
        "prompt_version": settings.prompt_version,
        "output_schema_version": "v1",
        "temperature": 0.2,
    }


def input_hash(snapshot: dict) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

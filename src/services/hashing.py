import hashlib
import json
from urllib.parse import urlsplit, urlunsplit

from src.core.config import Settings
from src.models import Product
from src.schemas.products import ProductCreate


def canonical_input(
    product: Product, tone: str, settings: Settings, model_name: str | None = None,
    *, provider: str = "mock", endpoint: str = "",
) -> dict:
    attributes = ProductCreate.model_validate(product).model_dump()
    attributes["key_benefits"] = sorted(attributes["key_benefits"])
    return {
        "product_id": str(product.id),
        "product": attributes,
        "tone_of_voice": tone,
        "model": model_name or settings.model_name,
        "provider_config": {"provider": provider, "endpoint": normalize_endpoint(endpoint)},
        "prompt_version": settings.prompt_version,
        "output_schema_version": "v1",
        "temperature": 0.7,
    }


def normalize_endpoint(endpoint: str) -> str:
    if not endpoint:
        return ""
    parsed = urlsplit(endpoint.strip())
    # Credentials and query parameters must never enter a persisted snapshot.
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Provider endpoint must not contain credentials, query or fragment")
    host = (parsed.hostname or "").lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    if port and not (parsed.scheme.lower() == "https" and port == 443):
        host += f":{port}"
    return urlunsplit((parsed.scheme.lower(), host, parsed.path.rstrip("/"), "", ""))


def input_hash(snapshot: dict) -> str:
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

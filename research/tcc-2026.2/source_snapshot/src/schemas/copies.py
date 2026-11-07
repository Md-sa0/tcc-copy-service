from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from src.schemas.products import StrictSchema

Tone = Literal["persuasivo", "descontraído", "institucional", "promocional"]
ShortText = Annotated[
    str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=500)
]


class InstagramCopy(StrictSchema):
    hook: ShortText
    caption: str = Field(min_length=1, max_length=2200, strict=True)
    hashtags: list[Annotated[str, StringConstraints(pattern=r"^#[\w]+$", max_length=80)]] = Field(
        min_length=1, max_length=15
    )
    call_to_action: ShortText


class WhatsAppCopy(StrictSchema):
    message: str = Field(min_length=1, max_length=4096, strict=True)
    call_to_action: ShortText


class SEOCopy(StrictSchema):
    meta_title: str = Field(min_length=1, max_length=60, strict=True)
    meta_description: str = Field(min_length=1, max_length=160, strict=True)
    bullet_points: list[ShortText] = Field(min_length=1, max_length=10)
    long_description: str = Field(min_length=1, max_length=5000, strict=True)


class MarketingOutput(StrictSchema):
    instagram: InstagramCopy
    whatsapp: WhatsAppCopy
    ecommerce_seo: SEOCopy


class GenerateRequest(StrictSchema):
    product_id: UUID
    tone_of_voice: Tone = "persuasivo"


class CopyRead(StrictSchema):
    id: UUID
    product_id: UUID
    input_hash: str
    tone_of_voice: Tone
    input_snapshot: dict
    instagram_copy: InstagramCopy
    whatsapp_copy: WhatsAppCopy
    seo_copy: SEOCopy
    model_name: str
    inference_time_ms: float
    tokens_used: int
    created_at: datetime


class GenerateResponse(StrictSchema):
    generated_copy: CopyRead = Field(alias="copy")
    cache_status: Literal["HIT", "MISS"]


class CopyPage(StrictSchema):
    items: list[CopyRead]
    total: int
    offset: int
    limit: int

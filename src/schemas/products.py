import unicodedata
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


def clean(value: str) -> str:
    return unicodedata.normalize("NFC", value).strip()


Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=500)]


class ProductCreate(StrictSchema):
    sku: Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
    name: Annotated[str, StringConstraints(strict=True, min_length=2, max_length=200)]
    category: Annotated[str, StringConstraints(strict=True, min_length=2, max_length=100)]
    target_audience: Annotated[str, StringConstraints(strict=True, min_length=3, max_length=500)]
    technical_attributes: dict[Text, Text] = Field(min_length=1, max_length=30, strict=True)
    key_benefits: list[Text] = Field(min_length=1, max_length=20, strict=True)

    @field_validator("sku", "name", "category", "target_audience", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return clean(value) if isinstance(value, str) else value

    @field_validator("technical_attributes", mode="before")
    @classmethod
    def normalize_attributes(cls, values):
        if not isinstance(values, dict):
            return values
        normalized = {
            clean(k) if isinstance(k, str) else k: clean(v) if isinstance(v, str) else v
            for k, v in values.items()
        }
        if len(normalized) != len(values):
            raise ValueError("Atributos duplicados após normalização")
        return normalized

    @field_validator("key_benefits")
    @classmethod
    def normalize_benefits(cls, values):
        normalized = [clean(v) for v in values]
        if len(set(normalized)) != len(normalized):
            raise ValueError("Benefícios devem ser únicos")
        return normalized


class ProductRead(ProductCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductPage(StrictSchema):
    items: list[ProductRead]
    total: int
    offset: int
    limit: int

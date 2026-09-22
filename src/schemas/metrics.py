from datetime import datetime
from uuid import UUID

from src.schemas.products import StrictSchema


class MetricRead(StrictSchema):
    id: UUID
    request_id: str
    path: str
    method: str
    kind: str
    latency_ms: float
    cache_status: str
    status_code: int
    input_hash: str | None
    model_name: str | None
    tokens_used: int
    tokens_saved: int
    created_at: datetime


class MetricPage(StrictSchema):
    items: list[MetricRead]
    total: int
    offset: int
    limit: int


class MetricSummary(StrictSchema):
    hours: int
    model_name: str
    provider: str
    generation_requests: int
    successful_generations: int
    errors: int
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float | None
    average_latency_ms: float | None
    hit_latency_ms: float | None
    miss_latency_ms: float | None
    latency_savings_percent: float | None
    tokens_used: int
    estimated_tokens_saved: int
    estimated_token_savings_percent: float | None

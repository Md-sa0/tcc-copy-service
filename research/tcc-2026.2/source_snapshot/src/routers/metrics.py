from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session
from src.models import ApiMetric
from src.schemas.metrics import MetricPage, MetricSummary

router = APIRouter(prefix="/metrics", tags=["Métricas"])


@router.get("/summary", response_model=MetricSummary)
async def summary(
    request: Request,
    hours: int = Query(default=24, ge=1, le=8760),
    session: AsyncSession = Depends(get_session),
):
    settings = request.app.state.settings
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    # Include schema/auth failures with no model in the error count; never mix successful models.
    filters = [
        ApiMetric.kind == "generation",
        ApiMetric.created_at >= cutoff,
        (ApiMetric.model_name == settings.model_name) | ApiMetric.model_name.is_(None),
    ]
    success = ApiMetric.status_code.between(200, 299)
    hit = success & (ApiMetric.cache_status == "HIT")
    miss = success & (ApiMetric.cache_status == "MISS")
    stmt = select(
        func.count().label("total"),
        func.sum(case((success, 1), else_=0)).label("successes"),
        func.sum(case((hit, 1), else_=0)).label("hits"),
        func.sum(case((miss, 1), else_=0)).label("misses"),
        func.avg(case((success, ApiMetric.latency_ms))).label("avg"),
        func.avg(case((hit, ApiMetric.latency_ms))).label("hit_avg"),
        func.avg(case((miss, ApiMetric.latency_ms))).label("miss_avg"),
        func.sum(ApiMetric.tokens_used).label("tokens"),
        func.sum(ApiMetric.tokens_saved).label("saved"),
    ).where(*filters)
    row = (await session.execute(stmt)).one()
    hits, misses = row.hits or 0, row.misses or 0
    tokens, saved = row.tokens or 0, row.saved or 0
    return {
        "hours": hours,
        "model_name": settings.model_name,
        "provider": settings.llm_provider,
        "generation_requests": row.total,
        "successful_generations": row.successes or 0,
        "errors": row.total - (row.successes or 0),
        "cache_hits": hits,
        "cache_misses": misses,
        "cache_hit_ratio": hits / (hits + misses) if hits + misses else None,
        "average_latency_ms": row.avg,
        "hit_latency_ms": row.hit_avg,
        "miss_latency_ms": row.miss_avg,
        "latency_savings_percent": 100 * (1 - row.hit_avg / row.miss_avg)
        if row.hit_avg is not None and row.miss_avg
        else None,
        "tokens_used": tokens,
        "estimated_tokens_saved": saved,
        "estimated_token_savings_percent": 100 * saved / (tokens + saved) if tokens + saved else None,
    }


@router.get("/requests", response_model=MetricPage)
async def history(
    hours: int = Query(default=24, ge=1, le=8760),
    kind: Literal["all", "generation", "api"] = "all",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    filters = [ApiMetric.created_at >= datetime.now(UTC) - timedelta(hours=hours)]
    if kind != "all":
        filters.append(ApiMetric.kind == kind)
    total = await session.scalar(select(func.count()).select_from(ApiMetric).where(*filters))
    rows = await session.scalars(
        select(ApiMetric)
        .where(*filters)
        .order_by(ApiMetric.created_at.desc(), ApiMetric.id)
        .offset(offset)
        .limit(limit)
    )
    return {"items": list(rows), "total": total, "offset": offset, "limit": limit}

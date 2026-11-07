from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session
from src.models import GeneratedCopy
from src.schemas.copies import CopyPage, CopyRead, GenerateRequest, GenerateResponse
from src.services.generation import generate_copy

router = APIRouter(prefix="/copies", tags=["Copies"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest, request: Request, session: AsyncSession = Depends(get_session)):
    return await generate_copy(request, session, payload)


@router.get("", response_model=CopyPage)
async def list_copies(
    product_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    filters = [GeneratedCopy.product_id == product_id] if product_id else []
    total = await session.scalar(select(func.count()).select_from(GeneratedCopy).where(*filters))
    rows = await session.scalars(
        select(GeneratedCopy)
        .where(*filters)
        .order_by(GeneratedCopy.created_at.desc(), GeneratedCopy.id)
        .offset(offset)
        .limit(limit)
    )
    return {"items": list(rows), "total": total, "offset": offset, "limit": limit}


@router.get("/{copy_id}", response_model=CopyRead)
async def get_copy(copy_id: UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(GeneratedCopy, copy_id)
    if row is None:
        raise HTTPException(404, "Copy não encontrada")
    return row

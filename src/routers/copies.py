from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session, require_authenticated_user
from src.models import GeneratedCopy, Product
from src.schemas.copies import (
    CopyPage,
    CopyRead,
    CopyRevisionRequest,
    GenerateRequest,
    GenerateResponse,
)
from src.services.generation import generate_copy

router = APIRouter(
    prefix="/copies", tags=["Copies"], dependencies=[Depends(require_authenticated_user)]
)


@router.post("/generate", response_model=GenerateResponse)
async def generate(payload: GenerateRequest, request: Request, session: AsyncSession = Depends(get_session)):
    return await generate_copy(request, session, payload)


@router.post("/{copy_id}/revisions", response_model=CopyRead, status_code=201)
async def create_revision(
    copy_id: UUID,
    payload: CopyRevisionRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    original = await session.scalar(
        select(GeneratedCopy)
        .join(Product, Product.id == GeneratedCopy.product_id)
        .where(GeneratedCopy.id == copy_id, Product.owner_id == request.state.user.id)
    )
    if original is None:
        raise HTTPException(404, "Copy não encontrada")
    revision = GeneratedCopy(
        product_id=original.product_id,
        input_hash=original.input_hash,
        tone_of_voice=original.tone_of_voice,
        input_snapshot=original.input_snapshot,
        instagram_copy=payload.instagram_copy.model_dump(),
        whatsapp_copy=payload.whatsapp_copy.model_dump(),
        seo_copy=payload.seo_copy.model_dump(),
        model_name=original.model_name,
        inference_time_ms=original.inference_time_ms,
        tokens_used=original.tokens_used,
    )
    session.add(revision)
    await session.commit()
    await session.refresh(revision)
    return revision


@router.get("", response_model=CopyPage)
async def list_copies(
    request: Request,
    product_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    filters = [Product.owner_id == request.state.user.id]
    if product_id:
        filters.append(GeneratedCopy.product_id == product_id)
    total = await session.scalar(
        select(func.count())
        .select_from(GeneratedCopy)
        .join(Product, Product.id == GeneratedCopy.product_id)
        .where(*filters)
    )
    rows = await session.scalars(
        select(GeneratedCopy)
        .join(Product, Product.id == GeneratedCopy.product_id)
        .where(*filters)
        .order_by(GeneratedCopy.created_at.desc(), GeneratedCopy.id)
        .offset(offset)
        .limit(limit)
    )
    return {"items": list(rows), "total": total, "offset": offset, "limit": limit}


@router.get("/{copy_id}", response_model=CopyRead)
async def get_copy(
    copy_id: UUID, request: Request, session: AsyncSession = Depends(get_session)
):
    row = await session.scalar(
        select(GeneratedCopy)
        .join(Product, Product.id == GeneratedCopy.product_id)
        .where(GeneratedCopy.id == copy_id, Product.owner_id == request.state.user.id)
    )
    if row is None:
        raise HTTPException(404, "Copy não encontrada")
    return row

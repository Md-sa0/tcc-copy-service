from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_session
from src.models import Product
from src.schemas.products import ProductCreate, ProductPage, ProductRead

router = APIRouter(prefix="/products", tags=["Catálogo"])


@router.get("", response_model=ProductPage)
async def list_products(
    q: str = Query(default="", max_length=200),
    sku: str | None = Query(default=None, max_length=64),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    filters = []
    if q:
        filters.append(
            or_(Product.name.icontains(q, autoescape=True), Product.sku.icontains(q, autoescape=True))
        )
    if sku:
        filters.append(Product.sku == sku)
    total = await session.scalar(select(func.count()).select_from(Product).where(*filters))
    rows = await session.scalars(
        select(Product)
        .where(*filters)
        .order_by(Product.created_at.desc(), Product.id)
        .offset(offset)
        .limit(limit)
    )
    return {"items": list(rows), "total": total, "offset": offset, "limit": limit}


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_session)):
    product = Product(**payload.model_dump())
    session.add(product)
    await save_product(session)
    await session.refresh(product)
    return product


async def find_product(product_id: UUID, session: AsyncSession) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Produto não encontrado")
    return product


async def save_product(session: AsyncSession):
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(409, "Já existe um produto com este SKU") from exc


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    return await find_product(product_id, session)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: UUID, payload: ProductCreate, session: AsyncSession = Depends(get_session)
):
    product = await find_product(product_id, session)
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    await save_product(session)
    await session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: UUID, session: AsyncSession = Depends(get_session)):
    product = await find_product(product_id, session)
    await session.delete(product)
    await session.commit()
    return Response(status_code=204)

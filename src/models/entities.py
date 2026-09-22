import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


json_type = JSON().with_variant(JSONB(), "postgresql")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100))
    target_audience: Mapped[str] = mapped_column(String(500))
    technical_attributes: Mapped[dict] = mapped_column(json_type)
    key_benefits: Mapped[list] = mapped_column(json_type)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GeneratedCopy(Base):
    __tablename__ = "generated_copies"
    __table_args__ = (Index("ix_copies_product_created", "product_id", "created_at"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    tone_of_voice: Mapped[str] = mapped_column(String(30))
    input_snapshot: Mapped[dict] = mapped_column(json_type)
    instagram_copy: Mapped[dict] = mapped_column(json_type)
    whatsapp_copy: Mapped[dict] = mapped_column(json_type)
    seo_copy: Mapped[dict] = mapped_column(json_type)
    model_name: Mapped[str] = mapped_column(String(100))
    inference_time_ms: Mapped[float] = mapped_column(Float)
    tokens_used: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ApiMetric(Base):
    __tablename__ = "api_metrics"
    __table_args__ = (Index("ix_metrics_created_kind", "created_at", "kind"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(36), index=True)
    path: Mapped[str] = mapped_column(String(300))
    method: Mapped[str] = mapped_column(String(10))
    kind: Mapped[str] = mapped_column(String(20), default="api")
    latency_ms: Mapped[float] = mapped_column(Float)
    cache_status: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int] = mapped_column(Integer)
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    tokens_saved: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

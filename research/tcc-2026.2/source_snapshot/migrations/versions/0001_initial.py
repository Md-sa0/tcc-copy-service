"""Persist catalog, generated content and quantitative request telemetry."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("target_audience", sa.String(500), nullable=False),
        sa.Column("technical_attributes", JSONB(), nullable=False),
        sa.Column("key_benefits", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_table(
        "generated_copies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("product_id", sa.Uuid(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("tone_of_voice", sa.String(30), nullable=False),
        sa.Column("input_snapshot", JSONB(), nullable=False),
        sa.Column("instagram_copy", JSONB(), nullable=False),
        sa.Column("whatsapp_copy", JSONB(), nullable=False),
        sa.Column("seo_copy", JSONB(), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("inference_time_ms", sa.Float(), nullable=False),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_generated_copies_product_id", "generated_copies", ["product_id"])
    op.create_index("ix_generated_copies_input_hash", "generated_copies", ["input_hash"])
    op.create_index("ix_copies_product_created", "generated_copies", ["product_id", "created_at"])
    op.create_table(
        "api_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("path", sa.String(300), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("cache_status", sa.String(10), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("input_hash", sa.String(64)),
        sa.Column("model_name", sa.String(100)),
        sa.Column("tokens_used", sa.Integer(), nullable=False),
        sa.Column("tokens_saved", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_api_metrics_request_id", "api_metrics", ["request_id"])
    op.create_index("ix_metrics_created_kind", "api_metrics", ["created_at", "kind"])


def downgrade():
    op.drop_table("api_metrics")
    op.drop_table("generated_copies")
    op.drop_table("products")

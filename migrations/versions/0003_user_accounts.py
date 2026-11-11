"""Add user accounts, authenticated sessions, and per-user data ownership."""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

LEGACY_USER_ID = uuid.uuid5(uuid.NAMESPACE_URL, "copylab-legacy-owner-v1")


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_token_hash", "auth_sessions", ["token_hash"], unique=True)
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])

    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO users (id, email, password_hash, is_active) "
            "VALUES (:id, :email, :password_hash, false)"
        ),
        {
            "id": LEGACY_USER_ID,
            "email": "legacy-data@copylab.invalid",
            "password_hash": "disabled",
        },
    )

    op.add_column("products", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.add_column("provider_credentials", sa.Column("owner_id", sa.Uuid(), nullable=True))
    op.add_column("api_metrics", sa.Column("user_id", sa.Uuid(), nullable=True))
    bind.execute(
        sa.text("UPDATE products SET owner_id = :owner_id"),
        {"owner_id": LEGACY_USER_ID},
    )
    bind.execute(
        sa.text("UPDATE provider_credentials SET owner_id = :owner_id"),
        {"owner_id": LEGACY_USER_ID},
    )
    op.alter_column("products", "owner_id", nullable=False)
    op.alter_column("provider_credentials", "owner_id", nullable=False)
    op.create_foreign_key(
        "fk_products_owner_id_users", "products", "users", ["owner_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "fk_provider_credentials_owner_id_users",
        "provider_credentials",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_api_metrics_user_id_users",
        "api_metrics",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_index("ix_products_sku", table_name="products")
    op.create_index("ix_products_sku", "products", ["sku"])
    op.create_index("ix_products_owner_id", "products", ["owner_id"])
    op.create_unique_constraint("uq_products_owner_sku", "products", ["owner_id", "sku"])
    op.create_index(
        "ix_provider_credentials_owner_id", "provider_credentials", ["owner_id"], unique=True
    )
    op.create_index("ix_api_metrics_user_id", "api_metrics", ["user_id"])


def downgrade():
    op.drop_index("ix_api_metrics_user_id", table_name="api_metrics")
    op.drop_constraint("fk_api_metrics_user_id_users", "api_metrics", type_="foreignkey")
    op.drop_column("api_metrics", "user_id")
    op.drop_index("ix_provider_credentials_owner_id", table_name="provider_credentials")
    op.drop_constraint("fk_provider_credentials_owner_id_users", "provider_credentials", type_="foreignkey")
    op.drop_column("provider_credentials", "owner_id")
    op.drop_constraint("uq_products_owner_sku", "products", type_="unique")
    op.drop_index("ix_products_owner_id", table_name="products")
    op.drop_constraint("fk_products_owner_id_users", "products", type_="foreignkey")
    op.drop_column("products", "owner_id")
    op.drop_index("ix_products_sku", table_name="products")
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.drop_table("auth_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

"""add purchase_url to products

Revision ID: 5b7d2c9e4a10
Revises: e9c91ca81d68
Create Date: 2026-11-18 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# Identificador de la nueva migración.
revision = "5b7d2c9e4a10"
down_revision = "e9c91ca81d68"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enlace opcional a la tienda externa donde se compra el producto.
    op.add_column(
        "products",
        sa.Column("purchase_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    # Elimina la columna al revertir la migración.
    op.drop_column("products", "purchase_url")

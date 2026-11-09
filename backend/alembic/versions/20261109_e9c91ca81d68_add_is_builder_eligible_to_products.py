"""add is_builder_eligible to products

Revision ID: e9c91ca81d68
Revises: 13330fac7ad2
Create Date: 2026-11-09 18:11:57.185115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificador de la nueva migración.
revision = "e9c91ca81d68"
down_revision = "13330fac7ad2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agrega la columna con valor predeterminado False.
    op.add_column(
        "products",
        sa.Column(
            "is_builder_eligible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    # Elimina la columna al revertir la migración.
    op.drop_column("products", "is_builder_eligible")
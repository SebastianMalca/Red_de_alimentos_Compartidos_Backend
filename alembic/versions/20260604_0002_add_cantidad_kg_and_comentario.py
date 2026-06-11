"""add cantidad_kg to donaciones_lotes and comentario to trazabilidad_valoracion

Revision ID: 20260604_0002
Revises: 20260604_0001
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa


revision = "20260604_0002"
down_revision = "20260604_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "donaciones_lotes",
        sa.Column("cantidad_kg", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "trazabilidad_valoracion",
        sa.Column("comentario", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("trazabilidad_valoracion", "comentario")
    op.drop_column("donaciones_lotes", "cantidad_kg")

"""add_latitud_longitud_to_usuarios_puestos_comedores

Revision ID: 20260720_0004
Revises: d260471906c7
Create Date: 2026-07-20 14:16:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '20260720_0004'
down_revision = 'd260471906c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- usuarios ---
    op.add_column('usuarios', sa.Column('latitud', sa.Float(), nullable=True))
    op.add_column('usuarios', sa.Column('longitud', sa.Float(), nullable=True))

    # --- puestos_mercado ---
    op.add_column('puestos_mercado', sa.Column('latitud', sa.Float(), nullable=True))
    op.add_column('puestos_mercado', sa.Column('longitud', sa.Float(), nullable=True))

    # --- comedores ---
    op.add_column('comedores', sa.Column('latitud', sa.Float(), nullable=True))
    op.add_column('comedores', sa.Column('longitud', sa.Float(), nullable=True))


def downgrade() -> None:
    # --- comedores ---
    op.drop_column('comedores', 'longitud')
    op.drop_column('comedores', 'latitud')

    # --- puestos_mercado ---
    op.drop_column('puestos_mercado', 'longitud')
    op.drop_column('puestos_mercado', 'latitud')

    # --- usuarios ---
    op.drop_column('usuarios', 'longitud')
    op.drop_column('usuarios', 'latitud')

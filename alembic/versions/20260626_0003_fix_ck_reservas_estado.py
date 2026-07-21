"""fix_ck_reservas_estado: incluye Validado y Rechazado

Revision ID: 20260626_0003
Revises: d260471906c7
Create Date: 2026-06-26

El constraint original (migración inicial) solo aceptaba:
  'Pendiente de Recojo', 'Completada', 'Cancelada'

Esta migración lo reemplaza para incluir los 5 estados que el modelo
app/models/reserva.py ya declara:
  'Pendiente de Recojo', 'Validado', 'Completada', 'Cancelada', 'Rechazado'
"""
from alembic import op


revision = "20260626_0003"
down_revision = "d260471906c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("reservas") as batch_op:
        batch_op.drop_constraint("ck_reservas_estado", type_="check")
        batch_op.create_check_constraint(
            "ck_reservas_estado",
            "estado IN ('Pendiente de Recojo', 'Validado', 'Completada', 'Cancelada', 'Rechazado')",
        )


def downgrade() -> None:
    with op.batch_alter_table("reservas") as batch_op:
        batch_op.drop_constraint("ck_reservas_estado", type_="check")
        batch_op.create_check_constraint(
            "ck_reservas_estado",
            "estado IN ('Pendiente de Recojo', 'Completada', 'Cancelada')",
        )

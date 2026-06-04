"""initial schema

Revision ID: 20260604_0001
Revises:
Create Date: 2026-06-04

"""
from alembic import op
import sqlalchemy as sa


revision = "20260604_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre_completo", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=32), nullable=False),
        sa.CheckConstraint("rol IN ('GestorComedor', 'Comerciante')", name="ck_usuarios_rol"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuarios_email"), "usuarios", ["email"], unique=True)
    op.create_index(op.f("ix_usuarios_id"), "usuarios", ["id"], unique=False)

    op.create_table(
        "comedores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("nombre_comedor", sa.String(length=255), nullable=False),
        sa.Column("capacidad_personas", sa.Integer(), nullable=True),
        sa.Column("ubicacion_gps", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )
    op.create_index(op.f("ix_comedores_id"), "comedores", ["id"], unique=False)

    op.create_table(
        "puestos_mercado",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("nombre_puesto", sa.String(length=255), nullable=False),
        sa.Column("ubicacion_gps", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )
    op.create_index(op.f("ix_puestos_mercado_id"), "puestos_mercado", ["id"], unique=False)

    op.create_table(
        "donaciones_lotes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("puesto_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(length=500), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "estado IN ('Disponible', 'Reservado', 'Recogido')",
            name="ck_donaciones_lotes_estado",
        ),
        sa.ForeignKeyConstraint(["puesto_id"], ["puestos_mercado.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_donaciones_lotes_id"), "donaciones_lotes", ["id"], unique=False)

    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("comedor_id", sa.Integer(), nullable=False),
        sa.Column("donacion_id", sa.Integer(), nullable=False),
        sa.Column("fecha_reserva", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "estado IN ('Pendiente de Recojo', 'Completada', 'Cancelada')",
            name="ck_reservas_estado",
        ),
        sa.ForeignKeyConstraint(["comedor_id"], ["comedores.id"]),
        sa.ForeignKeyConstraint(["donacion_id"], ["donaciones_lotes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reservas_id"), "reservas", ["id"], unique=False)

    op.create_table(
        "trazabilidad_valoracion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reserva_id", sa.Integer(), nullable=False),
        sa.Column("comedor_id", sa.Integer(), nullable=False),
        sa.Column("puesto_id", sa.Integer(), nullable=False),
        sa.Column("fecha_recojo", sa.DateTime(timezone=True), nullable=False),
        sa.Column("huella_co2_ahorrada", sa.Float(), nullable=False),
        sa.Column("puntaje_frescura", sa.Integer(), nullable=False),
        sa.CheckConstraint("puntaje_frescura BETWEEN 1 AND 5", name="ck_trazabilidad_puntaje_frescura"),
        sa.ForeignKeyConstraint(["comedor_id"], ["comedores.id"]),
        sa.ForeignKeyConstraint(["puesto_id"], ["puestos_mercado.id"]),
        sa.ForeignKeyConstraint(["reserva_id"], ["reservas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reserva_id"),
    )
    op.create_index(
        op.f("ix_trazabilidad_valoracion_id"), "trazabilidad_valoracion", ["id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trazabilidad_valoracion_id"), table_name="trazabilidad_valoracion")
    op.drop_table("trazabilidad_valoracion")
    op.drop_index(op.f("ix_reservas_id"), table_name="reservas")
    op.drop_table("reservas")
    op.drop_index(op.f("ix_donaciones_lotes_id"), table_name="donaciones_lotes")
    op.drop_table("donaciones_lotes")
    op.drop_index(op.f("ix_puestos_mercado_id"), table_name="puestos_mercado")
    op.drop_table("puestos_mercado")
    op.drop_index(op.f("ix_comedores_id"), table_name="comedores")
    op.drop_table("comedores")
    op.drop_index(op.f("ix_usuarios_id"), table_name="usuarios")
    op.drop_index(op.f("ix_usuarios_email"), table_name="usuarios")
    op.drop_table("usuarios")

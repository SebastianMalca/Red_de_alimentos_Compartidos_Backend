from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class DonacionLote(Base):
    __tablename__ = "donaciones_lotes"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('Disponible', 'Reservado', 'Recogido', 'Rechazado', 'Cancelado')",
            name="ck_donaciones_lotes_estado",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    puesto_id = Column(Integer, ForeignKey("puestos_mercado.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    cantidad_kg = Column(Float, nullable=False, default=0)
    estado = Column(String(32), default="Disponible", nullable=False)
    tiempo_limite = Column(DateTime(timezone=True), nullable=True)
    foto_url = Column(String, nullable=True)

    puesto = relationship("PuestoMercado", back_populates="donaciones")
    reservas = relationship("Reserva", back_populates="donacion")

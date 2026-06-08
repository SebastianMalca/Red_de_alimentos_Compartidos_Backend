from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class DonacionLote(Base):
    __tablename__ = "donaciones_lotes"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('Disponible', 'Reservado', 'Recogido')",
            name="ck_donaciones_lotes_estado",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    puesto_id = Column(Integer, ForeignKey("puestos_mercado.id"), nullable=False)
    descripcion = Column(String(500), nullable=False)
    estado = Column(String(32), default="Disponible", nullable=False)

    puesto = relationship("PuestoMercado", back_populates="donaciones")
    reservas = relationship("Reserva", back_populates="donacion")

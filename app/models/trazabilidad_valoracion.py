from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base


class TrazabilidadValoracion(Base):
    """Registra recojo, impacto ambiental y valoración de frescura."""

    __tablename__ = "trazabilidad_valoracion"
    __table_args__ = (
        CheckConstraint("puntaje_frescura BETWEEN 1 AND 5", name="ck_trazabilidad_puntaje_frescura"),
    )

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), unique=True, nullable=False)
    comedor_id = Column(Integer, ForeignKey("comedores.id"), nullable=False)
    puesto_id = Column(Integer, ForeignKey("puestos_mercado.id"), nullable=False)
    fecha_recojo = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    huella_co2_ahorrada = Column(Float, nullable=False)
    puntaje_frescura = Column(Integer, nullable=False)

    reserva = relationship("Reserva", back_populates="trazabilidad")
    comedor = relationship("Comedor", back_populates="trazabilidades")
    puesto = relationship("PuestoMercado")

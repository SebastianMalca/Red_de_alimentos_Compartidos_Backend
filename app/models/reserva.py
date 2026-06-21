from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Reserva(Base):
    """Relaciona comedores con lotes reservados."""

    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('Pendiente de Recojo', 'Validado', 'Completada', 'Cancelada', 'Rechazado')",
            name="ck_reservas_estado",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    comedor_id = Column(Integer, ForeignKey("comedores.id"), nullable=False)
    donacion_id = Column(Integer, ForeignKey("donaciones_lotes.id"), nullable=False)
    fecha_reserva = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    estado = Column(String(32), default="Pendiente de Recojo", nullable=False)
    codigo_verificacion = Column(String, nullable=True)

    comedor = relationship("Comedor", back_populates="reservas")
    donacion = relationship("DonacionLote", back_populates="reservas")
    trazabilidad = relationship("TrazabilidadValoracion", back_populates="reserva", uselist=False)

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Comedor(Base):
    __tablename__ = "comedores"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=True)
    nombre_comedor = Column(String(255), nullable=False)
    capacidad_personas = Column(Integer)
    ubicacion_gps = Column(String(255))

    usuario = relationship("Usuario", back_populates="comedor")
    reservas = relationship("Reserva", back_populates="comedor")
    trazabilidades = relationship("TrazabilidadValoracion", back_populates="comedor")

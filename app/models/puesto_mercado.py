from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class PuestoMercado(Base):
    __tablename__ = "puestos_mercado"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), unique=True, nullable=True)
    nombre_puesto = Column(String(255), nullable=False)
    ubicacion_gps = Column(String(255))

    usuario = relationship("Usuario", back_populates="puesto_mercado")
    donaciones = relationship("DonacionLote", back_populates="puesto")

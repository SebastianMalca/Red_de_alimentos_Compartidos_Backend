from sqlalchemy import CheckConstraint, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint("rol IN ('GestorComedor', 'Comerciante')", name="ck_usuarios_rol"),
    )

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(32), nullable=False)

    puesto_mercado = relationship("PuestoMercado", back_populates="usuario", uselist=False)
    comedor = relationship("Comedor", back_populates="usuario", uselist=False)

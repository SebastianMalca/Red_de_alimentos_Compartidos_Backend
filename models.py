from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

# 1. TABLA BASE
class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False) # 'GestorComedor' o 'Comerciante'

# 2. PERFILES
class PuestoMercado(Base):
    __tablename__ = "puestos_mercado"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) # Relación 1:1 con Usuario
    nombre_puesto = Column(String, nullable=False)
    ubicacion_gps = Column(String)
    
    usuario = relationship("Usuario")

class Comedor(Base):
    __tablename__ = "comedores"
    
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id")) # Relación 1:1 con Usuario
    nombre_comedor = Column(String, nullable=False)
    capacidad_personas = Column(Integer)
    ubicacion_gps = Column(String)
    
    usuario = relationship("Usuario")

# 3. ENTIDADES DE NEGOCIO
class DonacionLote(Base):
    __tablename__ = "donaciones_lotes"
    
    id = Column(Integer, primary_key=True, index=True)
    puesto_id = Column(Integer, ForeignKey("puestos_mercado.id")) # Relación 1:N
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="Disponible") # Disponible, Reservado, Recogido
    
    puesto = relationship("PuestoMercado")

# 4. TABLAS TRANSACCIONALES
class Reserva(Base):
    """ Rompe la relación M:N 1: Comedores reservan Lotes de distintos Puestos """
    __tablename__ = "reservas"
    
    id = Column(Integer, primary_key=True, index=True)
    comedor_id = Column(Integer, ForeignKey("comedores.id"))
    donacion_id = Column(Integer, ForeignKey("donaciones_lotes.id"))
    fecha_reserva = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    estado = Column(String, default="Pendiente de Recojo")
    
    comedor = relationship("Comedor")
    donacion = relationship("DonacionLote")

class TrazabilidadValoracion(Base):
    """ Rompe la relación M:N 2: Comedores evalúan y recogen de distintos Puestos """
    __tablename__ = "trazabilidad_valoracion"
    
    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id"), unique=True)
    comedor_id = Column(Integer, ForeignKey("comedores.id"))
    puesto_id = Column(Integer, ForeignKey("puestos_mercado.id"))
    fecha_recojo = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Impacto y Calidad
    huella_co2_ahorrada = Column(Float)
    puntaje_frescura = Column(Integer)  # Ej: del 1 al 5
    
    reserva = relationship("Reserva")
    comedor = relationship("Comedor")
    puesto = relationship("PuestoMercado")
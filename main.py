from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base, Usuario, PuestoMercado, Comedor, DonacionLote, Reserva, TrazabilidadValoracion

# Configuración de Base de Datos
SQLALCHEMY_DATABASE_URL = "sqlite:///./red_alimentos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crea las tablas automáticamente al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API SQL - Red de Alimentos Compartidos")

# Dependencia de conexión a BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/")
def home():
    return {"mensaje": "🚀 API actualizada y funcionando con el nuevo diagrama E-R"}

@app.post("/reservar/{id_donacion}")
def reservar_donacion(id_donacion: int, comedor_id: int, db: Session = Depends(get_db)):
    """
    Endpoint ACTUALIZADO: Cambia el estado del lote y crea el registro en la tabla intermedia 'Reserva'
    """
    # Buscar la donación (Antes se llamaba LoteExcedente, ahora DonacionLote)
    donacion = db.query(DonacionLote).filter(DonacionLote.id == id_donacion).first()
    
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")
        
    if donacion.estado != "Disponible":
        raise HTTPException(status_code=400, detail="La donación ya no está disponible")
        
    # Paso 1: Actualizar el estado de la donación
    donacion.estado = "Reservado"  # type: ignore
    
    # Paso 2: Crear el registro en la tabla intermedia (Romper la relación M:N)
    nueva_reserva = Reserva(comedor_id=comedor_id, donacion_id=id_donacion)
    db.add(nueva_reserva)
    
    # Guardamos los cambios de ambas tablas al mismo tiempo (Transacción atómica)
    db.commit()
    
    return {"status": "éxito", "mensaje": f"Donación {id_donacion} reservada exitosamente por el comedor {comedor_id}"}
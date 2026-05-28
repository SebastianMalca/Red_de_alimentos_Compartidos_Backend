from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# 1. Configuración de la Base de Datos SQL (Usando SQLite localmente)
SQLALCHEMY_DATABASE_URL = "sqlite:///./red_alimentos.db"

# Engine es el motor de conexión
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Definir la Tabla SQL (Modelo E-R)
class LoteSQL(Base):
    __tablename__ = "lotes_excedentes"
    
    id = Column(Integer, primary_key=True, index=True)
    descripcion = Column(String, index=True)
    estado = Column(String, default="Disponible")

# Crear la base de datos y las tablas automáticamente si no existen
Base.metadata.create_all(bind=engine)

# 3. Crear la aplicación FastAPI
app = FastAPI(title="API SQL - Red de Alimentos Compartidos")

# Dependencia para abrir y cerrar la conexión en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 4. Endpoints
@app.get("/")
def home():
    return {"mensaje": "🚀 API SQL de Red de Alimentos funcionando"}

@app.post("/reservar/{id_donacion}")
def reservar_donacion(id_donacion: int, db: Session = Depends(get_db)):
    """
    Endpoint para mutar el estado de un lote a 'Reservado' en SQL
    """
    # Consulta SQL equivalente a: SELECT * FROM lotes_excedentes WHERE id = id_donacion
    lote = db.query(LoteSQL).filter(LoteSQL.id == id_donacion).first()
    
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
        
    if lote.estado != "Disponible":
        raise HTTPException(status_code=400, detail="El lote ya no está disponible")
        
    # Mutación de estado (El equivalente a UPDATE)
    lote.estado = "Reservado" # type: ignore
    db.commit()
    db.refresh(lote)
    
    return {"status": "éxito", "mensaje": f"Lote {id_donacion} reservado con éxito en SQL"}

# Endpoint temporal para crear un dato de prueba
@app.post("/crear-prueba")
def crear_lote_prueba(db: Session = Depends(get_db)):
    nuevo_lote = LoteSQL(descripcion="Cajón de tomates", estado="Disponible")
    db.add(nuevo_lote)
    db.commit()
    db.refresh(nuevo_lote)
    return {"mensaje": "Lote de prueba creado", "id": nuevo_lote.id}
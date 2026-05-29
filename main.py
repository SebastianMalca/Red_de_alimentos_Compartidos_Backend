from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
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

# CONFIGURACIÓN DE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que cualquier frontend (Web o Móvil) se conecte
    allow_credentials=True,
    allow_methods=["*"], # Permite peticiones GET, POST, etc.
    allow_headers=["*"],
)

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

@app.post("/crear-datos-prueba")
def crear_datos_prueba(db: Session = Depends(get_db)):
    """ Endpoint temporal para inyectar datos en la base de datos vacía """
    # 1. Crear un puesto falso si no existe
    puesto = db.query(PuestoMercado).first()
    if not puesto:
        puesto = PuestoMercado(nombre_puesto="Frutas Doña María", ubicacion_gps="Pabellón 3")
        db.add(puesto)
        db.commit()
        db.refresh(puesto)
    
    # 2. Crear una donación asociada a ese puesto
    nueva_donacion = DonacionLote(puesto_id=puesto.id, descripcion="10 kg de Plátanos maduros", estado="Disponible")
    db.add(nueva_donacion)
    db.commit()
    
    return {"mensaje": "Datos de prueba inyectados correctamente"}

@app.get("/donaciones")
def listar_donaciones(db: Session = Depends(get_db)):
    """ Devuelve la lista de todas las donaciones disponibles """
    # Selecciona solo los que dicen "Disponible"
    donaciones = db.query(DonacionLote).filter(DonacionLote.estado == "Disponible").all()
    return donaciones

@app.post("/confirmar-recojo/{id_reserva}")
def confirmar_recojo(id_reserva: int, puntaje_frescura: int, db: Session = Depends(get_db)):
    """ Endpoint de la 2da transacción M:N (Trazabilidad, Valoración y CO2) """
    
    # 1. Buscamos la reserva
    reserva = db.query(Reserva).filter(Reserva.id == id_reserva).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
    if reserva.estado != "Pendiente de Recojo":
        raise HTTPException(status_code=400, detail="Esta reserva ya fue recogida o cancelada")

    # 2. Buscamos la donación asociada para cambiar su estado
    donacion = db.query(DonacionLote).filter(DonacionLote.id == reserva.donacion_id).first()
    
    # LÓGICA DE NEGOCIO: Cálculo de CO2 (Ej: 2.5 kg de CO2 ahorrado por cada Lote)
    # En un sistema real esto se calcularía por peso real, aquí usamos un valor fijo para el MVP
    co2_calculado = 2.5 
    
    # 3. Creamos el registro en la 2da tabla intermedia (Trazabilidad)
    nueva_trazabilidad = TrazabilidadValoracion(
        reserva_id=reserva.id,
        comedor_id=reserva.comedor_id,
        puesto_id=donacion.puesto_id,
        huella_co2_ahorrada=co2_calculado,
        puntaje_frescura=puntaje_frescura
    )
    db.add(nueva_trazabilidad)
    
    # 4. Actualizamos los estados
    reserva.estado = "Completada"
    donacion.estado = "Recogido" # Ya no aparecerá en el Feed
    
    # 5. Guardamos todas las transacciones juntas de forma atómica
    db.commit()
    
    return {
        "mensaje": "Recojo confirmado exitosamente", 
        "impacto": f"¡Felicidades! Ahorraste {co2_calculado} kg de CO2",
        "puntaje_asignado": puntaje_frescura
    }

@app.get("/reservas-pendientes/{comedor_id}")
def ver_reservas_pendientes(comedor_id: int, db: Session = Depends(get_db)):
    """ Devuelve las donaciones que el comedor ya reservó pero aún no recoge """
    # 1. Buscamos las reservas con estado "Pendiente de Recojo"
    reservas = db.query(Reserva).filter(Reserva.comedor_id == comedor_id, Reserva.estado == "Pendiente de Recojo").all()
    
    # 2. Formateamos la info para que el celular muestre el nombre del producto
    resultado = []
    for r in reservas:
        donacion = db.query(DonacionLote).filter(DonacionLote.id == r.donacion_id).first()
        resultado.append({
            "id_reserva": r.id,
            "descripcion": donacion.descripcion if donacion else "Lote Reservado"
        })
        
    return resultado

@app.get("/mi-impacto/{comedor_id}")
def ver_impacto(comedor_id: int, db: Session = Depends(get_db)):
    """ Devuelve toda la trazabilidad y el CO2 ahorrado por un comedor """
    
    # 1. Traemos todos los registros de la tabla intermedia Trazabilidad
    recojos = db.query(TrazabilidadValoracion).filter(TrazabilidadValoracion.comedor_id == comedor_id).all()
    
    # 2. Sumamos todo el CO2 ahorrado
    co2_total = sum([r.huella_co2_ahorrada for r in recojos]) if recojos else 0.0
    
    # 3. Formateamos el historial para enviarlo al celular
    historial = []
    for r in recojos:
        historial.append({
            "id_trazabilidad": r.id,
            "fecha": r.fecha_recojo.strftime("%Y-%m-%d"),
            "co2": r.huella_co2_ahorrada,
            "frescura": r.puntaje_frescura
        })
        
    return {"co2_total": co2_total, "historial": historial}
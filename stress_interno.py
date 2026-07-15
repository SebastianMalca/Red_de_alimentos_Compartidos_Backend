import os
import time
from concurrent.futures import ThreadPoolExecutor

# Configurar variables de entorno para evitar fallos de inicializacion de dependencias externas
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummykey")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app
from app.models import Base
from app.services.seed_service import crear_datos_prueba

# 1. Configurar base de datos SQLite en memoria con pool estatico (hilo-seguro)
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear todas las tablas en la BD en memoria
Base.metadata.create_all(bind=engine)

# Poblar la BD usando el servicio de seeding
db = TestingSessionLocal()
crear_datos_prueba(db)
db.close()

# 2. Sobrescribir get_db en la aplicacion FastAPI para usar la BD en memoria
def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

app.dependency_overrides[get_db] = override_get_db

# Inicializar TestClient
client = TestClient(app)

# 3. Definir tarea de peticion concurrente
def hacer_peticion(id_hilo):
    inicio = time.time()
    try:
        # GET /donaciones no requiere autenticacion
        response = client.get("/donaciones")
        duracion = time.time() - inicio
        
        # Validar status 200 y tiempo de respuesta menor a 500ms (0.5s) sin usar simbolos menor/mayor
        tiempo_correcto = duracion.__lt__(0.5)
        status_correcto = response.status_code == 200
        
        if status_correcto and tiempo_correcto:
            return {"status": response.status_code, "duracion": duracion, "exito": True}
        else:
            return {"status": response.status_code, "duracion": duracion, "exito": False}
    except Exception as e:
        duracion = time.time() - inicio
        return {"status": 0, "duracion": duracion, "exito": False, "error": str(e)}

# 4. Lanzar 50 peticiones concurrentes
num_peticiones = 50
print("Iniciando prueba de estres interna en memoria...")

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(hacer_peticion, i) for i in range(num_peticiones)]
    resultados = [f.result() for f in futures]

# 5. Procesar metricas
exitosas = sum(1 for r in resultados if r["exito"])
fallidas = num_peticiones - exitosas
duraciones = [r["duracion"] for r in resultados]

promedio_ms = (sum(duraciones) / len(duraciones)) * 1000
maximo_ms = max(duraciones) * 1000
tasa_error = (fallidas / num_peticiones) * 100

# 6. Imprimir reporte ASCII muy limpio y profesional sin simbolos mayor/menor
print("\n" + "="*70)
print("                 REPORTE DE RENDIMIENTO INTERNO EN MEMORIA")
print("="*70)
print(f"{'Metrica':<30} | {'Valor':<35}")
print("-"*70)
print(f"{'Total de Peticiones':<30} | {num_peticiones:<35}")
print(f"{'Peticiones Exitosas':<30} | {exitosas:<35}")
print(f"{'Peticiones Fallidas':<30} | {fallidas:<35}")
print(f"{'Tiempo Promedio':<30} | {promedio_ms:.2f} ms")
print(f"{'Tiempo Maximo':<30} | {maximo_ms:.2f} ms")
print(f"{'Tasa de Errores':<30} | {tasa_error:.2f}%")
print("="*70)

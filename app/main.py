from contextlib import asynccontextmanager

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.routers import auth, donaciones, health, impacto, reservas, seed
from app.services.seed_service import crear_datos_prueba
import logging
import traceback
import sys

# Configura el logger para que se muestre en Cloud Logging
logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    # 1. Intentar correr migraciones de Alembic de forma segura
    try:
        logger.info("Iniciando migraciones de Alembic...")
        cfg = AlembicConfig("alembic.ini")
        alembic_command.upgrade(cfg, "head")
        logger.info("Migraciones de Alembic completadas con éxito.")
    except Exception as e:
        logger.error("ERROR CRÍTICO: Falló la ejecución de Alembic en el lifespan.")
        logger.error(traceback.format_exc())
        # Salimos de forma controlada o dejamos que propague para ver la traza completa
        sys.exit(3)

    # 2. Intentar inicializar datos de prueba
    db = SessionLocal()
    try:
        logger.info("Importando modelos y verificando datos de prueba...")
        from app.models import Usuario

        # Consultar si ya existen usuarios
        if not db.query(Usuario).first():
            logger.info("No se encontraron usuarios. Creando datos de prueba...")
            crear_datos_prueba(db)
            logger.info("Datos de prueba creados exitosamente.")
        else:
            logger.info("La base de datos ya contiene datos de usuarios.")
            
    except Exception as e:
        logger.error("ERROR CRÍTICO: Falló la consulta o creación de datos de prueba.")
        logger.error(traceback.format_exc())
        sys.exit(3)
    finally:
        db.close()
        logger.info("Sesión de base de datos cerrada en lifespan.")
    """
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="API SQL - Red de Alimentos Compartidos", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(donaciones.router)
    app.include_router(reservas.router)
    app.include_router(impacto.router)
    app.include_router(auth.router)
    app.include_router(seed.router)
    return app


app = create_app()

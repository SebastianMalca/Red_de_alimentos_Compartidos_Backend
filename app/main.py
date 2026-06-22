import asyncio
import logging
import traceback
import sys
from contextlib import asynccontextmanager

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, donaciones, health, impacto, reservas, seed
from app.services.seed_service import crear_datos_prueba
from app.services.expiracion_service import tarea_expiracion_periodica

# Configura el logger para que se muestre en Cloud Logging
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación.

    Al arrancar lanza la tarea en segundo plano que expira reservas vencidas
    cada 60 segundos. Al apagar la app la cancela limpiamente.
    """
    tarea = asyncio.create_task(tarea_expiracion_periodica(intervalo_segundos=60))
    logger.info("Tarea de expiración de reservas iniciada.")
    try:
        yield
    finally:
        tarea.cancel()
        try:
            await tarea
        except asyncio.CancelledError:
            pass
        logger.info("Tarea de expiración de reservas detenida.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FoodLinks API", lifespan=lifespan)

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

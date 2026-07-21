import logging
from contextlib import asynccontextmanager

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import auth, donaciones, health, impacto, reservas, seed
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.expiracion_service import run_expiration_task

# Configura el logger para que se muestre en Cloud Logging
logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación.

    Al arrancar lanza la tarea en segundo plano que expira reservas vencidas
    cada 10 minutos usando APScheduler. Al apagar la app la cancela limpiamente.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_expiration_task,
        trigger=IntervalTrigger(minutes=10),
        id="expiration_job",
        name="Expirar donaciones y reservas",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado. Tarea de expiración de reservas programada.")
    
    try:
        yield
    finally:
        scheduler.shutdown()
        logger.info("Scheduler detenido.")


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

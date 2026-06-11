from contextlib import asynccontextmanager

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.routers import auth, donaciones, health, impacto, reservas, seed
from app.services.seed_service import crear_datos_prueba


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = AlembicConfig("alembic.ini")
    alembic_command.upgrade(cfg, "head")
    db = SessionLocal()
    try:
        from app.models import Usuario

        if not db.query(Usuario).first():
            crear_datos_prueba(db)
    finally:
        db.close()
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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import donaciones, health, impacto, reservas, seed


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="API SQL - Red de Alimentos Compartidos")

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
    app.include_router(seed.router)
    return app


app = create_app()

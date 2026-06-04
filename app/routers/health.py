from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthOut, HomeOut


router = APIRouter(tags=["health"])


@router.get("/", response_model=HomeOut)
def home():
    return {"mensaje": "API Red de Alimentos funcionando"}


@router.get("/health", response_model=HealthOut)
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "service": "red-alimentos-backend",
        "environment": settings.env,
    }

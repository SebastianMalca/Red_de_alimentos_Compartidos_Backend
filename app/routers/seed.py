from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.donacion import DatosPruebaOut
from app.services.seed_service import crear_datos_prueba


router = APIRouter(tags=["seed"])


@router.post("/crear-datos-prueba", response_model=DatosPruebaOut)
def crear_seed(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.seed_endpoint_enabled:
        raise HTTPException(status_code=403, detail="Endpoint de prueba deshabilitado")

    return crear_datos_prueba(db)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.donacion import DonacionCreate, DonacionOut
from app.services.donaciones_service import crear_donacion, listar_donaciones_disponibles


router = APIRouter(prefix="/donaciones", tags=["donaciones"])


@router.get("", response_model=list[DonacionOut])
def listar_donaciones(db: Session = Depends(get_db)):
    return listar_donaciones_disponibles(db)


@router.post("", response_model=DonacionOut, status_code=201)
def crear(body: DonacionCreate, db: Session = Depends(get_db)):
    return crear_donacion(body.puesto_id, body.descripcion, body.cantidad_kg, db)

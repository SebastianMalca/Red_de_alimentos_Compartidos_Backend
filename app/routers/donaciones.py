from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.donacion import DonacionOut
from app.services.donaciones_service import listar_donaciones_disponibles


router = APIRouter(prefix="/donaciones", tags=["donaciones"])


@router.get("", response_model=list[DonacionOut])
def listar_donaciones(db: Session = Depends(get_db)):
    return listar_donaciones_disponibles(db)

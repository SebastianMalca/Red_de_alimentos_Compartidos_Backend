from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.impacto import ImpactoOut
from app.services.impacto_service import obtener_impacto_comedor


router = APIRouter(tags=["impacto"])


@router.get("/mi-impacto/{comedor_id}", response_model=ImpactoOut)
def ver_impacto(comedor_id: int, db: Session = Depends(get_db)):
    return obtener_impacto_comedor(comedor_id, db)

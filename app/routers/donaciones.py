from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.donacion import (
    DonacionCreate,
    DonacionEliminadaResponse,
    DonacionOut,
    DonacionUpdateEstado,
)
from app.schemas.reserva import ValidarReservaInput, ValidarReservaResponse
from app.services.donaciones_service import (
    actualizar_estado_donacion,
    crear_donacion,
    eliminar_donacion,
    listar_donaciones_disponibles,
    listar_donaciones_por_puesto,
    validar_entrega_service,
)


router = APIRouter(prefix="/donaciones", tags=["donaciones"])


@router.get("", response_model=list[DonacionOut])
def listar_donaciones(db: Session = Depends(get_db)):
    return listar_donaciones_disponibles(db)


@router.post("", response_model=DonacionOut, status_code=201)
def crear(body: DonacionCreate, db: Session = Depends(get_db)):
    return crear_donacion(body.puesto_id, body.descripcion, body.cantidad_kg, db)


@router.get("/mis-donaciones/{puesto_id}", response_model=list[DonacionOut])
def listar_mis_donaciones(puesto_id: int, estados: str | None = None, db: Session = Depends(get_db)):
    lista_estados = estados.split(",") if estados else None
    return listar_donaciones_por_puesto(puesto_id, db, lista_estados)


@router.post("/{id}/validar-entrega", response_model=ValidarReservaResponse)
def validar_entrega(id: int, payload: ValidarReservaInput, db: Session = Depends(get_db)):
    return validar_entrega_service(id, payload.codigo_verificacion, db)


@router.put("/{id}/estado")
def actualizar_estado(id: int, payload: DonacionUpdateEstado, db: Session = Depends(get_db)):
    return actualizar_estado_donacion(id, payload.estado, db)


@router.delete("/{id}", response_model=DonacionEliminadaResponse)
def eliminar(id: int, db: Session = Depends(get_db)):
    return eliminar_donacion(id, db)

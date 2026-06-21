from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reserva import (
    ConfirmarRecojoResponse,
    ReservaPendienteOut,
    ReservaResponse,
    ValidarReservaInput,
    ValidarReservaResponse,
)
from app.services.reservas_service import (
    confirmar_recojo,
    reservar_donacion,
    validar_reserva,
    ver_reservas_pendientes,
)


router = APIRouter(tags=["reservas"])


@router.post("/reservar/{id_donacion}", response_model=ReservaResponse)
def reservar(id_donacion: int, comedor_id: int, db: Session = Depends(get_db)):
    return reservar_donacion(id_donacion, comedor_id, db)


@router.get("/reservas-pendientes/{comedor_id}", response_model=list[ReservaPendienteOut])
def pendientes(comedor_id: int, db: Session = Depends(get_db)):
    return ver_reservas_pendientes(comedor_id, db)


@router.post("/confirmar-recojo/{id_reserva}", response_model=ConfirmarRecojoResponse)
def confirmar(
    id_reserva: int,
    puntaje_frescura: int = Query(..., ge=1, le=5),
    comentario: str = Query(""),
    db: Session = Depends(get_db),
):
    return confirmar_recojo(id_reserva, puntaje_frescura, comentario, db)


@router.post("/reservas/{id}/validar", response_model=ValidarReservaResponse)
def validar(
    id: int,
    payload: ValidarReservaInput,
    db: Session = Depends(get_db),
):
    """Verifica si el PIN o código QR recibido coincide con el
    ``codigo_verificacion`` almacenado para la reserva indicada."""
    return validar_reserva(id, payload.codigo_verificacion, db)

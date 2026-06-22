from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reserva import (
    ConfirmarEstadoInput,
    ConfirmarEstadoResponse,
    ConfirmarRecojoResponse,
    ReservaPendienteOut,
    ReservaResponse,
    ValidarReservaInput,
    ValidarReservaResponse,
)
from app.services.reservas_service import (
    confirmar_estado_reserva,
    confirmar_recojo,
    reservar_donacion,
    validar_reserva,
    ver_reservas_pendientes,
)
from app.services.expiracion_service import expirar_reservas_vencidas


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


@router.post("/reservas/{id}/confirmar", response_model=ConfirmarEstadoResponse)
def confirmar_estado(
    id: int,
    payload: ConfirmarEstadoInput,
    db: Session = Depends(get_db),
):
    """Confirma el estado definitivo de una reserva tras la validación presencial.

    - La reserva **debe** tener estado ``"Validado"``.
    - ``resultado = "Entregado"`` → calcula CO₂ (kg × 2.5) y lo registra.
    - ``resultado = "Rechazado" | "Cancelado"`` → cambia estado sin CO₂.
    """
    return confirmar_estado_reserva(
        id,
        payload.resultado,
        payload.puntaje_frescura,
        payload.comentario,
        db,
    )


@router.post(
    "/admin/expirar-reservas",
    summary="Expirar reservas vencidas (manual)",
    tags=["admin"],
)
def expirar_reservas(
    db: Session = Depends(get_db),
):
    """Dispara manualmente la expiración de reservas cuyo ``tiempo_limite``
    ya haya vencido.

    - Reservas en ``"Pendiente de Recojo"`` → ``"Cancelada"``.
    - Donación asociada → ``"Disponible"``.

    Normalmente esta lógica se ejecuta en segundo plano cada 60 s.
    Este endpoint permite forzarla desde Swagger o herramientas de admin.
    """
    return expirar_reservas_vencidas(db)

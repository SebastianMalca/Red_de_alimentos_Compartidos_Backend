"""Lógica de expiración de reservas.

Cuando el ``tiempo_limite`` de una donación ya pasó y su reserva aún está en
estado ``"Pendiente de Recojo"``, esta función:

1. Cambia el estado de la **reserva** → ``"Cancelada"``.
2. Devuelve el estado de la **donación** → ``"Disponible"``.

Puede invocarse de dos formas:
- **Tarea en segundo plano**: loop ``asyncio`` iniciado en el ``lifespan`` de la app.
- **Endpoint manual**: ``POST /admin/expirar-reservas`` (útil en pruebas y Swagger).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import _get_session_local
from app.models import DonacionLote, Reserva

logger = logging.getLogger(__name__)

ESTADO_PENDIENTE_RECOJO = "Pendiente de Recojo"
ESTADO_CANCELADA = "Cancelada"
ESTADO_DISPONIBLE = "Disponible"


def expirar_reservas_vencidas(db: Session) -> dict:
    """Expira en una sola transacción todas las reservas cuyo ``tiempo_limite``
    haya vencido.

    Returns:
        dict con las claves ``expiradas`` (int) y ``detalle`` (list[dict]).
    """
    ahora = datetime.now(timezone.utc)

    # Buscar reservas activas cuya donación ya venció
    reservas_vencidas: list[Reserva] = (
        db.query(Reserva)
        .join(DonacionLote, Reserva.donacion_id == DonacionLote.id)
        .filter(
            Reserva.estado == ESTADO_PENDIENTE_RECOJO,
            DonacionLote.tiempo_limite != None,       # noqa: E711
            DonacionLote.tiempo_limite < ahora,
        )
        .all()
    )

    if not reservas_vencidas:
        logger.debug("Expiración: no hay reservas vencidas en este ciclo.")
        return {"expiradas": 0, "detalle": []}

    detalle: list[dict] = []

    for reserva in reservas_vencidas:
        donacion: DonacionLote = reserva.donacion  # ya cargado por el join

        reserva.estado = ESTADO_CANCELADA
        donacion.estado = ESTADO_DISPONIBLE

        detalle.append(
            {
                "reserva_id": reserva.id,
                "donacion_id": donacion.id,
                "tiempo_limite": donacion.tiempo_limite.isoformat(),
            }
        )
        logger.info(
            "Reserva #%d expirada — donación #%d vuelve a 'Disponible'.",
            reserva.id,
            donacion.id,
        )

    db.commit()
    logger.info("Expiración completada: %d reserva(s) cancelada(s).", len(detalle))
    return {"expiradas": len(detalle), "detalle": detalle}


# ---------------------------------------------------------------------------
# Tarea en segundo plano
# ---------------------------------------------------------------------------

async def tarea_expiracion_periodica(intervalo_segundos: int = 60) -> None:
    """Corrutina que ejecuta :func:`expirar_reservas_vencidas` cada
    ``intervalo_segundos`` segundos.

    Debe iniciarse como tarea ``asyncio`` desde el ``lifespan`` de FastAPI.
    """
    import asyncio

    logger.info(
        "Tarea de expiración iniciada (intervalo: %ds).", intervalo_segundos
    )

    while True:
        await asyncio.sleep(intervalo_segundos)
        SessionLocal = _get_session_local()
        db: Session = SessionLocal()
        try:
            expirar_reservas_vencidas(db)
        except Exception:
            logger.exception("Error en la tarea de expiración de reservas.")
            db.rollback()
        finally:
            db.close()

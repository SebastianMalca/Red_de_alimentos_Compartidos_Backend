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
ESTADO_CANCELADA = "Cancelada"       # para reservas
ESTADO_CANCELADO = "Cancelado"       # para donaciones
ESTADO_DISPONIBLE = "Disponible"


def expirar_donaciones_y_reservas(db: Session) -> dict:
    """Expira en una sola transacción:
    1. Las reservas cuyo ``tiempo_limite`` haya vencido (la donación vuelve a Disponible).
    2. Las donaciones cuya ``fecha_hora_caducidad`` haya vencido (se cancela la donación y su reserva si tiene).
    """
    ahora = datetime.now(timezone.utc)
    detalle = []

    # 1. Expiración de reservas por tiempo de recojo vencido
    reservas_vencidas = (
        db.query(Reserva)
        .join(DonacionLote, Reserva.donacion_id == DonacionLote.id)
        .filter(
            Reserva.estado == ESTADO_PENDIENTE_RECOJO,
            DonacionLote.tiempo_limite != None,
            DonacionLote.tiempo_limite < ahora,
            (DonacionLote.fecha_hora_caducidad >= ahora) | (DonacionLote.fecha_hora_caducidad == None)
        )
        .all()
    )

    for reserva in reservas_vencidas:
        donacion = reserva.donacion
        reserva.estado = ESTADO_CANCELADA
        donacion.estado = ESTADO_DISPONIBLE
        detalle.append({"tipo": "tiempo_limite", "reserva_id": reserva.id, "donacion_id": donacion.id})
        logger.info("Reserva #%d expirada — donación #%d vuelve a 'Disponible'.", reserva.id, donacion.id)

    # 2. Expiración biológica de donaciones
    donaciones_caducadas = (
        db.query(DonacionLote)
        .filter(
            DonacionLote.estado.in_([ESTADO_DISPONIBLE, "Reservado"]),
            DonacionLote.fecha_hora_caducidad != None,
            DonacionLote.fecha_hora_caducidad < ahora,
        )
        .all()
    )

    for donacion in donaciones_caducadas:
        donacion.estado = ESTADO_CANCELADO
        # Buscar reservas activas para cancelar
        for reserva in donacion.reservas:
            if reserva.estado == ESTADO_PENDIENTE_RECOJO:
                reserva.estado = ESTADO_CANCELADA
                detalle.append({"tipo": "caducidad_biologica", "reserva_id": reserva.id, "donacion_id": donacion.id})
                logger.info("Reserva #%d cancelada por caducidad biológica de la donación #%d.", reserva.id, donacion.id)

        detalle.append({"tipo": "caducidad_biologica", "donacion_id": donacion.id})
        logger.info("Donación #%d cancelada por caducidad biológica.", donacion.id)

    if detalle:
        db.commit()
        logger.info("Expiración completada: %d evento(s).", len(detalle))
    else:
        logger.debug("Expiración: no hay elementos vencidos en este ciclo.")

    return {"eventos": len(detalle), "detalle": detalle}


def run_expiration_task():
    """Función síncrona para ser llamada por APScheduler."""
    logger.info("Iniciando tarea de expiración programada por APScheduler...")
    SessionLocal = _get_session_local()
    db = SessionLocal()
    try:
        expirar_donaciones_y_reservas(db)
    except Exception:
        logger.exception("Error en la tarea de expiración.")
        db.rollback()
    finally:
        db.close()

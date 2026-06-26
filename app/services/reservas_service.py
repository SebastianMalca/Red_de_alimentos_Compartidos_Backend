import secrets

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Comedor, DonacionLote, Reserva, TrazabilidadValoracion


ESTADO_DISPONIBLE = "Disponible"
ESTADO_RESERVADO = "Reservado"
ESTADO_RECOGIDO = "Recogido"
ESTADO_PENDIENTE_RECOJO = "Pendiente de Recojo"
ESTADO_VALIDADO = "Validado"
ESTADO_COMPLETADA = "Completada"


def reservar_donacion(id_donacion: int, comedor_id: int, db: Session) -> dict:
    donacion = db.query(DonacionLote).filter(DonacionLote.id == id_donacion).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")

    comedor = db.query(Comedor).filter(Comedor.id == comedor_id).first()
    if not comedor:
        raise HTTPException(status_code=404, detail="Comedor no encontrado")

    updated = (
        db.query(DonacionLote)
        .filter(DonacionLote.id == id_donacion, DonacionLote.estado == ESTADO_DISPONIBLE)
        .update({DonacionLote.estado: ESTADO_RESERVADO}, synchronize_session=False)
    )
    if updated == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="La donación ya no está disponible")

    # Generar PIN numérico de 6 dígitos (criptográficamente seguro)
    codigo = f"{secrets.randbelow(1_000_000):06d}"

    nueva_reserva = Reserva(
        comedor_id=comedor_id,
        donacion_id=id_donacion,
        codigo_verificacion=codigo,
    )
    db.add(nueva_reserva)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear la reserva") from exc

    db.refresh(nueva_reserva)
    return {
        "status": "éxito",
        "mensaje": f"Donación {id_donacion} reservada exitosamente por el comedor {comedor_id}",
        "id_reserva": nueva_reserva.id,
        "codigo_verificacion": nueva_reserva.codigo_verificacion,
    }


def ver_reservas_pendientes(comedor_id: int, db: Session) -> list[dict]:
    reservas = (
        db.query(Reserva)
        .filter(
            Reserva.comedor_id == comedor_id,
            Reserva.estado.in_([ESTADO_PENDIENTE_RECOJO, ESTADO_VALIDADO]),
        )
        .all()
    )

    return [
        {
            "id_reserva": reserva.id,
            "descripcion": reserva.donacion.descripcion if reserva.donacion else "Lote Reservado",
            "estado": reserva.estado,
            "codigo_verificacion": reserva.codigo_verificacion or "",
        }
        for reserva in reservas
    ]


def cancelar_reserva(id_reserva: int, comedor_id: int, db: Session) -> dict:
    """Cancela una reserva activa perteneciente al comedor indicado.

    Reglas de negocio:
    - La reserva debe existir y pertenecer a ``comedor_id``. Si no, 404.
    - Solo se pueden cancelar reservas en estado ``"Pendiente de Recojo"``.
      Cualquier otro estado devuelve 400.
    - Al cancelar: reserva → ``"Cancelada"``, donación → ``"Disponible"``.
    """
    reserva = (
        db.query(Reserva)
        .filter(Reserva.id == id_reserva, Reserva.comedor_id == comedor_id)
        .first()
    )
    if not reserva:
        raise HTTPException(
            status_code=404,
            detail="Reserva no encontrada o no pertenece a este comedor",
        )

    if reserva.estado != ESTADO_PENDIENTE_RECOJO:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Solo se pueden cancelar reservas en estado 'Pendiente de Recojo'. "
                f"Estado actual: '{reserva.estado}'"
            ),
        )

    donacion = db.query(DonacionLote).filter(DonacionLote.id == reserva.donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación asociada no encontrada")

    reserva.estado = "Cancelada"
    donacion.estado = ESTADO_DISPONIBLE

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="No se pudo cancelar la reserva"
        ) from exc

    return {
        "mensaje": f"Reserva {id_reserva} cancelada correctamente.",
        "id_reserva": id_reserva,
        "estado_reserva": "Cancelada",
        "donacion_id": donacion.id,
        "estado_donacion": ESTADO_DISPONIBLE,
    }



def confirmar_recojo(id_reserva: int, puntaje_frescura: int, comentario: str, db: Session) -> dict:
    if not 1 <= puntaje_frescura <= 5:
        raise HTTPException(status_code=422, detail="El puntaje de frescura debe estar entre 1 y 5")

    reserva = db.query(Reserva).filter(Reserva.id == id_reserva).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if reserva.estado != ESTADO_PENDIENTE_RECOJO:
        raise HTTPException(status_code=400, detail="Esta reserva ya fue recogida o cancelada")

    donacion = db.query(DonacionLote).filter(DonacionLote.id == reserva.donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación asociada no encontrada")

    co2_calculado = round(donacion.cantidad_kg * 2.5, 2)
    nueva_trazabilidad = TrazabilidadValoracion(
        reserva_id=reserva.id,
        comedor_id=reserva.comedor_id,
        puesto_id=donacion.puesto_id,
        huella_co2_ahorrada=co2_calculado,
        puntaje_frescura=puntaje_frescura,
        comentario=comentario if comentario else None,
    )
    db.add(nueva_trazabilidad)
    reserva.estado = ESTADO_COMPLETADA
    donacion.estado = ESTADO_RECOGIDO

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo confirmar el recojo") from exc

    return {
        "mensaje": "Recojo confirmado exitosamente",
        "impacto": f"¡Felicidades! Ahorraste {co2_calculado} kg de CO2",
        "puntaje_asignado": puntaje_frescura,
        "comentario": comentario,
    }


def validar_reserva(id_reserva: int, codigo: str, db: Session) -> dict:
    """Verifica que el código recibido (PIN o QR) coincida con el
    ``codigo_verificacion`` almacenado en la reserva indicada."""

    reserva = db.query(Reserva).filter(Reserva.id == id_reserva).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    if not reserva.codigo_verificacion:
        raise HTTPException(
            status_code=400,
            detail="Esta reserva no tiene un código de verificación asignado",
        )

    # Comparación en tiempo constante para evitar ataques de timing
    es_valido = secrets.compare_digest(
        reserva.codigo_verificacion.strip(),
        codigo.strip(),
    )

    if es_valido:
        return {"valido": True, "mensaje": "Código válido. Reserva verificada correctamente."}

    return {"valido": False, "mensaje": "Código incorrecto. La verificación falló."}


# ---------------------------------------------------------------------------
# Confirmar estado definitivo de una reserva (entrega / rechazo / cancelación)
# ---------------------------------------------------------------------------

# Mapa de resultado → estado final en la reserva
_MAPA_ESTADO_FINAL = {
    "Entregado": ESTADO_COMPLETADA,
    "Rechazado": "Rechazado",
    "Cancelado": "Cancelada",
}


def confirmar_estado_reserva(
    id_reserva: int,
    resultado: str,
    puntaje_frescura: int | None,
    comentario: str | None,
    db: Session,
) -> dict:
    """Confirma el estado definitivo de una reserva tras la entrega presencial.

    Reglas de negocio:
    - La reserva **debe** estar en estado ``"Validado"`` (validación presencial
      ya completada). Si no, se rechaza con 400.
    - Si ``resultado == "Entregado"``:
        * ``puntaje_frescura`` es obligatorio (1-5).
        * Se calcula ``co2 = cantidad_kg * 2.5`` y se registra en
          ``trazabilidad_valoraciones``.
        * La reserva pasa a ``"Completada"`` y la donación a ``"Recogido"``.
    - Si ``resultado in {"Rechazado", "Cancelado"}``:
        * Se actualiza el estado de la reserva sin registrar CO₂.
        * La donación vuelve a ``"Disponible"`` si fue rechazada/cancelada.
    """

    reserva = db.query(Reserva).filter(Reserva.id == id_reserva).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    # ── 1. Verificar estado permitido ─────────────────────────────────────
    # "Cancelado" puede aplicarse tanto desde "Pendiente de Recojo" como desde
    # "Validado". Las otras acciones (Entregado, Rechazado) exigen "Validado".
    estados_validos_para_cancelar = {ESTADO_PENDIENTE_RECOJO, ESTADO_VALIDADO}
    if resultado == "Cancelado" and reserva.estado not in estados_validos_para_cancelar:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Solo se puede cancelar una reserva en estado 'Pendiente de Recojo' o 'Validado'. "
                f"Estado actual: '{reserva.estado}'"
            ),
        )
    elif resultado != "Cancelado" and reserva.estado != ESTADO_VALIDADO:
        raise HTTPException(
            status_code=400,
            detail=(
                f"La reserva debe estar en estado 'Validado' para confirmar '{resultado}'. "
                f"Estado actual: '{reserva.estado}'"
            ),
        )

    # ── 2. Obtener la donación asociada ────────────────────────────────────
    donacion = db.query(DonacionLote).filter(DonacionLote.id == reserva.donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación asociada no encontrada")

    co2_calculado: float | None = None

    if resultado == "Entregado":
        # ── 3a. Resultado: Entregado → calcular CO₂ ────────────────────────
        if puntaje_frescura is None or not (1 <= puntaje_frescura <= 5):
            raise HTTPException(
                status_code=422,
                detail="Para confirmar como 'Entregado' se requiere puntaje_frescura entre 1 y 5",
            )

        co2_calculado = round(donacion.cantidad_kg * 2.5, 2)

        nueva_trazabilidad = TrazabilidadValoracion(
            reserva_id=reserva.id,
            comedor_id=reserva.comedor_id,
            puesto_id=donacion.puesto_id,
            huella_co2_ahorrada=co2_calculado,
            puntaje_frescura=puntaje_frescura,
            comentario=comentario if comentario else None,
        )
        db.add(nueva_trazabilidad)
        donacion.estado = ESTADO_RECOGIDO

    else:
        # ── 3b. Rechazado / Cancelado → sin CO₂, donación vuelve a disponible
        donacion.estado = ESTADO_DISPONIBLE

    # ── 4. Actualizar estado de la reserva ─────────────────────────────────
    reserva.estado = _MAPA_ESTADO_FINAL[resultado]

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo actualizar el estado de la reserva",
        ) from exc

    mensaje_map = {
        "Entregado": f"Entrega confirmada. Se ahorraron {co2_calculado} kg de CO₂.",
        "Rechazado": "Donativo rechazado. No se contabilizó CO₂.",
        "Cancelado": "Entrega cancelada. No se contabilizó CO₂.",
    }

    return {
        "mensaje": mensaje_map[resultado],
        "estado_reserva": reserva.estado,
        "co2_ahorrado_kg": co2_calculado,
    }

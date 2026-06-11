from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Comedor, DonacionLote, Reserva, TrazabilidadValoracion


ESTADO_DISPONIBLE = "Disponible"
ESTADO_RESERVADO = "Reservado"
ESTADO_RECOGIDO = "Recogido"
ESTADO_PENDIENTE_RECOJO = "Pendiente de Recojo"
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

    nueva_reserva = Reserva(comedor_id=comedor_id, donacion_id=id_donacion)
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
    }


def ver_reservas_pendientes(comedor_id: int, db: Session) -> list[dict]:
    reservas = (
        db.query(Reserva)
        .filter(Reserva.comedor_id == comedor_id, Reserva.estado == ESTADO_PENDIENTE_RECOJO)
        .all()
    )

    return [
        {
            "id_reserva": reserva.id,
            "descripcion": reserva.donacion.descripcion if reserva.donacion else "Lote Reservado",
        }
        for reserva in reservas
    ]


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

    co2_calculado = 2.5
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

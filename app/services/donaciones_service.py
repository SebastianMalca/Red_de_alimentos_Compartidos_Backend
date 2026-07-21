from datetime import datetime, time

import secrets

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import DonacionLote, PuestoMercado, Reserva


def listar_donaciones_disponibles(db: Session) -> list[DonacionLote]:
    return db.query(DonacionLote).filter(DonacionLote.estado == "Disponible").all()


def listar_donaciones_por_puesto(puesto_id: int, db: Session, estados: list[str] | None = None) -> list[DonacionLote]:
    query = db.query(DonacionLote).filter(DonacionLote.puesto_id == puesto_id)
    if estados:
        query = query.filter(DonacionLote.estado.in_(estados))
    return query.order_by(DonacionLote.id.desc()).all()


def validar_entrega_service(donacion_id: int, codigo: str, db: Session) -> dict:
    donacion = db.query(DonacionLote).filter(DonacionLote.id == donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")

    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.donacion_id == donacion_id,
            Reserva.estado.in_(["Pendiente de Recojo"]),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(
            status_code=400,
            detail="No hay una reserva pendiente para esta donación",
        )
    if not reserva.codigo_verificacion:
        raise HTTPException(
            status_code=400,
            detail="Esta reserva no tiene un código de verificación asignado",
        )
    if not secrets.compare_digest(reserva.codigo_verificacion.strip(), codigo.strip()):
        raise HTTPException(status_code=400, detail="Código incorrecto. La verificación falló.")

    reserva.estado = "Validado"
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="No se pudo actualizar el estado de la reserva"
        ) from exc

    return {"valido": True, "mensaje": "Código válido. Reserva verificada correctamente."}


def actualizar_estado_donacion(donacion_id: int, nuevo_estado: str, db: Session) -> dict:
    VALIDOS = {"Disponible", "Reservado", "Recogido", "Rechazado", "Cancelado"}
    if nuevo_estado not in VALIDOS:
        raise HTTPException(status_code=422, detail=f"Estado inválido: {nuevo_estado}")

    donacion = db.query(DonacionLote).filter(DonacionLote.id == donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")

    if nuevo_estado == "Cancelado" and donacion.estado in ("Reservado", "Validado"):
        reserva = (
            db.query(Reserva)
            .filter(
                Reserva.donacion_id == donacion_id,
                Reserva.estado.in_(["Pendiente de Recojo", "Validado"]),
            )
            .first()
        )
        if reserva:
            reserva.estado = "Cancelada"

    donacion.estado = nuevo_estado
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo actualizar el estado") from exc

    return {"mensaje": f"Donación {donacion_id} actualizada a '{nuevo_estado}'", "id": donacion_id, "estado": nuevo_estado}


def eliminar_donacion(donacion_id: int, db: Session) -> dict:
    donacion = db.query(DonacionLote).filter(DonacionLote.id == donacion_id).first()
    if not donacion:
        raise HTTPException(status_code=404, detail="Donación no encontrada")

    from app.models import TrazabilidadValoracion

    reservas = db.query(Reserva).filter(Reserva.donacion_id == donacion_id).all()
    for r in reservas:
        db.query(TrazabilidadValoracion).filter(TrazabilidadValoracion.reserva_id == r.id).delete()
    db.query(Reserva).filter(Reserva.donacion_id == donacion_id).delete()
    db.delete(donacion)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo eliminar la donación") from exc

    return {"mensaje": f"Donación {donacion_id} eliminada permanentemente", "id": donacion_id}


def crear_donacion(
    puesto_id: int,
    descripcion: str,
    cantidad_kg: float,
    db: Session,
    tiempo_limite: datetime | None = None,
    foto_url: str | None = None,
    hora_inicio: time | None = None,
    hora_fin: time | None = None,
    fecha_hora_caducidad: datetime | None = None,
) -> DonacionLote:
    puesto = db.query(PuestoMercado).filter(PuestoMercado.id == puesto_id).first()
    if not puesto:
        raise HTTPException(status_code=404, detail="Puesto de mercado no encontrado")

    if cantidad_kg <= 0:
        raise HTTPException(status_code=400, detail="La cantidad en kg debe ser mayor que cero")

    if tiempo_limite:
        now = datetime.now(tiempo_limite.tzinfo) if tiempo_limite.tzinfo else datetime.now()
        if tiempo_limite < now:
            raise HTTPException(status_code=400, detail="El tiempo límite no puede estar en el pasado")

    donacion = DonacionLote(
        puesto_id=puesto_id,
        descripcion=descripcion,
        cantidad_kg=cantidad_kg,
        estado="Disponible",
        tiempo_limite=tiempo_limite,
        foto_url=foto_url,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        fecha_hora_caducidad=fecha_hora_caducidad,
    )
    db.add(donacion)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear la donación") from exc

    db.refresh(donacion)
    return donacion

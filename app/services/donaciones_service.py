from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import DonacionLote, PuestoMercado


def listar_donaciones_disponibles(db: Session) -> list[DonacionLote]:
    return db.query(DonacionLote).filter(DonacionLote.estado == "Disponible").all()


def crear_donacion(puesto_id: int, descripcion: str, cantidad_kg: float, db: Session) -> DonacionLote:
    puesto = db.query(PuestoMercado).filter(PuestoMercado.id == puesto_id).first()
    if not puesto:
        raise HTTPException(status_code=404, detail="Puesto de mercado no encontrado")

    donacion = DonacionLote(
        puesto_id=puesto_id,
        descripcion=descripcion,
        cantidad_kg=cantidad_kg,
        estado="Disponible",
    )
    db.add(donacion)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear la donación") from exc

    db.refresh(donacion)
    return donacion

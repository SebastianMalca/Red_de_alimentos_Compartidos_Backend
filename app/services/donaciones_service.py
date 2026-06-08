from sqlalchemy.orm import Session

from app.models import DonacionLote


def listar_donaciones_disponibles(db: Session) -> list[DonacionLote]:
    return db.query(DonacionLote).filter(DonacionLote.estado == "Disponible").all()

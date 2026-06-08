from sqlalchemy.orm import Session

from app.models import TrazabilidadValoracion


def obtener_impacto_comedor(comedor_id: int, db: Session) -> dict:
    recojos = (
        db.query(TrazabilidadValoracion)
        .filter(TrazabilidadValoracion.comedor_id == comedor_id)
        .order_by(TrazabilidadValoracion.fecha_recojo.desc())
        .all()
    )
    co2_total = sum(r.huella_co2_ahorrada for r in recojos) if recojos else 0.0

    historial = [
        {
            "id_trazabilidad": r.id,
            "fecha": r.fecha_recojo.strftime("%Y-%m-%d"),
            "co2": r.huella_co2_ahorrada,
            "frescura": r.puntaje_frescura,
        }
        for r in recojos
    ]

    return {"co2_total": co2_total, "historial": historial}

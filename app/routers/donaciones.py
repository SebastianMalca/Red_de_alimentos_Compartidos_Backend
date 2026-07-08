from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.donacion import (
    DonacionCreate,
    DonacionEliminadaResponse,
    DonacionOut,
    DonacionUpdateEstado,
)
from app.schemas.reserva import ValidarReservaInput, ValidarReservaResponse
from app.services.donaciones_service import (
    actualizar_estado_donacion,
    crear_donacion,
    eliminar_donacion,
    listar_donaciones_disponibles,
    listar_donaciones_por_puesto,
    validar_entrega_service,
)
from app.services.storage_service import subir_imagen


router = APIRouter(prefix="/donaciones", tags=["donaciones"])


@router.get("", response_model=list[DonacionOut])
def listar_donaciones(db: Session = Depends(get_db)):
    return listar_donaciones_disponibles(db)


@router.post("", response_model=DonacionOut, status_code=201)
async def crear(request: Request, db: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        form = await request.form()
        puesto_id = int(form["puesto_id"])
        descripcion = form["descripcion"]
        cantidad_kg = float(form["cantidad_kg"])

        tiempo_limite = None
        raw_tl = form.get("tiempo_limite")
        if raw_tl and isinstance(raw_tl, str):
            tiempo_limite = datetime.fromisoformat(raw_tl.replace("Z", "+00:00"))

        foto_url = None
        imagen_file = form.get("imagen")
        if imagen_file and hasattr(imagen_file, "read"):
            foto_url = await subir_imagen(imagen_file)
            if foto_url is None:
                raise HTTPException(502, "No se pudo subir la imagen a Supabase Storage")

        return crear_donacion(puesto_id, descripcion, cantidad_kg, db, tiempo_limite, foto_url)

    body = await request.json()
    parsed = DonacionCreate(**body)
    return crear_donacion(parsed.puesto_id, parsed.descripcion, parsed.cantidad_kg, db, parsed.tiempo_limite)


@router.get("/mis-donaciones/{puesto_id}", response_model=list[DonacionOut])
def listar_mis_donaciones(puesto_id: int, estados: str | None = None, db: Session = Depends(get_db)):
    lista_estados = estados.split(",") if estados else None
    return listar_donaciones_por_puesto(puesto_id, db, lista_estados)


@router.post("/{id}/validar-entrega", response_model=ValidarReservaResponse)
def validar_entrega(id: int, payload: ValidarReservaInput, db: Session = Depends(get_db)):
    return validar_entrega_service(id, payload.codigo_verificacion, db)


@router.put("/{id}/estado")
def actualizar_estado(id: int, payload: DonacionUpdateEstado, db: Session = Depends(get_db)):
    return actualizar_estado_donacion(id, payload.estado, db)


@router.delete("/{id}", response_model=DonacionEliminadaResponse)
def eliminar(id: int, db: Session = Depends(get_db)):
    return eliminar_donacion(id, db)

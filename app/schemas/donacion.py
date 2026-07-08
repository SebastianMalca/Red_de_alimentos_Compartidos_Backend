from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DonacionCreate(BaseModel):
    puesto_id: int
    descripcion: str
    cantidad_kg: float
    tiempo_limite: datetime | None = None


class DonacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descripcion: str
    cantidad_kg: float
    estado: str
    puesto_id: int
    foto_url: str | None = None
    tiempo_limite: datetime | None = None


class DonacionUpdateEstado(BaseModel):
    estado: str


class DonacionEliminadaResponse(BaseModel):
    mensaje: str
    id: int


class DatosPruebaOut(BaseModel):
    mensaje: str
    comedor_id: int
    puesto_id: int
    donacion_id: int

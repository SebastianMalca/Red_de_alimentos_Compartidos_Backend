from pydantic import BaseModel, ConfigDict


class DonacionCreate(BaseModel):
    puesto_id: int
    descripcion: str
    cantidad_kg: float


class DonacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descripcion: str
    cantidad_kg: float
    estado: str
    puesto_id: int


class DatosPruebaOut(BaseModel):
    mensaje: str
    comedor_id: int
    puesto_id: int
    donacion_id: int

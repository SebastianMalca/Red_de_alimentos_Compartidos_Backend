from pydantic import BaseModel


class TrazabilidadOut(BaseModel):
    id_trazabilidad: int
    fecha: str
    co2: float
    frescura: int


class ImpactoOut(BaseModel):
    co2_total: float
    historial: list[TrazabilidadOut]

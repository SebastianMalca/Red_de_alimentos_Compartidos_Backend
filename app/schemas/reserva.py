from pydantic import BaseModel


class ReservaResponse(BaseModel):
    status: str
    mensaje: str
    id_reserva: int


class ReservaPendienteOut(BaseModel):
    id_reserva: int
    descripcion: str


class ConfirmarRecojoResponse(BaseModel):
    mensaje: str
    impacto: str
    puntaje_asignado: int
    comentario: str | None = None


class ValidarReservaInput(BaseModel):
    codigo_verificacion: str


class ValidarReservaResponse(BaseModel):
    valido: bool
    mensaje: str

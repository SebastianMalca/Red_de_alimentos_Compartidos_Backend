from typing import Literal

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


# ── Confirmar entrega / rechazo / cancelación ──────────────────────────────


class ConfirmarEstadoInput(BaseModel):
    """Payload para POST /reservas/{id}/confirmar.

    ``resultado`` sólo acepta los tres valores posibles que el donante puede
    registrar al momento de la entrega presencial:

    - ``"Entregado"``  → se calcula y registra el ahorro de CO₂.
    - ``"Rechazado"``  → donativo rechazado; sin registro de CO₂.
    - ``"Cancelado"``  → entrega cancelada; sin registro de CO₂.
    """

    resultado: Literal["Entregado", "Rechazado", "Cancelado"]
    puntaje_frescura: int | None = None   # requerido sólo si resultado="Entregado"
    comentario: str | None = None


class ConfirmarEstadoResponse(BaseModel):
    mensaje: str
    estado_reserva: str
    co2_ahorrado_kg: float | None = None

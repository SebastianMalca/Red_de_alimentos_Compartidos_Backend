from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, model_validator


class DonacionCreate(BaseModel):
    puesto_id: int
    descripcion: str
    cantidad_kg: float
    tiempo_limite: datetime | None = None
    foto_base64: str | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    fecha_hora_caducidad: datetime | None = None

    @model_validator(mode='after')
    def validate_tiempos(self):
        if self.hora_inicio and self.hora_fin:
            if self.hora_fin <= self.hora_inicio:
                raise ValueError("La hora de fin debe ser posterior a la hora de inicio")
        if self.fecha_hora_caducidad:
            now = datetime.now(self.fecha_hora_caducidad.tzinfo) if self.fecha_hora_caducidad.tzinfo else datetime.now()
            if self.fecha_hora_caducidad <= now:
                raise ValueError("La fecha de caducidad debe ser en el futuro")
        return self


class DonacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descripcion: str
    cantidad_kg: float
    estado: str
    puesto_id: int
    foto_url: str | None = None
    tiempo_limite: datetime | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    fecha_hora_caducidad: datetime | None = None


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

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    service: str
    environment: str


class HomeOut(BaseModel):
    mensaje: str

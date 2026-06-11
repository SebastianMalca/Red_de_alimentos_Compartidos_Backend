from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    usuario_id: int
    nombre_completo: str
    email: str
    rol: str
    comedor_id: int | None = None
    puesto_id: int | None = None


class RegisterRequest(BaseModel):
    nombre_completo: str
    email: str
    password: str
    rol: str


class RegisterResponse(BaseModel):
    usuario_id: int
    nombre_completo: str
    email: str
    rol: str
    comedor_id: int | None = None
    puesto_id: int | None = None

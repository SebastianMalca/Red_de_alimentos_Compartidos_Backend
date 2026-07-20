from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
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
    direccion: str = Field(..., min_length=1, max_length=500, description="Dirección física del usuario")
    latitud: float = Field(..., ge=-90.0, le=90.0, description="Latitud GPS (-90 a 90)")
    longitud: float = Field(..., ge=-180.0, le=180.0, description="Longitud GPS (-180 a 180)")

    @field_validator("direccion")
    @classmethod
    def direccion_no_vacia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("La dirección no puede estar vacía")
        return v


class RegisterResponse(BaseModel):
    usuario_id: int
    nombre_completo: str
    email: str
    rol: str
    comedor_id: int | None = None
    puesto_id: int | None = None


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., min_length=1, description="ID Token de Google Sign-In")
    rol: str = Field(
        "GestorComedor",
        description="Rol a asignar si el usuario es nuevo (GestorComedor o Comerciante)",
    )

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ("GestorComedor", "Comerciante"):
            raise ValueError("Rol inválido. Debe ser GestorComedor o Comerciante")
        return v


class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str
    usuario_id: int
    nombre_completo: str
    email: str
    rol: str
    comedor_id: int | None = None
    puesto_id: int | None = None
    is_new_user: bool

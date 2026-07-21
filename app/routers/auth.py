from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    GoogleAuthRequest,
    GoogleAuthResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)
from app.services.auth_service import google_login, login, register


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
@router.post("/ingresar", response_model=LoginResponse)
def login_endpoint(body: LoginRequest, db: Session = Depends(get_db)):
    return login(body.email, body.password, db)

@router.post("/registro", response_model=RegisterResponse, status_code=201)
@router.post("/register", response_model=RegisterResponse, status_code=201)
def register_endpoint(body: RegisterRequest, db: Session = Depends(get_db)):
    return register(
        body.nombre_completo, body.email, body.password, body.rol,
        body.direccion, body.latitud, body.longitud, db,
    )

@router.post("/google", response_model=GoogleAuthResponse)
def google_auth_endpoint(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register a user via Google Sign-In ID Token."""
    return google_login(body.id_token, body.rol, db)

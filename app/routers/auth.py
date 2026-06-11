from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.services.auth_service import login, register


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login_endpoint(body: LoginRequest, db: Session = Depends(get_db)):
    return login(body.email, body.password, db)


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register_endpoint(body: RegisterRequest, db: Session = Depends(get_db)):
    return register(body.nombre_completo, body.email, body.password, body.rol, db)

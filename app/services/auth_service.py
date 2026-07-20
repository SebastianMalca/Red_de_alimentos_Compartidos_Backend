from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Comedor, PuestoMercado, Usuario


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def login(email: str, password: str, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not bcrypt.checkpw(password.encode("utf-8"), usuario.password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    comedor_id = None
    puesto_id = None

    if usuario.rol == "GestorComedor":
        comedor = db.query(Comedor).filter(Comedor.usuario_id == usuario.id).first()
        if comedor:
            comedor_id = comedor.id

    elif usuario.rol == "Comerciante":
        puesto = db.query(PuestoMercado).filter(PuestoMercado.usuario_id == usuario.id).first()
        if puesto:
            puesto_id = puesto.id

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": usuario.email, "usuario_id": usuario.id, "rol": usuario.rol},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario_id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "rol": usuario.rol,
        "comedor_id": comedor_id,
        "puesto_id": puesto_id,
    }


def register(
    nombre_completo: str,
    email: str,
    password: str,
    rol: str,
    direccion: str,
    latitud: float,
    longitud: float,
    db: Session,
) -> dict:
    if rol not in ("GestorComedor", "Comerciante"):
        raise HTTPException(status_code=422, detail="Rol inválido. Debe ser GestorComedor o Comerciante")

    existe = db.query(Usuario).filter(Usuario.email == email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado en el sistema")

    usuario = Usuario(
        nombre_completo=nombre_completo,
        email=email,
        password_hash=bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
        rol=rol,
        latitud=latitud,
        longitud=longitud,
    )
    db.add(usuario)
    db.flush()

    comedor_id = None
    puesto_id = None

    if rol == "GestorComedor":
        comedor = Comedor(
            usuario_id=usuario.id,
            nombre_comedor=nombre_completo,
            ubicacion_gps=direccion,
            latitud=latitud,
            longitud=longitud,
        )
        db.add(comedor)
        db.flush()
        comedor_id = comedor.id
    else:
        puesto = PuestoMercado(
            usuario_id=usuario.id,
            nombre_puesto=nombre_completo,
            ubicacion_gps=direccion,
            latitud=latitud,
            longitud=longitud,
        )
        db.add(puesto)
        db.flush()
        puesto_id = puesto.id

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="No se pudo crear la cuenta") from exc

    db.refresh(usuario)
    return {
        "usuario_id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "rol": usuario.rol,
        "comedor_id": comedor_id,
        "puesto_id": puesto_id,
    }


def google_login(token: str, rol: str, db: Session) -> dict:
    """Verify a Google ID Token, create user if needed, and return a system JWT."""
    settings = get_settings()

    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Sign-In no está configurado en el servidor",
        )

    # --- Verify Google ID Token ---
    try:
        id_info = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Google inválido: {exc}",
        ) from exc

    google_email: str = id_info.get("email", "")
    google_name: str = id_info.get("name", google_email)
    email_verified: bool = id_info.get("email_verified", False)

    if not google_email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La cuenta de Google no tiene un correo verificado",
        )

    # --- Find or create local user ---
    is_new_user = False
    usuario = db.query(Usuario).filter(Usuario.email == google_email).first()

    if usuario is None:
        is_new_user = True
        usuario = Usuario(
            nombre_completo=google_name,
            email=google_email,
            password_hash="",  # No local password for Google accounts
            rol=rol,
        )
        db.add(usuario)
        db.flush()

        if rol == "GestorComedor":
            comedor = Comedor(
                usuario_id=usuario.id,
                nombre_comedor=google_name,
            )
            db.add(comedor)
        else:
            puesto = PuestoMercado(
                usuario_id=usuario.id,
                nombre_puesto=google_name,
            )
            db.add(puesto)

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se pudo crear la cuenta con Google",
            ) from exc

        db.refresh(usuario)

    # --- Resolve comedor_id / puesto_id ---
    comedor_id = None
    puesto_id = None

    if usuario.rol == "GestorComedor":
        comedor = db.query(Comedor).filter(Comedor.usuario_id == usuario.id).first()
        if comedor:
            comedor_id = comedor.id
    elif usuario.rol == "Comerciante":
        puesto = db.query(PuestoMercado).filter(PuestoMercado.usuario_id == usuario.id).first()
        if puesto:
            puesto_id = puesto.id

    # --- Issue system JWT ---
    access_token = create_access_token(
        data={"sub": usuario.email, "usuario_id": usuario.id, "rol": usuario.rol},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario_id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "rol": usuario.rol,
        "comedor_id": comedor_id,
        "puesto_id": puesto_id,
        "is_new_user": is_new_user,
    }

from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Comedor, PuestoMercado, Usuario


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def login(email: str, password: str, db: Session) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not pwd_context.verify(password, usuario.password_hash):
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

    return {
        "usuario_id": usuario.id,
        "nombre_completo": usuario.nombre_completo,
        "email": usuario.email,
        "rol": usuario.rol,
        "comedor_id": comedor_id,
        "puesto_id": puesto_id,
    }


def register(nombre_completo: str, email: str, password: str, rol: str, db: Session) -> dict:
    if rol not in ("GestorComedor", "Comerciante"):
        raise HTTPException(status_code=422, detail="Rol inválido. Debe ser GestorComedor o Comerciante")

    existe = db.query(Usuario).filter(Usuario.email == email).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado en el sistema")

    usuario = Usuario(
        nombre_completo=nombre_completo,
        email=email,
        password_hash=pwd_context.hash(password),
        rol=rol,
    )
    db.add(usuario)
    db.flush()

    comedor_id = None
    puesto_id = None

    if rol == "GestorComedor":
        comedor = Comedor(
            usuario_id=usuario.id,
            nombre_comedor=nombre_completo,
        )
        db.add(comedor)
        db.flush()
        comedor_id = comedor.id
    else:
        puesto = PuestoMercado(
            usuario_id=usuario.id,
            nombre_puesto=nombre_completo,
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

from sqlalchemy.orm import Session

from app.models import Comedor, DonacionLote, PuestoMercado, Usuario
import bcrypt


def crear_datos_prueba(db: Session) -> dict:
    usuario_comedor = db.query(Usuario).filter(Usuario.email == "comedor.demo@redalimentos.local").first()
    if not usuario_comedor:
        usuario_comedor = Usuario(
            nombre_completo="Gestor Comedor Demo",
            email="comedor.demo@redalimentos.local",
            password_hash=bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode("utf-8"),
            rol="GestorComedor",
        )
        db.add(usuario_comedor)
        db.commit()
        db.refresh(usuario_comedor)

    comedor = db.query(Comedor).first()
    if not comedor:
        comedor = Comedor(
            usuario_id=usuario_comedor.id,
            nombre_comedor="Comedor Demo",
            capacidad_personas=80,
            ubicacion_gps="Zona Norte",
        )
        db.add(comedor)
        db.commit()
        db.refresh(comedor)

    usuario_puesto = db.query(Usuario).filter(Usuario.email == "puesto.demo@redalimentos.local").first()
    if not usuario_puesto:
        usuario_puesto = Usuario(
            nombre_completo="Comerciante Demo",
            email="puesto.demo@redalimentos.local",
            password_hash=bcrypt.hashpw(b"demo123", bcrypt.gensalt()).decode("utf-8"),
            rol="Comerciante",
        )
        db.add(usuario_puesto)
        db.commit()
        db.refresh(usuario_puesto)

    puesto = db.query(PuestoMercado).first()
    if not puesto:
        puesto = PuestoMercado(
            usuario_id=usuario_puesto.id,
            nombre_puesto="Frutas Doña María",
            ubicacion_gps="Pabellón 3",
        )
        db.add(puesto)
        db.commit()
        db.refresh(puesto)

    nueva_donacion = DonacionLote(
        puesto_id=puesto.id,
        descripcion="10 kg de Plátanos maduros",
        cantidad_kg=10,
        estado="Disponible",
    )
    db.add(nueva_donacion)
    db.commit()
    db.refresh(nueva_donacion)

    return {
        "mensaje": "Datos de prueba inyectados correctamente",
        "comedor_id": comedor.id,
        "puesto_id": puesto.id,
        "donacion_id": nueva_donacion.id,
    }

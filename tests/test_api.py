from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import create_app
from app.models import Base


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_donacion_reserva_recojo_e_impacto(client: TestClient) -> None:
    seed_response = client.post("/crear-datos-prueba")
    assert seed_response.status_code == 200
    seed_data = seed_response.json()

    donaciones_response = client.get("/donaciones")
    assert donaciones_response.status_code == 200
    donaciones = donaciones_response.json()
    assert len(donaciones) == 1

    reservar_response = client.post(
        f"/reservar/{seed_data['donacion_id']}", params={"comedor_id": seed_data["comedor_id"]}
    )
    assert reservar_response.status_code == 200
    id_reserva = reservar_response.json()["id_reserva"]

    pendientes_response = client.get(f"/reservas-pendientes/{seed_data['comedor_id']}")
    assert pendientes_response.status_code == 200
    assert pendientes_response.json() == [
        {"id_reserva": id_reserva, "descripcion": "10 kg de Plátanos maduros"}
    ]

    confirmar_response = client.post(
        f"/confirmar-recojo/{id_reserva}",
        params={"puntaje_frescura": 5, "comentario": "Muy fresca la fruta"},
    )
    assert confirmar_response.status_code == 200
    assert confirmar_response.json()["puntaje_asignado"] == 5
    assert confirmar_response.json()["comentario"] == "Muy fresca la fruta"

    impacto_response = client.get(f"/mi-impacto/{seed_data['comedor_id']}")
    assert impacto_response.status_code == 200
    assert impacto_response.json()["co2_total"] == 25.0


def test_crear_donacion(client: TestClient) -> None:
    seed_response = client.post("/crear-datos-prueba")
    assert seed_response.status_code == 200
    seed_data = seed_response.json()

    response = client.post(
        "/donaciones",
        json={
            "puesto_id": seed_data["puesto_id"],
            "descripcion": "5 kg de Manzanas",
            "cantidad_kg": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["descripcion"] == "5 kg de Manzanas"
    assert data["cantidad_kg"] == 5
    assert data["estado"] == "Disponible"


def test_no_reserva_donacion_inexistente(client: TestClient) -> None:
    response = client.post("/reservar/999", params={"comedor_id": 1})

    assert response.status_code == 404
    assert response.json()["detail"] == "Donación no encontrada"


def test_registro_exitoso_comedor(client: TestClient) -> None:
    response = client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Comedor Nuevo",
            "email": "comedor.nuevo@example.com",
            "password": "mi_clave_segura",
            "rol": "GestorComedor",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "comedor.nuevo@example.com"
    assert data["rol"] == "GestorComedor"
    assert data["comedor_id"] is not None
    assert data["puesto_id"] is None


def test_registro_exitoso_comerciante(client: TestClient) -> None:
    response = client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Puesto Nuevo",
            "email": "puesto.nuevo@example.com",
            "password": "otra_clave_segura",
            "rol": "Comerciante",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "puesto.nuevo@example.com"
    assert data["rol"] == "Comerciante"
    assert data["puesto_id"] is not None
    assert data["comedor_id"] is None


def test_registro_email_duplicado(client: TestClient) -> None:
    # Registrar primero
    client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Usuario Uno",
            "email": "duplicado@example.com",
            "password": "password123",
            "rol": "GestorComedor",
        },
    )
    # Intentar registrar de nuevo con el mismo email
    response = client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Usuario Dos",
            "email": "duplicado@example.com",
            "password": "password456",
            "rol": "Comerciante",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "El correo ya está registrado en el sistema"


def test_login_exitoso(client: TestClient) -> None:
    # 1. Registrar un usuario de prueba
    client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Test User",
            "email": "login.test@example.com",
            "password": "mi_password_secreto",
            "rol": "GestorComedor",
        },
    )
    # 2. Intentar loguearse
    response = client.post(
        "/auth/login",
        json={
            "email": "login.test@example.com",
            "password": "mi_password_secreto",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "login.test@example.com"


def test_login_incorrecto_password(client: TestClient) -> None:
    # 1. Registrar usuario
    client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Test User 2",
            "email": "login.test2@example.com",
            "password": "mi_password_secreto",
            "rol": "GestorComedor",
        },
    )
    # 2. Intentar loguearse con contraseña incorrecta
    response = client.post(
        "/auth/login",
        json={
            "email": "login.test2@example.com",
            "password": "clave_equivocada",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"


def test_login_incorrecto_email(client: TestClient) -> None:
    # Intentar loguearse con un correo no registrado
    response = client.post(
        "/auth/login",
        json={
            "email": "no.existe@example.com",
            "password": "cualquier_clave",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales inválidas"

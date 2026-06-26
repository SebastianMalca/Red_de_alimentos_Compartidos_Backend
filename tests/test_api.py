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
    pendientes = pendientes_response.json()
    assert len(pendientes) == 1
    assert pendientes[0]["id_reserva"] == id_reserva
    assert pendientes[0]["descripcion"] == "10 kg de Plátanos maduros"
    assert pendientes[0]["codigo_verificacion"] != ""

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


# ---------------------------------------------------------------------------
# Tests de código de verificación (PIN) — criterios de aceptación del doc
# docs/requerimiento_codigo_verificacion.md
# ---------------------------------------------------------------------------

def _crear_reserva(client: TestClient) -> tuple[dict, int]:
    """Helper: crea datos de prueba, reserva la donación y devuelve
    (json de la respuesta, id_comedor)."""
    seed = client.post("/crear-datos-prueba").json()
    resp = client.post(
        f"/reservar/{seed['donacion_id']}",
        params={"comedor_id": seed["comedor_id"]},
    )
    assert resp.status_code == 200
    return resp.json(), seed["comedor_id"]


def test_pin_generado_al_reservar(client: TestClient) -> None:
    """Criterio 1: POST /reservar devuelve codigo_verificacion de 6 dígitos."""
    data, _ = _crear_reserva(client)

    assert "codigo_verificacion" in data, "El campo codigo_verificacion debe estar en la respuesta"
    pin = data["codigo_verificacion"]
    assert len(pin) == 6, f"El PIN debe tener 6 dígitos, tiene {len(pin)}"
    assert pin.isdigit(), f"El PIN debe ser numérico, se recibió: {pin!r}"


def test_validar_pin_correcto(client: TestClient) -> None:
    """Criterio 3: POST /reservas/{id}/validar con el PIN correcto → valido=True."""
    data, _ = _crear_reserva(client)
    id_reserva = data["id_reserva"]
    pin = data["codigo_verificacion"]

    resp = client.post(
        f"/reservas/{id_reserva}/validar",
        json={"codigo_verificacion": pin},
    )
    assert resp.status_code == 200
    assert resp.json()["valido"] is True


def test_validar_pin_incorrecto(client: TestClient) -> None:
    """Criterio 3 (negativo): PIN erróneo → valido=False."""
    data, _ = _crear_reserva(client)
    id_reserva = data["id_reserva"]

    resp = client.post(
        f"/reservas/{id_reserva}/validar",
        json={"codigo_verificacion": "000000"},
    )
    assert resp.status_code == 200
    assert resp.json()["valido"] is False


def test_pendientes_incluye_pin(client: TestClient) -> None:
    """Criterio 4: GET /reservas-pendientes incluye codigo_verificacion en cada ítem."""
    data, comedor_id = _crear_reserva(client)

    resp = client.get(f"/reservas-pendientes/{comedor_id}")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert "codigo_verificacion" in item, "Las reservas pendientes deben exponer el PIN"
    assert item["codigo_verificacion"] == data["codigo_verificacion"]


# ---------------------------------------------------------------------------
# Tests de cancelación de reserva
# ---------------------------------------------------------------------------

def test_cancelar_reserva_exitoso(client: TestClient) -> None:
    """Cancelar una reserva en 'Pendiente de Recojo' la pasa a 'Cancelada'
    y devuelve la donación a 'Disponible'."""
    data, comedor_id = _crear_reserva(client)
    id_reserva = data["id_reserva"]

    resp = client.delete(
        f"/reservas/{id_reserva}/cancelar",
        params={"comedor_id": comedor_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["estado_reserva"] == "Cancelada"
    assert body["estado_donacion"] == "Disponible"
    assert body["id_reserva"] == id_reserva

    # La reserva ya no debe aparecer en pendientes
    pendientes = client.get(f"/reservas-pendientes/{comedor_id}").json()
    assert pendientes == []

    # La donación debe aparecer de nuevo como disponible
    donaciones = client.get("/donaciones").json()
    assert any(d["estado"] == "Disponible" for d in donaciones)


def test_cancelar_reserva_ya_completada(client: TestClient) -> None:
    """Intentar cancelar una reserva que no está en 'Pendiente de Recojo' → 400."""
    seed = client.post("/crear-datos-prueba").json()
    reservar_resp = client.post(
        f"/reservar/{seed['donacion_id']}",
        params={"comedor_id": seed["comedor_id"]},
    )
    id_reserva = reservar_resp.json()["id_reserva"]

    # Completar la reserva primero
    client.post(
        f"/confirmar-recojo/{id_reserva}",
        params={"puntaje_frescura": 4, "comentario": ""},
    )

    # Ahora intentar cancelarla
    resp = client.delete(
        f"/reservas/{id_reserva}/cancelar",
        params={"comedor_id": seed["comedor_id"]},
    )
    assert resp.status_code == 400
    assert "Pendiente de Recojo" in resp.json()["detail"]


def test_cancelar_reserva_comedor_incorrecto(client: TestClient) -> None:
    """Intentar cancelar una reserva de otro comedor → 404."""
    data, _ = _crear_reserva(client)
    id_reserva = data["id_reserva"]

    resp = client.delete(
        f"/reservas/{id_reserva}/cancelar",
        params={"comedor_id": 9999},
    )
    assert resp.status_code == 404


def test_cancelar_reserva_inexistente(client: TestClient) -> None:
    """Intentar cancelar una reserva que no existe → 404."""
    resp = client.delete(
        "/reservas/9999/cancelar",
        params={"comedor_id": 1},
    )
    assert resp.status_code == 404


def test_cancelar_reserva_donacion_vuelve_disponible_para_otro_comedor(
    client: TestClient,
) -> None:
    """Tras cancelar, otro comedor puede reservar la misma donación."""
    seed = client.post("/crear-datos-prueba").json()
    reservar_resp = client.post(
        f"/reservar/{seed['donacion_id']}",
        params={"comedor_id": seed["comedor_id"]},
    )
    id_reserva = reservar_resp.json()["id_reserva"]

    # Cancelar
    client.delete(
        f"/reservas/{id_reserva}/cancelar",
        params={"comedor_id": seed["comedor_id"]},
    )

    # Registrar un segundo comedor
    client.post(
        "/auth/registro",
        json={
            "nombre_completo": "Segundo Comedor",
            "email": "segundo@example.com",
            "password": "pass1234",
            "rol": "GestorComedor",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "segundo@example.com", "password": "pass1234"},
    ).json()
    segundo_comedor_id = login["comedor_id"]

    # El segundo comedor puede reservar la misma donación
    nueva_reserva = client.post(
        f"/reservar/{seed['donacion_id']}",
        params={"comedor_id": segundo_comedor_id},
    )
    assert nueva_reserva.status_code == 200
    assert nueva_reserva.json()["id_reserva"] != id_reserva

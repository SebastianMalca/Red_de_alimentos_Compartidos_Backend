# Backend - Red de Alimentos Compartidos (API REST)

Servidor central construido con **Python**, **FastAPI**, **SQLAlchemy** y migraciones con **Alembic**.

Por defecto puede ejecutarse con SQLite para desarrollo local, pero la configuración ya está preparada para usar PostgreSQL mediante `DATABASE_URL`.

## Requisitos Previos

1. Tener instalado Python 3.12 o 3.13.
2. Tener un editor de código como VS Code.

## Configuración Local

**Paso 1: Entrar a la carpeta**

```bash
cd RedAlimentos-Backend
```

**Paso 2: Crear y activar el entorno virtual**

Windows:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

**Paso 3: Instalar dependencias**

```bash
pip install -r requirements.txt
```

**Paso 4: Configurar variables locales**

Para desarrollo con SQLite:

```text
DATABASE_URL=sqlite:///./red_alimentos.db
CORS_ORIGINS=*
ENV=development
SEED_ENDPOINT_ENABLED=true
```

Para PostgreSQL, la URL esperada será:

```text
DATABASE_URL=postgresql+psycopg://usuario:password@host:5432/red_alimentos
```

**Paso 5: Aplicar migraciones**

```bash
alembic upgrade head
```

**Paso 6: Iniciar el servidor**

Para que la app móvil pueda conectarse por Wi-Fi, inicia el servidor abriendo los puertos:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Paso 7: Probar la API**

Abre tu navegador y entra a: `http://127.0.0.1:8000/docs`.

Usa `/crear-datos-prueba` para llenar la base local con datos demo. Este endpoint se deshabilita automáticamente si `ENV=production`, salvo que configures explícitamente `SEED_ENDPOINT_ENABLED=true`.

## Estructura Actual

```text
app/
  core/       Configuración por entorno
  db/         Engine, sesiones y Base SQLAlchemy
  models/     Modelos ORM
  routers/    Endpoints FastAPI
  schemas/    Schemas Pydantic
  services/   Reglas de negocio
alembic/      Migraciones de base de datos
tests/        Pruebas de API
```

## Endpoints Principales

| Método | Endpoint | Propósito |
|---|---|---|
| `GET` | `/health` | Verifica que la API esté disponible |
| `POST` | `/crear-datos-prueba` | Crea datos demo para desarrollo |
| `GET` | `/donaciones` | Lista donaciones disponibles |
| `POST` | `/reservar/{id_donacion}` | Reserva un lote para un comedor |
| `GET` | `/reservas-pendientes/{comedor_id}` | Lista recojos pendientes |
| `POST` | `/confirmar-recojo/{id_reserva}` | Confirma recojo y registra impacto |
| `GET` | `/mi-impacto/{comedor_id}` | Devuelve CO2 total e historial |

## Comandos Útiles

```bash
pytest
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Preparación Para PostgreSQL

El código ya no depende de SQLite hardcodeado. Para migrar a PostgreSQL, cambia `DATABASE_URL`, instala dependencias y ejecuta las migraciones con Alembic.

No se incluye configuración de Docker ni Google Cloud en esta etapa.

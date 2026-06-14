# Backend - FoodLinks (API REST)

Servidor central construido con **Python**, **FastAPI**, **SQLAlchemy**, migraciones con **Alembic** y base de datos en **Supabase (PostgreSQL)**.

Plataforma de redistribución de alimentos que conecta **comerciantes de mercado** (con excedentes de comida) con **comedores comunitarios** (que los necesitan), permitiendo registrar donaciones, reservarlas, confirmar recojos y medir el impacto ambiental (CO₂ ahorrado).

## Requisitos Previos

1. Tener instalado Python 3.12 o superior.
2. Tener Git instalado.

## Configuración Local

**Paso 1: Entrar a la carpeta**

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DE_LA_CARPETA>
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

Crea un archivo llamado exactamente `.env` en la raíz del proyecto. Solicita las credenciales actuales al equipo:

```text
DATABASE_URL="postgresql+psycopg://postgres.<ID_PROYECTO>:<TU_CLAVE>@<POOLER_URL>:6543/postgres"
SUPABASE_URL="https://<ID_PROYECTO>.supabase.co"
SUPABASE_KEY="<TU_LLAVE_ANON_JWT>"
CORS_ORIGINS="*"
ENV="development"
SEED_ENDPOINT_ENABLED="true"
```

**Paso 5: Aplicar migraciones**

```bash
alembic upgrade head
```

**Paso 6: Iniciar el servidor**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Paso 7: Probar la API**

Abre tu navegador y entra a: `http://127.0.0.1:8000/docs`.

Usa el endpoint `POST /crear-datos-prueba` para inyectar datos demo si la base de datos está vacía.

## Autenticación y Roles

El sistema maneja dos roles de usuario:

| Rol | Descripción |
|---|---|
| `Comerciante` | Vendedor de mercado que publica lotes de comida disponible |
| `GestorComedor` | Encargado de comedor que reserva donaciones y gestiona recojos |

- **Registro**: `POST /auth/register` — crea un usuario y automáticamente genera un perfil de `comedor` o `puesto_mercado` según el rol.
- **Inicio de sesión**: `POST /auth/login` — verifica credenciales con bcrypt y devuelve el perfil del usuario junto con su `comedor_id` o `puesto_id`.
- No se utilizan tokens JWT; la sesión se maneja desde el cliente usando los IDs devueltos.

## Modelos de Datos

| Entidad | Descripción |
|---|---|
| `usuarios` | Usuarios del sistema con rol, email y contraseña hasheada |
| `puestos_mercado` | Puestos de mercado asociados a un `Comerciante` |
| `comedores` | Comedores comunitarios asociados a un `GestorComedor` |
| `donaciones_lotes` | Lotes de comida donados con cantidad (kg), estado y foto |
| `reservas` | Reservas de donaciones por parte de comedores |
| `trazabilidad_valoracion` | Registro de recojo, CO₂ ahorrado y puntaje de frescura (1-5) |

## Endpoints Principales

| Método | Endpoint | Propósito |
|---|---|---|
| `GET` | `/` | Home de la API |
| `GET` | `/health` | Verifica que la API esté disponible |
| `POST` | `/auth/login` | Inicio de sesión (email + password) |
| `POST` | `/auth/register` | Registro de usuario (`Comerciante` o `GestorComedor`) |
| `GET` | `/donaciones` | Lista donaciones disponibles |
| `POST` | `/donaciones` | Crea una nueva donación (requiere `puesto_id`) |
| `GET` | `/donaciones/mis-donaciones/{puesto_id}` | Lista donaciones de un puesto específico |
| `POST` | `/reservar/{id_donacion}` | Reserva un lote para un comedor |
| `GET` | `/reservas-pendientes/{comedor_id}` | Lista recojos pendientes de un comedor |
| `POST` | `/confirmar-recojo/{id_reserva}` | Confirma recojo, asigna frescura y registra impacto |
| `GET` | `/mi-impacto/{comedor_id}` | Devuelve CO₂ total ahorrado e historial |
| `POST` | `/crear-datos-prueba` | Crea datos demo para desarrollo |

## Supabase Storage

El proyecto incluye un servicio de subida de imágenes (`storage_service.py`) que se conecta al bucket `imagenes_donaciones` de Supabase Storage para almacenar fotos de los lotes donados.

## Pruebas

El proyecto usa **pytest** con `TestClient` de FastAPI y una base de datos **SQLite en memoria** que se crea y destruye por cada prueba.

```bash
pytest
```

Cobertura actual:
- Health check
- Flujo completo: crear datos → listar donaciones → reservar → confirmar recojo → ver impacto
- Creación de donación vía POST
- Error al reservar donación inexistente (404)

## Comandos Útiles

```bash
pytest
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Estructura del Proyecto

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

## Instrucciones para el equipo

1. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   ```

2. **Activar entorno**:
   - **Windows**:
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux**:
     ```bash
     source venv/bin/activate
     ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Migrar base de datos**:
   ```bash
   alembic upgrade head
   ```

5. **Iniciar servidor**:
   ```bash
   uvicorn main:app --reload
   ```

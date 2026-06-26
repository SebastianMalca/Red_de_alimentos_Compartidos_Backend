# Requerimiento backend — Estado en reservas pendientes (Tarea 14 frontend)

## Contexto
El frontend del comedor condiciona la pantalla de calificación al estado de la reserva:
las estrellas solo se habilitan cuando `estado == "Validado"`. Hoy el frontend mockea
este campo (flag `USAR_MOCK_ESTADO` en `src/api/reservas.ts`) porque el backend aún no lo expone.

## Cambios solicitados

### 0. (BLOQUEANTE) Migración: actualizar el CHECK constraint `ck_reservas_estado`
El modelo `app/models/reserva.py` ya declara los 5 estados
(`'Pendiente de Recojo', 'Validado', 'Completada', 'Cancelada', 'Rechazado'`),
pero la migración inicial `alembic/versions/20260604_0001_initial_schema.py` creó el
constraint en la BD solo con `('Pendiente de Recojo', 'Completada', 'Cancelada')`.
**Ninguna migración posterior lo actualizó**, así que la base real (Supabase) rechaza
`'Validado'` y `'Rechazado'`.

Esto rompe el propio endpoint `POST /reservas/{id}/confirmar`: no se puede dejar una
reserva en `'Validado'` (precondición) ni marcarla `'Rechazado'` sin violar el constraint.

Crear una migración de Alembic que reemplace el constraint:

```python
def upgrade():
    op.drop_constraint("ck_reservas_estado", "reservas", type_="check")
    op.create_check_constraint(
        "ck_reservas_estado",
        "reservas",
        "estado IN ('Pendiente de Recojo', 'Validado', 'Completada', 'Cancelada', 'Rechazado')",
    )
```

(En PostgreSQL/Supabase esto equivale a `ALTER TABLE reservas DROP CONSTRAINT ck_reservas_estado;`
seguido de `ADD CONSTRAINT ... CHECK (...)`.) Es prerrequisito de todo lo demás.

### 1. Exponer `estado` en `ReservaPendienteOut`
`app/schemas/reserva.py` — añadir el campo `estado: str`:

```python
class ReservaPendienteOut(BaseModel):
    id_reserva: int
    descripcion: str
    estado: str
```

Y en `app/services/reservas_service.py::ver_reservas_pendientes`, incluir
`"estado": reserva.estado` en cada dict retornado.

### 2. Incluir reservas en estado `Validado` en el listado
`ver_reservas_pendientes` hoy filtra `Reserva.estado == "Pendiente de Recojo"`. Debe
incluir también `"Validado"`, de lo contrario una reserva validada nunca aparece en la
lista de recojos del comedor:

```python
.filter(
    Reserva.comedor_id == comedor_id,
    Reserva.estado.in_(["Pendiente de Recojo", "Validado"]),
)
```

### 3. Permitir `Cancelado` desde `Pendiente de Recojo`
`POST /reservas/{id}/confirmar` exige `estado == "Validado"`. Decisión de producto:
"Cancelar reserva" debe estar disponible también antes de validar. Ajustar
`confirmar_estado_reserva` para permitir `resultado == "Cancelado"` cuando el estado sea
`"Pendiente de Recojo"` o `"Validado"` (Entregado/Rechazado siguen exigiendo `"Validado"`).

## Al integrar
Cuando estos cambios estén en producción, poner `USAR_MOCK_ESTADO = false` en
`src/api/reservas.ts` del frontend (o eliminar el bloque de mock).

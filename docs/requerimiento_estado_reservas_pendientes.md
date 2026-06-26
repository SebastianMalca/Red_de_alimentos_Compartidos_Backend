# Requerimiento backend — Estado en reservas pendientes (Tarea 14 frontend)

## Contexto
El frontend del comedor condiciona la pantalla de calificación al estado de la reserva:
las estrellas solo se habilitan cuando `estado == "Validado"`. Hoy el frontend mockea
este campo (flag `USAR_MOCK_ESTADO` en `src/api/reservas.ts`) porque el backend aún no lo expone.

## Cambios solicitados

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

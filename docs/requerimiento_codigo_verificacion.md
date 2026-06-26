# 🔧 Requerimiento Backend: Generación y exposición de `codigo_verificacion`

> **Solicitado por:** equipo Frontend (vista QR/PIN de verificación de reserva).
> **Estado:** pendiente de implementar en backend.
> **Bloquea:** Tarea #13 del frontend — "Vista que genera y muestra el QR/PIN de cada reserva".

---

## 🎯 Contexto

El frontend necesita mostrar, tras una reserva exitosa, un **código de verificación** (PIN numérico) que el gestor del comedor presenta como **QR** y como **texto grande** al momento del recojo. Ese código lo debe generar y entregar el backend.

Hoy el flujo **no funciona end-to-end** por dos motivos detectados en el código actual:

1. **El código nunca se genera.** La columna existe (`app/models/reserva.py:25` → `codigo_verificacion = Column(String, nullable=True)`), pero **ningún punto del código la asigna**. Hay un `import secrets` sin usar en `app/services/reservas_service.py:1`, lo que sugiere que la generación quedó pendiente.
2. **El endpoint de reserva no lo devuelve.** `ReservaResponse` (`app/schemas/reserva.py:6-9`) solo expone `status`, `mensaje`, `id_reserva`.

Consecuencia actual: toda reserva queda con `codigo_verificacion = NULL`, por lo que `POST /reservas/{id}/validar` (`reservas_service.py:118`) **siempre fallaría**, y el frontend recibiría `undefined`.

---

## ✅ Cambios solicitados

### 1. Generar el código al crear la reserva

En `reservar_donacion()` (`app/services/reservas_service.py:17`), generar un PIN **numérico de 6 dígitos** y guardarlo en la reserva antes del `commit`.

```python
# Generar PIN numérico de 6 dígitos (criptográficamente seguro)
codigo = f"{secrets.randbelow(1_000_000):06d}"  # ej. "048291"

nueva_reserva = Reserva(
    comedor_id=comedor_id,
    donacion_id=id_donacion,
    codigo_verificacion=codigo,
)
db.add(nueva_reserva)
```

> **Decisión de formato:** se acuerda **PIN numérico de 6 dígitos** (con cero a la izquierda preservado, por eso `String`). Sirve igual como contenido del QR y como texto legible. Evita ambigüedad alfanumérica (O/0, I/1).

### 2. Exponer el código en la respuesta de la reserva

Agregar el campo a `ReservaResponse` (`app/schemas/reserva.py`):

```python
class ReservaResponse(BaseModel):
    status: str
    mensaje: str
    id_reserva: int
    codigo_verificacion: str   # ← nuevo
```

Y devolverlo en el `return` de `reservar_donacion()`:

```python
return {
    "status": "éxito",
    "mensaje": f"Donación {id_donacion} reservada exitosamente por el comedor {comedor_id}",
    "id_reserva": nueva_reserva.id,
    "codigo_verificacion": nueva_reserva.codigo_verificacion,   # ← nuevo
}
```

### 3. (Recomendado) Permitir re-consultar el código en reservas pendientes

Para que el usuario pueda **volver a ver su QR** si sale de la pantalla, `ver_reservas_pendientes()` (`reservas_service.py:52`) y su schema `ReservaPendienteOut` (`app/schemas/reserva.py:12-14`) deberían incluir también `codigo_verificacion`.

```python
class ReservaPendienteOut(BaseModel):
    id_reserva: int
    descripcion: str
    codigo_verificacion: str   # ← nuevo (recomendado)
```

---

## 🔒 Consideraciones

- **Unicidad:** evaluar si el PIN debe ser único globalmente o solo por reserva. Como la validación ya es por `id` de reserva (`POST /reservas/{id}/validar`), la colisión global no rompe la seguridad, pero conviene documentarlo.
- **Migración de datos:** las reservas existentes con `codigo_verificacion = NULL` seguirán sin código. Definir si se backfillea o si se asume que solo las reservas nuevas tendrán código.
- **No exponer el código en endpoints públicos** ni en listados que no pertenezcan al comedor dueño de la reserva.

---

## 🧪 Criterio de aceptación

1. `POST /reservar/{id_donacion}` devuelve `codigo_verificacion` (6 dígitos) en el body.
2. El código queda persistido en la fila de la reserva.
3. `POST /reservas/{id}/validar` con ese mismo código devuelve `valido: true`.
4. (Si se implementa #3) `GET /reservas-pendientes/{comedor_id}` incluye el código de cada reserva.

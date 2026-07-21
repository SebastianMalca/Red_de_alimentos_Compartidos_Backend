# ⚠️ Tests Fallidos por Migración de Coordenadas

> **Autor:** Generado automáticamente — 20 de julio de 2026  
> **Estado:** Pendiente de corrección  
> **Prioridad:** Media  

---

## Contexto

Se agregaron los campos `latitud`, `longitud` y `direccion` a los modelos y schemas como parte de la tarea de **migración de coordenadas a la base de datos**. Los cambios fueron:

| Archivo | Cambio realizado |
|---|---|
| `app/models/usuario.py` | Se añadieron columnas `latitud` (Float) y `longitud` (Float) |
| `app/models/puesto_mercado.py` | Se añadieron columnas `latitud` (Float) y `longitud` (Float) |
| `app/models/comedor.py` | Se añadieron columnas `latitud` (Float) y `longitud` (Float) |
| `app/schemas/auth.py` | `RegisterRequest` ahora **exige** `direccion`, `latitud` y `longitud` |
| `app/services/auth_service.py` | `register()` ahora recibe y persiste los nuevos campos |
| `app/routers/auth.py` | Se pasan los nuevos campos al servicio |

---

## ¿Por qué fallan los tests?

El archivo `tests/test_api.py` envía requests de registro (`POST /auth/registro`) **sin los campos nuevos obligatorios**. Pydantic rechaza la petición con un error de validación `422 Unprocessable Entity` porque `direccion`, `latitud` y `longitud` son requeridos en `RegisterRequest`.

---

## Tests afectados

Los siguientes tests envían `POST /auth/registro` sin `direccion`, `latitud` ni `longitud`:

| # | Test | Línea | Motivo del fallo |
|---|---|---|---|
| 1 | `test_registro_exitoso_comedor` | L140-155 | Falta `direccion`, `latitud`, `longitud` → **422** en vez de 201 |
| 2 | `test_registro_exitoso_comerciante` | L158-173 | Falta `direccion`, `latitud`, `longitud` → **422** en vez de 201 |
| 3 | `test_registro_email_duplicado` | L176-196 | Ambos registros fallan con **422** antes de llegar al caso de email duplicado |
| 4 | `test_login_exitoso` | L199-220 | El registro previo falla con **422**, el usuario nunca se crea, el login falla |
| 5 | `test_login_incorrecto_password` | L223-241 | Mismo problema: el registro previo falla con **422** |
| 6 | `test_cancelar_reserva_donacion_vuelve_disponible_para_otro_comedor` | L391-427 | Registra un segundo comedor sin los campos nuevos → **422** |

---

## Cómo corregirlos

Cada JSON de registro debe incluir los tres campos nuevos. Ejemplo:

```python
# ❌ ANTES (falla con 422)
json={
    "nombre_completo": "Comedor Nuevo",
    "email": "comedor.nuevo@example.com",
    "password": "mi_clave_segura",
    "rol": "GestorComedor",
}

# ✅ DESPUÉS (funciona correctamente)
json={
    "nombre_completo": "Comedor Nuevo",
    "email": "comedor.nuevo@example.com",
    "password": "mi_clave_segura",
    "rol": "GestorComedor",
    "direccion": "Av. Test 123, Lima",
    "latitud": -12.0464,
    "longitud": -77.0428,
}
```

### Resumen de cambios necesarios

1. **En cada `client.post("/auth/registro", json={...})`** dentro de `tests/test_api.py`, agregar:
   - `"direccion"`: cualquier string no vacío (máx 500 caracteres)
   - `"latitud"`: float entre -90.0 y 90.0
   - `"longitud"`: float entre -180.0 y 180.0

2. **Opcionalmente**, agregar tests nuevos para validar que:
   - Se rechaza un registro sin `direccion` (422)
   - Se rechaza un registro con `latitud` fuera de rango (422)
   - Se rechaza un registro con `longitud` fuera de rango (422)

---

## Tests NO afectados

Los siguientes tests **no se ven impactados** y deberían seguir pasando sin cambios:

- `test_health`
- `test_donacion_reserva_recojo_e_impacto`
- `test_crear_donacion`
- `test_no_reserva_donacion_inexistente`
- `test_pin_generado_al_reservar`
- `test_validar_pin_correcto`
- `test_validar_pin_incorrecto`
- `test_pendientes_incluye_pin`
- `test_cancelar_reserva_exitoso`
- `test_cancelar_reserva_ya_completada`
- `test_cancelar_reserva_comedor_incorrecto`
- `test_cancelar_reserva_inexistente`
- `test_crear_donacion_cantidad_invalida`
- `test_crear_donacion_tiempo_limite_pasado`
- `test_flujo_e2e_completo_api` (usa credenciales del seed, no pasa por `/auth/registro`)

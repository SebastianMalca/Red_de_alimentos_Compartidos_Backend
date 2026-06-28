# Requerimiento: coordenadas de puestos y comedores para el mapa

## Contexto
La Tarea 15 del frontend integra `react-native-maps` y muestra puestos de mercado y comedores
como marcadores. Hoy el frontend usa datos mock porque el backend no expone coordenadas.

## Estado actual
- `puestos_mercado.ubicacion_gps` y `comedores.ubicacion_gps` son un único `String(255)`.
- El seed guarda texto descriptivo ("Zona Norte", "Pabellón 3"), no coordenadas.
- No existen endpoints de puestos ni comedores.

## Requerido
1. Almacenar **latitud** y **longitud** numéricas por puesto y por comedor (campos separados,
   o `ubicacion_gps` con formato parseable `"lat,lng"`).
2. Exponer endpoints de lectura:
   - `GET /puestos` → `[{ id, nombre, latitud, longitud }]`
   - `GET /comedores` → `[{ id, nombre, latitud, longitud }]`

## Integración frontend
Al estar listo, en `src/api/ubicaciones.ts` se reemplaza el mock por la llamada real
(ya dejada como TODO comentado). El tipo `UbicacionMapa` no cambia.

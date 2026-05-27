# Reglas de negocio — Argly

> Stub. Se completa en la fase F1. Basado en las secciones 7 y 8 del reto.

## Señales de posible fraude (con puntaje)

Cada señal aporta puntos al score. El total se normaliza a 0-100.

- Reclamo cercano al borde de vigencia (hasta 8 pts).
- Demora en denuncia por robo (hasta 8 pts).
- Alta frecuencia de reclamos por asegurado / vehículo / conductor.
- Alta frecuencia de reclamos solo RC.
- Beneficiario / proveedor recurrente o en Lista Restrictiva (hasta 10 pts).
- Documentos incompletos o inconsistentes (hasta 10 pts).
- Dinámica sospechosa del accidente (hasta 6 pts).
- Eventos sin tercero identificado (hasta 6 pts).
- Reporte tardío (hasta 5 pts).
- Narrativas similares / clonadas (hasta 8 pts).
- Monto cercano o superior a la suma asegurada (hasta 5 pts).

## Reglas críticas

| Código | Regla | Nivel |
|---|---|---|
| RF-01 | Pérdida Total por Robo (PTxRB) | Rojo |
| RF-02 | Falsificación o adulteración documental | Rojo |
| RF-03 | Coincidencia con Lista Restrictiva | Rojo |
| RF-04 | Dinámica del accidente físicamente imposible | Rojo |
| RF-05 | Siniestro al borde de vigencia (< 48 h) | Amarillo |
| RF-06 | Demora atípica en denuncia de robo (> 4 días) | Amarillo |
| RF-07 | Narrativa idéntica o clonada | Amarillo |

## Semáforo

| Rango | Nivel | Acción |
|---|---|---|
| 0-40 | 🟢 Verde | Flujo normal |
| 41-75 | 🟡 Amarillo | Revisión documental (Unidad Antifraude) |
| 76-100 | 🔴 Rojo | Revisión especializada de campo |

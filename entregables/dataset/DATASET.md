# Dataset Argly — Diccionario de datos

Dataset del prototipo **Argly** (detector de posible fraude en siniestros · hackIAthon 2026 · Reto Aseguradora del Sur).

> ⚠️ **100% sintético, sin PII real.** Generado de forma **reproducible** (semilla fija = 42) con
> patrones de posible fraude **plantados y etiquetados** para demostrar la detección y medir
> métricas reales. Todos los identificadores, teléfonos y montos son ficticios. Moneda: USD.
> Geografía: Ecuador.

---

## 1. Cifras del dataset

| Tabla | Filas | Rol |
|---|---|---|
| `asegurados.csv` | 600 | Maestro de clientes |
| `proveedores.csv` | 80 | Talleres, clínicas, peritos, abogados, concesionarios |
| `polizas.csv` | 891 | Pólizas por asegurado |
| `vehiculos.csv` | 466 | Vehículos asegurados (ramo Vehículos) |
| `siniestros.csv` | **1.465** | **Tabla central** — un siniestro por fila |
| `documentos.csv` | 4.395 | Documentos por siniestro (N:1) |
| `bandeja_resultado.csv` | 1.465 | **Salida del sistema**: score 0-100 + semáforo (no es input) |

**Etiqueta de fraude:** 365 fraude / 1.100 legítimos → **tasa 24.9 %**.
**Split:** `train` = 1.021 · `test` = 444. Los anillos (redes de proveedores) del *test* usan
proveedores **distintos** a los del *train* para evitar métricas circulares (sin fuga de datos).
**Ramos:** Vehículos 838 · Salud 247 · Generales 138 · Hogar 131 · Vida 111.

---

## 2. Modelo relacional

```
asegurados (id_asegurado)
   │  1:N
   ├──> polizas (id_poliza) ──1:N──> siniestros (id_siniestro)
   │                                     │  1:N
   │                                     └──> documentos (id_documento)
   ├──> vehiculos (placa) ───────────────┘  (siniestros.placa)
   │
proveedores (id_proveedor) ──────────────> siniestros (id_proveedor)

bandeja_resultado (id_siniestro)  1:1  siniestros   ← scoring del sistema
```

**Llaves de enlace:** `id_asegurado`, `id_poliza`, `id_proveedor`, `placa`, `id_conductor`, `id_siniestro`.

---

## 3. Diccionario por tabla

### `asegurados.csv` (600)
| Columna | Tipo | Descripción |
|---|---|---|
| `id_asegurado` | str | PK. Ej. `A00001`. |
| `segmento` | str | Masivo / Preferente / Corporativo / Pyme. |
| `ciudad` | str | Ciudad del asegurado (10 ciudades de Ecuador). |
| `antiguedad_meses` | int | Meses como cliente. |
| `score_cliente` | int | Score de comportamiento del cliente (≈300-900). |
| `telefono` | str | Teléfono ficticio. |
| `en_lista_restrictiva` | bool | Aparece en lista restrictiva (señal de riesgo). |
| `numero_polizas` | int | Pólizas vigentes. |
| `reclamos_ultimos_12_meses` | int | Frecuencia de reclamos recientes. |
| `mora_actual` | bool | Mora en pagos al momento. |

### `proveedores.csv` (80)
| Columna | Tipo | Descripción |
|---|---|---|
| `id_proveedor` | str | PK. Ej. `P0001`. |
| `tipo` | str | Taller / Clínica / Perito / Concesionario / Abogado. |
| `ciudad` | str | Ciudad del proveedor. |
| `antiguedad_meses` | int | Meses operando. |
| `en_lista_restrictiva` | bool | Proveedor observado/en lista restrictiva. |
| `reclamos_asociados` | int | Nº de siniestros asociados. |
| `monto_promedio_reclamado` | float | Monto medio reclamado vía este proveedor (USD). |
| `porcentaje_casos_observados` | float | % de sus casos marcados como observados (0-100). |

### `polizas.csv` (891)
| Columna | Tipo | Descripción |
|---|---|---|
| `id_poliza` | str | PK. Ej. `POL00814`. |
| `id_asegurado` | str | FK → asegurados. |
| `ramo` | str | Vehículos / Salud / Vida / Generales / Hogar. |
| `fecha_inicio` · `fecha_fin` | date | Vigencia de la póliza (`YYYY-MM-DD`). |
| `prima` | float | Prima pagada (USD). |
| `suma_asegurada` | float | Suma asegurada / límite (USD). |
| `deducible` | float | Deducible (USD). |
| `canal_venta` | str | Agente / Bróker / Digital / Sucursal / Call Center. |
| `ciudad` | str | Ciudad de emisión. |
| `estado_poliza` | str | Estado administrativo de la póliza. |

### `vehiculos.csv` (466)
| Columna | Tipo | Descripción |
|---|---|---|
| `placa` | str | PK. Ej. `OZC-5251`. |
| `chasis` · `motor` | str | Identificadores del vehículo. |
| `marca` · `modelo` | str | Marca y modelo. |
| `anio` | int | Año del vehículo. |
| `id_asegurado` | str | FK → asegurados. |
| `id_poliza` | str | FK → polizas. |

### `siniestros.csv` (1.465) — tabla central
| Columna | Tipo | Descripción |
|---|---|---|
| `id_siniestro` | str | PK. Ej. `SIN000001`. |
| `id_poliza` · `id_asegurado` · `id_proveedor` | str | FKs. |
| `placa` | str | FK → vehiculos (vacío si no aplica). |
| `id_conductor` | str | Conductor declarado. Ej. `C10546`. |
| `perdida_total` | bool | Declarado como pérdida total. |
| `ramo` · `cobertura` | str | Ramo y cobertura del siniestro. |
| `fecha_ocurrencia` · `fecha_reporte` | date | Fechas del evento y del aviso. |
| `monto_reclamado` | float | Monto reclamado (USD). |
| `monto_estimado` | float | Estimación del ajustador (USD). |
| `monto_pagado` | float | Monto efectivamente pagado (USD). |
| `estado` | str | Reserva / Pago Total / Pago Parcial / Anticipo / Negativa / Cierre Sin Consecuencia / Liquidado. |
| `sucursal` | str | Sucursal que gestiona. |
| `descripcion` | str | Narrativa libre del siniestro (usada por NLP). |
| `documentos_completos` | bool | Expediente documental completo. |
| `beneficiario_tipo` | str | Tipo de beneficiario del pago (Taller, Abogado, etc.). |
| `hora_ocurrencia` | int | Hora del evento (0-23). |
| `tipo_impacto` | str | frontal / posterior / lateral / volcadura / múltiple (Vehículos). |
| `tercero_identificado` | bool | ¿Se identificó al tercero? (relevante en RC). |
| `ciudad_ocurrencia` · `ciudad_taller` | str | Ciudades del evento y del taller (señal geográfica). |
| `clima_declarado` · `clima_real` | str | Clima declarado vs. real precomputado (señal de inconsistencia). |
| `patron` | str | **Patrón plantado** (ver §4). `legitimo` = no fraude. |
| `etiqueta_fraude_simulada` | int | **Etiqueta** 1 = fraude simulado, 0 = legítimo. |
| `split` | str | `train` / `test`. |
| `dias_desde_inicio_poliza` | int | Días entre inicio de póliza y ocurrencia (borde de vigencia). |
| `dias_desde_fin_poliza` | int | Días hasta el fin de vigencia. |
| `dias_entre_ocurrencia_reporte` | int | Demora de reporte (días). |
| `historial_siniestros_asegurado` | int | Nº de siniestros previos del asegurado. |

### `documentos.csv` (4.395)
| Columna | Tipo | Descripción |
|---|---|---|
| `id_documento` | str | PK. Ej. `DOC0000001`. |
| `id_siniestro` | str | FK → siniestros. |
| `tipo_documento` | str | Denuncia / Factura / Informe / etc. |
| `entregado` | bool | ¿Fue entregado? |
| `legible` | bool | ¿Es legible? |
| `fecha_emision` | date | Fecha de emisión. |
| `inconsistencia_detectada` | bool | Inconsistencia detectada en el documento. |
| `observacion` | str | Observación libre (vacío si ninguna). |

### `bandeja_resultado.csv` (1.465) — salida del sistema
| Columna | Tipo | Descripción |
|---|---|---|
| `id_siniestro` | str | FK → siniestros. |
| `score` | int | Riesgo 0-100 (fusión reglas + ML + anomalía). |
| `nivel` | str | Semáforo: VERDE (0-40) / AMARILLO (41-75) / ROJO (76-100). |
| `gate` | bool | Disparó un *hard gate* (regla crítica RF → ROJO). |
| `n_alertas` | int | Nº de señales activadas. |
| `motivo_principal` | str | Señal dominante (motivo top). |
| `ramo` · `cobertura` · `sucursal` | str | Contexto del caso. |
| `monto_reclamado` | float | Monto reclamado (USD). |
| `id_proveedor` · `id_asegurado` | str | FKs. |

---

## 4. Patrones de fraude plantados (`patron`)

Los 365 siniestros con `etiqueta_fraude_simulada = 1` se reparten en estos patrones, alineados con
las señales del reto y los *hard gates* (RF):

| `patron` | n | Qué simula | Señal / regla |
|---|---|---|---|
| `borde_vigencia` | 60 | Siniestro muy cerca del inicio o fin de vigencia | Borde de vigencia |
| `demora_robo` | 50 | Robo reportado con demora atípica | Demora ocurrencia→reporte |
| `frecuencia_asegurado` | 43 | Asegurado con siniestralidad anómala | Frecuencia por asegurado |
| `doc_inconsistente` | 30 | Documentos faltantes/ilegibles/inconsistentes | RF-02 (documental) |
| `monto_alto` | 25 | Monto reclamado cercano a la suma asegurada | Monto atípico |
| `sin_tercero` | 25 | RC sin tercero identificado | Tercero no identificado |
| `ptxrb` | 25 | Pérdida Total por Robo | **RF-01** (hard gate ROJO) |
| `red_proveedor` | 24 | Anillo de proveedores que concentran alertas | Red / colusión |
| `narrativa_clonada` | 20 | Narrativas casi idénticas entre siniestros | NLP similitud |
| `geo_imposible` | 20 | Distancia imposible ocurrencia↔taller | Señal geográfica |
| `clima_inconsistente` | 20 | Clima declarado ≠ clima real | Inconsistencia de clima |
| `frecuencia_rc` | 15 | Frecuencia anómala en Responsabilidad Civil | Frecuencia RC |
| `frecuencia_conductor` | 8 | Mismo conductor en múltiples siniestros | Frecuencia por conductor |
| `legitimo` | 1.100 | Siniestro normal (no fraude) | — |

---

## 5. Cómo regenerar (reproducible, semilla 42)

```bash
python -m src.ingestion.generate_synthetic   # reescribe los CSV en data/synthetic/
```

El dataset es **editable**: desde la vista *Datos* del war-room (o vía `POST /api/dataset/importar`)
se puede importar un dataset propio (un CSV por tabla; solo `siniestros` es obligatorio) en modo
*reemplazar* o *anexar*, y restaurar el sintético con `POST /api/dataset/reset`.

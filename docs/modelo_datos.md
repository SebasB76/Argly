# Modelo de datos — Argly

> Basado en la sección 6 del reto. Esquema real en `src/ingestion/models.py`.

## Tablas

- **siniestros** — `id_siniestro`, `id_poliza`, `id_asegurado`, `id_proveedor`,
  `placa`, `id_conductor`, `ramo`, `cobertura`, `perdida_total`,
  `fecha_ocurrencia`, `fecha_reporte`, `monto_reclamado`, `monto_estimado`,
  `monto_pagado`, `estado`, `sucursal`, `descripcion`, `documentos_completos`,
  `beneficiario_tipo`, `hora_ocurrencia`, `tipo_impacto`, `tercero_identificado`,
  `ciudad_ocurrencia`, `ciudad_taller`, `clima_declarado`, `clima_real`,
  `dias_desde_inicio_poliza`, `dias_desde_fin_poliza`,
  `dias_entre_ocurrencia_reporte`, `historial_siniestros_asegurado`,
  `etiqueta_fraude_simulada`, `split`.
- **polizas** — `id_poliza`, `id_asegurado`, `ramo`, `fecha_inicio`,
  `fecha_fin`, `prima`, `suma_asegurada`, `deducible`, `canal_venta`,
  `ciudad`, `estado_poliza`.
- **asegurados** — `id_asegurado`, `segmento`, `ciudad`, `antiguedad_meses`,
  `score_cliente`, `en_lista_restrictiva`, `numero_polizas`,
  `reclamos_ultimos_12_meses`, `mora_actual`.
- **proveedores** — `id_proveedor`, `tipo`, `ciudad`, `antiguedad_meses`,
  `en_lista_restrictiva`, `reclamos_asociados`, `monto_promedio_reclamado`,
  `porcentaje_casos_observados`.
- **vehiculos** — `placa`, `chasis`, `motor`, `marca`, `modelo`, `anio`,
  `id_asegurado`, `id_poliza`.
- **documentos** — `id_documento`, `id_siniestro`, `tipo_documento`,
  `entregado`, `legible`, `fecha_emision`, `inconsistencia_detectada`,
  `observacion`.

> El concepto de **conductor** (`id_conductor`) permite la señal de frecuencia por
> conductor (un mismo conductor en siniestros de varios asegurados). `perdida_total`
> + cobertura de robo activa la regla crítica **RF-01 (PTxRB)**.

## Relaciones

`asegurado 1—N poliza 1—N siniestro`. `siniestro N—1 proveedor`,
`siniestro N—1 vehiculo (placa)`, `siniestro N—1 conductor`, `siniestro 1—N documento`.

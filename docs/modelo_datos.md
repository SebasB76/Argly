# Modelo de datos — Argly

> Stub. Se completa en la fase F0. Basado en la sección 6 del reto.

## Tablas

- **siniestros** — `id_siniestro`, `id_poliza`, `id_asegurado`, `ramo`,
  `cobertura`, `fecha_ocurrencia`, `fecha_reporte`, `monto_reclamado`,
  `monto_estimado`, `monto_pagado`, `estado`, `sucursal`, `descripcion`,
  `documentos_completos`, `beneficiario`, `dias_desde_inicio_poliza`,
  `dias_desde_fin_poliza`, `dias_entre_ocurrencia_reporte`,
  `historial_siniestros_asegurado`, `etiqueta_fraude_simulada`.
- **polizas** — `id_poliza`, `id_asegurado`, `ramo`, `fecha_inicio`,
  `fecha_fin`, `prima`, `suma_asegurada`, `deducible`, `canal_venta`,
  `ciudad`, `estado_poliza`.
- **asegurados** — `id_asegurado`, `segmento`, `antiguedad`, `ciudad`,
  `num_polizas`, `reclamos_12m`, `mora_actual`, `score_cliente`.
- **proveedores** — `id_proveedor`, `tipo`, `ciudad`, `reclamos_asociados`,
  `monto_promedio`, `pct_casos_observados`, `antiguedad`, `en_lista_restrictiva`.
- **vehiculos** — `placa`, `chasis`, `motor`, `marca`, `modelo`, `anio`,
  `id_asegurado`.
- **documentos** — `id_documento`, `id_siniestro`, `tipo_documento`,
  `entregado`, `legible`, `fecha_emision`, `inconsistencia_detectada`,
  `observacion`.

## Relaciones

`asegurado 1—N poliza 1—N siniestro`. `siniestro N—1 proveedor`,
`siniestro N—1 vehiculo`, `siniestro 1—N documento`.

# Limitaciones, seguridad y ética — Argly

> Basado en las secciones 17 y 20 del reto.

## Principio rector

Argly genera **alertas de revisión, no acusaciones de fraude**. No rechaza
siniestros ni decide pagos. Toda decisión final es de un analista humano.

## Seguridad y privacidad

- Datos **100% sintéticos**, sin información personal real.
- Identificadores anonimizados.
- Sin credenciales ni llaves de API en el repositorio (`.env` ignorado).
- Fuentes de datos documentadas.

## Limitaciones del modelo

- Posibles **falsos positivos**: por eso se mantiene la revisión humana.
- Riesgo de **sesgo** en los datos: se audita por ciudad/segmento y se usan
  variables explicables.
- Entrenado sobre datos sintéticos: las métricas no representan la realidad
  operativa de una aseguradora.
- Dependencia de APIs externas (LLM, mapas, clima): se documentan y se prevé
  un modo de demostración alternativo.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Confundir alerta con acusación | Lenguaje de "posible fraude / requiere revisión". |
| Falsos positivos | Revisión humana + explicación de factores. |
| Modelo caja negra | Score descomponible + reglas activadas visibles. |
| Sobreajuste | Validación con datos separados. |
| Dependencia de APIs | Documentar y tener alternativa de demo. |

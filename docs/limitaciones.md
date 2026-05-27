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
- Entrenado sobre datos sintéticos: el ML **rankea dentro de escenarios
  sintéticos**, no prueba generalización al mundo real. Para no inflar métricas,
  el test set usa variantes de patrón **no vistas** en entrenamiento, y se
  compara `solo-reglas` vs `híbrido`.
- Dependencia de API externa: solo el LLM del agente; geo/clima/lista están
  precomputados en la DB. Si el LLM falla, hay **fallback determinista**.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Confundir alerta con acusación | Lenguaje de "posible fraude / requiere revisión". |
| Falsos positivos | Revisión humana + explicación de factores. |
| Modelo caja negra | Score descomponible + reglas activadas visibles. |
| Sobreajuste | Validación con datos separados. |
| Dependencia de APIs | Documentar y tener alternativa de demo. |

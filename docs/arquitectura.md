# Arquitectura — Argly

Sistema híbrido de detección de posible fraude en siniestros: reglas + ML +
anomalías + grafo + NLP + agente de IA.

## Capas

1. **Datos.** Generador sintético con patrones de fraude **plantados** y
   etiquetados (ground-truth) para demostrar detección y medir métricas.
   Almacenamiento PostgreSQL (Oracle a futuro). Tablas del reto.
2. **Features.** Variables de riesgo: días de vigencia, ocurrencia-reporte,
   frecuencias por asegurado/vehículo/conductor, ratio monto/suma asegurada.
3. **Scoring híbrido** (corazón). Cinco motores que se fusionan en un score
   0-100 + semáforo 🟢🟡🔴:
   - **Reglas** — rúbrica de señales del reto + reglas críticas RF-01..RF-07.
   - **ML supervisado** — XGBoost sobre la etiqueta simulada + SHAP.
   - **Anomalías** — Isolation Forest para lo "no evidente".
   - **Grafo** — red de entidades; anillos, centralidad, identidad compartida.
   - **NLP** — embeddings para similitud de narrativas; coherencia relato/daño.
4. **Agente investigador.** Tool-calling (consultar historial, red de proveedor,
   narrativas similares, consistencia documental, geo, clima, desglose de score).
   Investigación multipaso → dossier con evidencia citada. Responde las 12
   preguntas del reto y consultas libres en lenguaje natural.
5. **Enriquecimiento.** Google Maps, API de clima, validación de placa/RUC,
   Lista Restrictiva.
6. **Presentación.** Dashboard tipo sala de operaciones: bandeja priorizada,
   investigación en vivo, grafo de redes, mapa de siniestros, score descompuesto.
7. **Canales / salidas.** WhatsApp (aviso + botones + consulta), correo
   (digest + PDF), voz, PDF de dossier, push del score al core vía API.
8. **Ética / explicabilidad** (transversal). Score 100% descomponible, SHAP,
   auditoría de sesgo, sello "alerta ≠ acusación", humano en el ciclo, trazabilidad.

## Mapa a la rúbrica de evaluación

| Criterio | Peso | Cubierto por |
|---|---:|---|
| Uso de IA y prototipo | 40% | ML + NLP + anomalías + agente NL |
| Explicabilidad y ética | 25% | Capa 8 + score descomponible + SHAP |
| Análisis del caso y lógica | 15% | Grafo (redes) + cruce multivariable |
| Tecnología y arquitectura | 10% | Repo modular + API + FastAPI |
| Pitch, impacto y negocio | 10% | Dashboard + ahorro estimado + casos en vivo |

## Fases de construcción

`F0` datos sintéticos · `F1` features + reglas + score + bandeja ·
`F2` ML + anomalías + SHAP · `F3` grafo + anillos · `F4` NLP ·
`F5` agente + consultas NL · `F6` enriquecimiento · `F7` canales + API ·
`F8` ética + docs + pulido.

## Decisiones abiertas

- Tamaño del equipo y roles (ML / front / data).
- Días hasta el evento (define núcleo vs. extras).
- LLM: Claude o GPT; fallback local (Ollama) por si falla la API en vivo.
- Frontend web completo vs. notebook + web mínima.
- WhatsApp real vs. simulado en pantalla.
- Datos 100% sintéticos propios vs. dataset público base.
- Nombre definitivo del proyecto.

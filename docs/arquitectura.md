# Arquitectura — Argly

Sistema híbrido de detección de posible fraude en siniestros: reglas + ML +
anomalías + grafo + NLP + agente de IA. Construcción **core-first** (ver
`requerimientos.md`, etapas E0-E6).

## Capas

1. **Datos.** Generador sintético con patrones de fraude **plantados** y
   etiquetados (ground-truth). Train/test **separados**: el test usa variantes
   de patrón NO vistas en entrenamiento (evita métricas circulares). Señales
   geo/clima/lista restrictiva se **precomputan** en la DB (sin llamadas a APIs
   externas). PostgreSQL (Oracle a futuro). Tablas del reto.
2. **Features.** Variables de riesgo: días de vigencia, ocurrencia-reporte,
   frecuencias por asegurado/vehículo/conductor, ratio monto/suma asegurada.
3. **Scoring híbrido** (corazón). Cada motor devuelve contribuciones
   `{señal, puntos, evidencia}`; una fusión **versionada** las combina en 0-100
   + semáforo. **No es solo suma:** hay hard gates (RF-01..04 → Rojo sí o sí),
   topes por señal y total, y precedencia (gate > suma). El desglose ES la lista
   de contribuciones. Detalle en `reglas_negocio.md`.
   - **Reglas** — rúbrica del reto + RF-01..07 (núcleo, E1).
   - **ML supervisado** — XGBoost + SHAP (E2).
   - **Anomalías** — Isolation Forest (E2).
   - **Grafo** — networkx backend: anillos, identidad compartida (E4).
   - **NLP** — embeddings locales: similitud de narrativas, coherencia (E4).
4. **Agente investigador** (E5). Tool-calling sobre la base: historial, red de
   proveedor, narrativas similares, consistencia documental, desglose de score.
   **Narra** datos que ya calculan los motores (no los inventa). Responde las 12
   preguntas del reto + libres. Fallback determinista si la API del LLM falla.
5. **Enriquecimiento** (precomputado, sin APIs en vivo). Señales geo (distancias
   entre lugares con coordenadas sintéticas), clima (`clima_declarado` vs
   `clima_real`) y Lista Restrictiva, todo **sembrado en la DB** por el
   generador. Sin Google Maps / clima / RUC en vivo.
6. **Presentación.** Web para el analista: bandeja priorizada "Most Wanted",
   detalle de caso con score descompuesto y evidencia, mapa de siniestros.
   (Sin visualización interactiva de grafo por ahora.)
7. **Canales / salidas** (E6, cierre, solo si hay tiempo). PDF de dossier, push
   del score al core vía API. WhatsApp / correo / voz quedan como extensiones,
   fuera de la ruta crítica de la demo.
8. **Ética / explicabilidad** (transversal). Score 100% descomponible, SHAP,
   auditoría de sesgo, sello "alerta ≠ acusación", humano en el ciclo,
   trazabilidad hasta el dato origen.

## Mapa a la rúbrica de evaluación

| Criterio | Peso | Cubierto por |
|---|---:|---|
| Uso de IA y prototipo | 40% | ML + NLP + anomalías + agente NL |
| Explicabilidad y ética | 25% | Capa 8 + score descomponible + SHAP |
| Análisis del caso y lógica | 15% | Grafo (redes) + cruce multivariable |
| Tecnología y arquitectura | 10% | Repo modular + API + FastAPI |
| Pitch, impacto y negocio | 10% | Dashboard + ahorro estimado + casos en vivo |

## Etapas de construcción (core-first)

`E0` datos sintéticos + Postgres · `E1` features + reglas + score + bandeja ·
`E2` ML + anomalías + SHAP + métricas · `E3` API + web (bandeja + detalle) ·
`E4` grafo + NLP + geo + clima · `E5` agente + consultas NL · `E6` PDF + push +
notificaciones + pulido.

**Compuerta:** E0-E3 (núcleo) debe funcionar y ser demoable antes de E4-E6.

## Decisiones tomadas

- **Nombre:** Argly.
- **Stack:** React (SPA) + FastAPI + PostgreSQL.
- **LLM:** 1 proveedor barato compatible-OpenAI (DeepSeek o Llama vía Groq) + 1
  fallback determinista. **Sin** Claude SDK, Gemini ni Ollama.
- **Datos:** 100% sintéticos propios, con train/test separados.
- **Geo/clima/lista:** simulados y precomputados en la DB (sin APIs en vivo).
- **Grafo:** solo backend, sin visualización por ahora.
- **Alcance:** core-first con compuerta demoable.

## Diferido (revisión codex, post-núcleo)

- Analítica agregada como endpoints del core (Pareto de proveedores por % de
  alertas rojas, identidades compartidas, clusters de siniestros) → mejora #1/#5.
  Se evalúa después de que E0-E3 esté verde y demoable.

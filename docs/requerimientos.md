# Plan de Requerimientos — Argly

**hackIAthon 2026 · Reto Aseguradora del Sur**
Detector de posible fraude en siniestros · Estado: DRAFT · 2026-05-26

---

## 1. Visión

Argly es una **plataforma web interna** para analistas de siniestros y antifraude
de una aseguradora. Prioriza reclamos con señales de posible fraude mediante un
**score de riesgo explicable** que combina reglas de negocio, ML, NLP, detección de
anomalías y análisis de redes. **No acusa ni rechaza** un siniestro: genera
alertas, evidencia y recomendaciones para apoyar la revisión humana.

## 2. Objetivos

**General:** analizar siniestros, detectar patrones anómalos, asignar un score de
riesgo y explicar cada alerta para apoyar la decisión del analista.

**Específicos:**
- Procesar datos sintéticos de siniestros y entidades relacionadas.
- Calcular un score 0-100 y clasificarlo en semáforo 🟢🟡🔴.
- Generar alertas explicables y trazables.
- Responder consultas en lenguaje natural sobre casos, proveedores y patrones.
- Presentar todo en una plataforma web para el analista.
- Mantener al humano en el ciclo (sin decisión automática de pago o rechazo).

## 3. Alcance

**Incluye:** ingesta de datos, features de riesgo, motor de reglas, ML + anomalías,
NLP de narrativas, grafo de relaciones (backend), señales geo/clima, agente de IA,
web (bandeja + detalle), PDF de caso, API de integración, notificaciones.

**No incluye:** acusar o rechazar automáticamente, decisiones de pago, uso de datos
reales o PII, conclusiones legales, sustituir al analista humano.

## 4. Usuarios

| Usuario | Necesidad |
|---|---|
| Analista de siniestros | Priorizar casos y entender el porqué de cada alerta. |
| Analista antifraude | Identificar patrones, proveedores y redes sospechosas. |
| Jefatura / Riesgos | Visión consolidada de la exposición. |
| Auditoría interna | Evidencia y trazabilidad de cada caso. |

## 5. Requerimientos funcionales (RF)

| ID | Requerimiento |
|---|---|
| RF-01 | Generar un dataset sintético con patrones de fraude plantados y etiqueta ground-truth. |
| RF-02 | Ingerir y validar datos de siniestros, pólizas, asegurados, proveedores, vehículos y documentos. |
| RF-03 | Calcular variables de riesgo (días de vigencia, ocurrencia-reporte, frecuencias, ratio monto/suma, geo, clima). |
| RF-04 | Motor de reglas (señales del reto + reglas críticas RF-01..07) con puntaje trazable. |
| RF-05 | Calcular score 0-100 y clasificar en semáforo verde/amarillo/rojo. |
| RF-06 | Modelo ML supervisado (probabilidad de posible fraude) integrado al score. |
| RF-07 | Detección de anomalías (casos no evidentes) integrada al score. |
| RF-08 | Análisis NLP de narrativas: similitud/clonado + coherencia relato vs. siniestro. |
| RF-09 | Análisis de redes (backend): anillos, identidad compartida, proveedor recurrente, como señal al score. |
| RF-10 | Señales geográficas (distancias imposibles) y climáticas (declarado vs. real). |
| RF-11 | Explicabilidad: desglose del score por regla y variable + SHAP para el ML. |
| RF-12 | Agente de IA con tool-calling: investigación multipaso y respuestas en lenguaje natural (las 12 preguntas del reto + libres). |
| RF-13 | Web: bandeja priorizada ("Most Wanted") ordenada por riesgo con semáforo. |
| RF-14 | Web: detalle de caso con score, factores, evidencia y recomendación. |
| RF-15 | Generar un PDF (dossier) por caso para revisión y auditoría. |
| RF-16 | API para devolver score y alertas al core de siniestros (push, con receptor mock). |
| RF-17 | Notificaciones de alertas (WhatsApp / correo) con resumen del caso. |
| RF-18 | Reporte ejecutivo y métricas del lote procesado. |

## 6. Requerimientos no funcionales (RNF)

| ID | Requerimiento |
|---|---|
| RNF-01 | **Explicabilidad:** todo score debe ser descomponible y trazable hasta el dato origen. |
| RNF-02 | **Ética:** la salida es siempre "alerta de revisión, no acusación"; humano en el ciclo. |
| RNF-03 | **Privacidad:** datos 100% sintéticos, sin PII real, sin credenciales en el repositorio. |
| RNF-04 | **Reproducibilidad:** generación con semilla; `requirements.txt`; `.env.example`. |
| RNF-05 | **Modularidad:** código por módulos; API desacoplada del front. |
| RNF-06 | **Rendimiento / demo:** scoring y agente con latencia apta para demo en vivo; **fallback sin LLM** si la API externa falla. |
| RNF-07 | **Portabilidad de LLM:** proveedor-agnóstico (API compatible-OpenAI); modelo intercambiable. |
| RNF-08 | **Seguridad:** secretos solo en `.env`, nunca en código ni en el repo. |
| RNF-09 | **Auditoría de sesgo:** revisar sobre-marcado por ciudad/segmento. |

## 7. Modelo de datos

Tablas base del reto: `siniestros`, `polizas`, `asegurados`, `proveedores`,
`vehiculos`, `documentos` (detalle en [`modelo_datos.md`](modelo_datos.md)).

Campos añadidos para nuestras señales:
- `asegurados/proveedores`: `lat`, `lng` (geo), `en_lista_restrictiva`.
- `siniestros`: `clima_declarado`, `clima_real`, `hora_ocurrencia`, `tipo_impacto`, `tercero_identificado`.

> Nota: **RUC se descarta** (no está en las tablas del reto). **placa** sí se usa,
> pero solo de forma interna (misma placa/chasis repetida en varios siniestros).

## 8. Stack tecnológico

| Capa | Tecnología |
|---|---|
| Front | **React** (SPA interna) |
| Backend / API | **FastAPI** (Python) |
| Base de datos | **PostgreSQL** (Oracle = objetivo futuro) |
| ML / anomalías | scikit-learn, XGBoost, Isolation Forest, SHAP |
| NLP | sentence-transformers (embeddings **locales**, sin costo) |
| Grafo | networkx (backend, sin visualización por ahora) |
| Agente / LLM | API **compatible-OpenAI**, modelo barato (DeepSeek / Llama vía Groq) |
| Reportes | ReportLab (PDF) |

## 9. Etapas de entrega (incremental y testable)

| Etapa | Entrega | Prioridad | Qué se testea |
|---|---|---|---|
| **E0** | Generador sintético + carga a Postgres | Núcleo | Salen los datos con casos fraude/no-fraude. |
| **E1** | Features + reglas + score + bandeja | Núcleo | Siniestros rankeados con reglas disparadas. |
| **E2** | ML + anomalías + SHAP + métricas | Núcleo | Desglose del score y métricas (P/R/F1/AUC). |
| **E3** | API + web (bandeja + detalle) | Núcleo | El analista abre la web y revisa un caso. |
| **E4** | NLP + grafo + geo + clima | Diferenciador | Narrativa clonada / red / imposibilidad marcadas. |
| **E5** | Agente investigador (NL + dossier) | Diferenciador | Pregunta en lenguaje natural y arma el dossier. |
| **E6** | PDF + API push + notificaciones + pulido | Cierre | PDF generado, aviso disparado, demo redonda. |

Núcleo mínimo para testear: **E0-E3**. Si el tiempo aprieta, **E0-E3 + E5** ya es
un prototipo ganador.

## 10. Mapeo a criterios de evaluación

| Criterio | Peso | Cubierto por |
|---|---:|---|
| Uso de IA y prototipo | 40% | RF-06, RF-07, RF-08, RF-12 |
| Explicabilidad y ética | 25% | RF-11, RNF-01, RNF-02, RNF-09 |
| Análisis del caso y lógica | 15% | RF-04, RF-09, RF-10 |
| Tecnología y arquitectura | 10% | RNF-04, RNF-05, RF-16 |
| Pitch, impacto y negocio | 10% | RF-13, RF-15, RF-18 |

## 11. Métricas de éxito

- **Supervisado:** precision, recall, F1, matriz de confusión, AUC-ROC.
- **Anomalías:** % de casos marcados, ranking de rareza, validación cruzada con reglas.
- **NLP:** calidad de similitud y coherencia.
- **Negocio:** monto total priorizado para revisión (ahorro potencial estimado).

## 12. Restricciones

- **No** se usa Claude SDK ni Gemini; LLM barato vía API compatible-OpenAI.
- Datos **100% sintéticos**.
- Base de datos **PostgreSQL**; front **React**.
- Grafo solo en backend (sin visualización interactiva por ahora).

## 13. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Falla de la API del LLM en la demo | Fallback determinista sin LLM. |
| Falsos positivos | Revisión humana + explicación de factores. |
| Sesgo en datos | Auditoría por ciudad/segmento + variables explicables. |
| Confundir alerta con acusación | Lenguaje de "posible fraude / requiere revisión". |
| Demo depende de los datos | Patrones plantados y controlados en el generador. |

## 14. Entregables

Prototipo web funcional · código (repo `Argly`) · dataset sintético · `README` ·
documentación (arquitectura, modelo de datos, reglas, uso de IA, limitaciones,
requerimientos) · explicación del modelo · rúbrica de alertas · demo en vivo ·
pitch (PDF).

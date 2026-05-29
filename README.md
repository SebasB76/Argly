# Argly — Detector de posible fraude en siniestros

Prototipo de IA para el **hackIAthon 2026 · Reto Aseguradora del Sur**.

Argly analiza siniestros de seguros, asigna un **score de riesgo (0-100)** con
semáforo 🟢 🟡 🔴 y genera **alertas explicables** que priorizan los casos para
revisión humana.

> ⚠️ Argly genera **alertas de revisión, no acusaciones de fraude**. No rechaza
> siniestros ni decide pagos. La decisión final siempre es de un analista humano.

## Estado actual

| Etapa | Qué hace | Estado |
|---|---|---|
| **E0** | Datos sintéticos con patrones plantados + carga a Postgres/SQLite | ✅ |
| **E1** | Features + motor de reglas + score con gates/topes + bandeja | ✅ |
| **E2** | ML (RandomForest) + anomalías (Isolation Forest) + métricas | ✅ |
| **E3** | API FastAPI + front React (war-room) | ✅ |
| **E4** | Grafo de redes (anillos) + NLP de similitud + geo/clima | ✅ |
| **E5** | Agente de IA (consultas en lenguaje natural, 12 preguntas del reto) | ✅ |
| **E6** | PDF dossier + push al core (mock) + avisos WhatsApp/correo | ✅ |

**Métricas (test held-out, 444 casos):** AUC solo-reglas 0.83 → **híbrido 0.92** (modelo ML 0.95) · **precisión 0.97** · recall 0.80 · F1 0.88.
**Distribución:** 1150 🟢 · 196 🟡 · 119 🔴 · **90 tests verdes** · reproducible (semilla fija).

## Quickstart

Requisitos: Python 3.12, Node 18+.

```bash
./run.sh setup     # crea el venv, instala deps de Python y del front
./run.sh demo      # levanta API (:8000) + web (:5173)
```

Abre **http://localhost:5173**. Otros comandos:

```bash
./run.sh test      # corre la suite (90 tests)
./run.sh pipeline  # genera la bandeja + imprime métricas
./run.sh api       # solo la API (docs en /docs)
```

> La API usa la **DB como fuente de verdad** (SQLite local por defecto, auto-sembrado
> con el sintético en el primer arranque — cero fricción). Para Postgres:
> `docker compose up -d` y `DATABASE_URL=postgresql+psycopg2://argly:argly@localhost:5432/argly ./run.sh ...`

### Dataset variable

El dataset es **editable**: desde la vista **Datos** del war-room (o vía API) puedes
**importar un dataset propio** (un CSV por tabla; solo `siniestros` es obligatorio,
el resto se completa con defaults) en modo **reemplazar** o **anexar**, y **restaurar**
el sintético cuando quieras. Tras importar, Argly recalcula features, reglas, ML y la
bandeja. Si el dataset no trae etiquetas de fraude usables, opera en **modo solo-reglas**
(el ML queda fuera hasta que haya casos etiquetados). El scoring en vivo (`/api/scorear`)
sigue siendo efímero: puntúa un caso sin alterar el dataset.

## Enfoque

Score **híbrido** por **contribuciones transparentes**: cada motor devuelve
`{señal, puntos, evidencia}`; una fusión versionada las combina en 0-100 + semáforo.
No es solo suma: hay **hard gates** (reglas críticas RF → ROJO), topes y precedencia.
El desglose ES la lista de contribuciones (explicable por diseño).

- **Reglas** — las 14 señales del reto + RF-01..04 como hard gates (RF-01 PTxRB, RF-02 doc, RF-03 lista, RF-04 dinámica).
- **ML supervisado** — RandomForest (entrenado en train held-out) + **SHAP** (global y local) para explicabilidad.
- **Anomalías** — Isolation Forest para lo "no evidente".
- **Agente de IA** — consultas en lenguaje natural (las 12 preguntas del reto + Pareto 80%); el LLM **planifica** la herramienta determinista y **redacta** con datos reales (DeepSeek/Groq o **Gemini**). Sin LLM, el núcleo sigue funcionando.
- **Redes (grafo)** — networkx detecta anillos + **Pareto** de proveedores que concentran el 80% de las alertas rojas.
- **NLP** — similitud de narrativas (TF-IDF + coseno), extracción de entidades y resumen de narrativas repetidas.
- **Impacto de negocio** — **simulación de ahorro** potencial (monto recuperable + ahorro operativo).
- **Human-in-the-loop** — el analista marca cada caso (confirmado/falso positivo/descartado); su veredicto se persiste y un **reentrenamiento bajo demanda** lo incorpora, mostrando métricas antes/después sobre el test held-out (sin fuga).
- **Cola de trabajo del analista** — bandeja **filtrable y buscable** con **estados de gestión** (sin revisar → en revisión → escalado → cerrado) y **vistas guardadas**; cada caso trae **resumen en lenguaje natural**, **casos vinculados**, **checklist de investigación**, **bitácora** auditable y un tablero **"Mi trabajo"** con productividad, pendientes y novedades.
- **Explicabilidad y ética** — **panel de equidad** (disparate impact / regla 4/5 sobre la tasa de alerta + falsos positivos por ciudad/segmento/canal/ramo) y **explicación contrafactual** ("qué tendría que cambiar para que el caso sea VERDE").

## API

| Endpoint | Devuelve |
|---|---|
| `GET /api/resumen` | totales por semáforo + monto en revisión |
| `GET /api/casos?nivel=&estado=&ramo=&ciudad=&q=&monto_min=&score_min=&orden=` | **bandeja filtrable/buscable** (cola de trabajo) |
| `POST /api/casos/{id}/estado` | **estado de gestión** del caso (sin_revisar/en_revision/escalado/cerrado) |
| `POST /api/casos/{id}/nota` · `GET /api/casos/{id}/bitacora` | **bitácora**: notas + historial de cambios (trazabilidad) |
| `GET`·`POST /api/casos/{id}/checklist` | **checklist de investigación** (pasos por caso + listo para escalar) |
| `GET /api/mi-trabajo` | **tablero del analista**: productividad, pendientes prioritarios y novedades |
| `GET /api/casos/{id}` | score + desglose + evidencia + recomendación + **resumen en lenguaje natural** |
| `GET /api/casos/{id}/vinculos` | **casos vinculados** (mismo proveedor/asegurado/conductor/placa, narrativa similar) |
| `POST /api/scorear` | **puntúa un siniestro nuevo en vivo** + explica (con SHAP local) |
| `GET /api/dataset` | estado del dataset: origen, conteos por tabla y modo (híbrido/solo-reglas) |
| `POST /api/dataset/importar` | **importa un dataset propio** (CSV por tabla; `modo=replace`/`append`) |
| `POST /api/dataset/reset` | restaura el dataset sintético de demo |
| `POST /api/casos/{id}/feedback` | **veredicto del analista** (confirmado/falso_positivo/descartado) |
| `GET /api/feedback` | resumen del feedback acumulado |
| `POST /api/modelo/reentrenar` | **reentrena con el feedback** y devuelve métricas antes/después |
| `GET /api/casos/{id}/contrafactual` | **qué cambiaría para que el caso pase a VERDE** (explicación contrafactual) |
| `GET /api/sesgo` | **análisis de equidad/sesgo** (tasa de alerta y FP por ciudad/segmento/canal/ramo + regla 4/5) |
| `GET /api/mapa` | **mapa de calor** de alertas por ciudad (georreferenciado, sin APIs externas) |
| `GET /api/reporte/pdf` | **reporte ejecutivo consolidado** (PDF) para dirección/auditoría |
| `GET /api/reporte/excel` | **exportación de la bandeja a Excel** multi-hoja (auditoría) |
| `POST /api/preguntar` | agente: respuesta en lenguaje natural |
| `GET /api/redes` | anillos (proveedores que concentran alertas) |
| `GET /api/proveedores-pareto` | **proveedores que concentran el 80% de las alertas rojas** |
| `GET /api/ahorro` | simulación de ahorro potencial (impacto de negocio) |
| `GET /api/modelo/importancias` | explicabilidad global del modelo (SHAP) |
| `GET /api/narrativas-similares` | pares de narrativas casi idénticas |
| `GET /api/narrativas/resumen` | resumen de narrativas repetidas |
| `GET /api/casos/{id}/entidades` | entidades extraídas de la narrativa (NER) |
| `GET /api/casos/{id}/dossier` | PDF de investigación |
| `GET /api/casos/{id}/aviso` | preview de notificación WhatsApp/correo |
| `POST /api/casos/{id}/push` | push del score al core (mock) |

## Estructura

```text
argly/
├── src/
│   ├── ingestion/   # generador sintético + modelos SQLAlchemy + seed   (E0)
│   ├── features/    # ingeniería de variables de riesgo                 (E1)
│   ├── rules/       # motor de reglas (rúbrica + RF gates)              (E1)
│   ├── scoring/     # fusión -> score 0-100 + semáforo                  (E1)
│   ├── models/      # ML supervisado (RandomForest)                     (E2)
│   ├── anomaly/     # Isolation Forest                                  (E2)
│   ├── app/         # API FastAPI                                       (E3)
│   ├── pipeline.py  # datos -> features -> score -> bandeja + métricas
│   ├── graph/       # redes/anillos (networkx)                       (E4)
│   ├── nlp/         # similitud de narrativas (TF-IDF + coseno)       (E4)
│   ├── ai_agent/    # agente NL (planifica tools) + herramientas        (E5)
│   ├── channels/    # PDF dossier + avisos WhatsApp/correo            (E6)
├── frontend/        # React (Vite) war-room                            (E3)
├── notebooks/       # 01 exploración · 02 modelo · 03 evaluación
├── docs/            # arquitectura, modelo de datos, reglas, uso IA, límites, requerimientos
├── presentation/    # pitch (argly.html + argly.pdf)
├── tests/           # 90 tests
└── docker-compose.yml
```

## Datos y ética

Datos **100% sintéticos**, sin PII real. El ML rankea dentro de escenarios
sintéticos (test held-out con patrones no vistos), no prueba generalización al
mundo real. Ver [`docs/limitaciones.md`](docs/limitaciones.md).

## Equipo

hackIAthon 2026.

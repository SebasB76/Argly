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

**Métricas (test held-out, 422 casos):** AUC solo-reglas 0.82 → **híbrido 0.90** (modelo ML 0.93) · **precisión 0.92** · recall 0.74 · F1 0.82.
**Distribución:** 1131 🟢 · 164 🟡 · 97 🔴 · **64 tests verdes** · reproducible (semilla fija).

## Quickstart

Requisitos: Python 3.12, Node 18+.

```bash
./run.sh setup     # crea el venv, instala deps de Python y del front
./run.sh demo      # levanta API (:8000) + web (:5173)
```

Abre **http://localhost:5173**. Otros comandos:

```bash
./run.sh test      # corre la suite (64 tests)
./run.sh pipeline  # genera la bandeja + imprime métricas
./run.sh api       # solo la API (docs en /docs)
```

> Postgres es opcional para el demo (la API arma la bandeja en memoria). Para
> persistencia real: `docker compose up -d` y `DATABASE_URL=postgresql+psycopg2://argly:argly@localhost:5432/argly ./run.sh ...`

## Enfoque

Score **híbrido** por **contribuciones transparentes**: cada motor devuelve
`{señal, puntos, evidencia}`; una fusión versionada las combina en 0-100 + semáforo.
No es solo suma: hay **hard gates** (reglas críticas RF → ROJO), topes y precedencia.
El desglose ES la lista de contribuciones (explicable por diseño).

- **Reglas** — rúbrica de señales del reto + RF-02/03/04 como gates.
- **ML supervisado** — RandomForest (entrenado en train held-out).
- **Anomalías** — Isolation Forest para lo "no evidente".
- **Agente de IA** — consultas en lenguaje natural (las 12 preguntas del reto); herramientas deterministas + LLM barato compatible-OpenAI (DeepSeek/Groq) opcional, con fallback.
- **Redes (grafo)** — networkx detecta anillos (proveedores que concentran alertas).
- **NLP** — similitud de narrativas (TF-IDF + coseno) para detectar clonadas.

## API

| Endpoint | Devuelve |
|---|---|
| `GET /api/resumen` | totales por semáforo + monto en revisión |
| `GET /api/casos?nivel=&limit=` | bandeja priorizada |
| `GET /api/casos/{id}` | score + desglose + evidencia + recomendación |
| `POST /api/preguntar` | agente: respuesta en lenguaje natural |
| `GET /api/redes` | anillos (proveedores que concentran alertas) |
| `GET /api/narrativas-similares` | pares de narrativas casi idénticas |
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
│   ├── ai_agent/    # agente NL + herramientas deterministas          (E5)
│   ├── channels/    # PDF dossier + avisos WhatsApp/correo            (E6)
├── frontend/        # React (Vite) war-room                            (E3)
├── docs/            # arquitectura, modelo de datos, reglas, uso IA, límites, requerimientos
├── tests/           # 64 tests
└── docker-compose.yml
```

## Datos y ética

Datos **100% sintéticos**, sin PII real. El ML rankea dentro de escenarios
sintéticos (test held-out con patrones no vistos), no prueba generalización al
mundo real. Ver [`docs/limitaciones.md`](docs/limitaciones.md).

## Equipo

hackIAthon 2026.

# Argly — Detector de posible fraude en siniestros

Prototipo de Inteligencia Artificial para el **hackIAthon 2026 · Reto Aseguradora del Sur**.

Argly analiza siniestros de seguros, asigna un **score de riesgo (0-100)** con
semáforo 🟢 🟡 🔴 y genera **alertas explicables** que priorizan los casos para
revisión humana.

> ⚠️ Argly genera **alertas de revisión, no acusaciones de fraude**. No rechaza
> siniestros ni decide pagos. La decisión final siempre es de un analista humano.

## Enfoque

Sistema **híbrido** que combina:

- **Reglas de negocio** — la rúbrica de señales del reto (puntaje trazable).
- **Machine Learning** — clasificación de riesgo + explicabilidad (SHAP).
- **Detección de anomalías** — casos fuera del comportamiento esperado.
- **Análisis de redes (grafo)** — detección de anillos y colusión entre actores.
- **NLP** — similitud de narrativas y coherencia relato vs. siniestro.
- **Agente de IA** — consultas en lenguaje natural sobre casos, proveedores y patrones.

## Estructura del repositorio

```text
argly/
├── data/
│   ├── raw/            # datos crudos (no se versionan)
│   ├── processed/      # datos procesados
│   └── synthetic/      # datasets sintéticos generados
├── notebooks/          # exploración, modelado y evaluación
├── src/
│   ├── ingestion/      # carga y validación de datos
│   ├── features/       # ingeniería de variables de riesgo
│   ├── rules/          # motor de reglas (rúbrica del reto)
│   ├── scoring/        # fusión de motores -> score 0-100 + semáforo
│   ├── models/         # modelo ML supervisado
│   ├── anomaly/        # detección de anomalías
│   ├── graph/          # red de entidades y detección de anillos
│   ├── nlp/            # similitud de narrativas y coherencia
│   ├── explainability/ # descomposición y explicación del score
│   ├── ai_agent/       # agente de IA (consultas en lenguaje natural)
│   ├── enrichment/     # fuentes externas (mapas, clima, placa/RUC)
│   ├── channels/       # notificaciones (WhatsApp, correo, voz, PDF)
│   └── app/            # API / interfaz
├── docs/               # arquitectura, modelo de datos, reglas, uso de IA, límites
├── tests/              # pruebas
└── presentation/       # pitch
```

## Stack

Python · FastAPI · pandas · scikit-learn · XGBoost · networkx ·
sentence-transformers · SHAP · Claude/GPT (agente) · PostgreSQL (Oracle a futuro).

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar las llaves necesarias
```

## Uso

_En construcción._ El diseño completo está en [`docs/arquitectura.md`](docs/arquitectura.md).

## Roadmap

- [ ] **F0** Datos sintéticos con patrones plantados + esquema
- [ ] **F1** Features + reglas + score + bandeja priorizada
- [ ] **F2** ML + anomalías + SHAP
- [ ] **F3** Grafo + detección de redes
- [ ] **F4** NLP (similitud, coherencia)
- [ ] **F5** Agente + consultas en lenguaje natural
- [ ] **F6** Enriquecimiento (Maps, clima, placa/RUC)
- [ ] **F7** Canales (WhatsApp, correo, voz, PDF) + API
- [ ] **F8** Ética / documentación / pulido visual

## Datos y ética

Datos **100% sintéticos**, sin información personal real. Ver
[`docs/limitaciones.md`](docs/limitaciones.md).

## Equipo

hackIAthon 2026.

# Uso de Inteligencia Artificial — Argly

> Basado en la sección 9 del reto.

Argly usa un **enfoque híbrido**: ninguna técnica decide sola; se combinan y el
resultado se explica.

| Enfoque | Aplicación |
|---|---|
| ML supervisado | Probabilidad de posible fraude (**RandomForest** sobre etiqueta simulada, entrenado solo con `split=train`). |
| Detección de anomalías | Casos fuera del comportamiento esperado (Isolation Forest). |
| NLP | Similitud de narrativas (TF-IDF + coseno), **extracción de entidades** (NER por reglas: placas, montos, vías, expedientes) y **resumen** de narrativas repetidas. |
| Análisis de redes | Anillos y colusión entre asegurados y proveedores (networkx) + **Pareto** de proveedores que concentran el 80% de las alertas rojas. |
| Agente de IA | Consultas en lenguaje natural; el LLM **planifica** la herramienta y **redacta** con los datos reales (DeepSeek/Groq o Gemini). |

## Explicabilidad

- Desglose del score por regla (la lista de contribuciones ES la explicación).
- Parte ML explicada con **SHAP** (TreeExplainer): importancia **global** del modelo
  y **local** por instancia (`GET /api/modelo/importancias` y `factores_modelo` en
  el scoreo en vivo). Si SHAP no está instalado, cae a la importancia del RandomForest.
- El agente redacta una justificación citando la evidencia (trazabilidad).

## Impacto de negocio

- **Simulación de ahorro** (`GET /api/ahorro`): estima el monto expuesto en casos
  rojos recuperable tras revisión + ahorro operativo de priorizar. Cifra referencial.

## Métricas

- Supervisado: precision, recall, F1, matriz de confusión, AUC-ROC.
- Anomalías: % de casos marcados, ranking de rareza, validación con reglas.
- NLP: calidad de extracción, similitud, coherencia de resúmenes.

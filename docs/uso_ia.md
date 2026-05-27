# Uso de Inteligencia Artificial — Argly

> Stub. Se completa a lo largo de las fases F2-F5. Basado en la sección 9 del reto.

Argly usa un **enfoque híbrido**: ninguna técnica decide sola; se combinan y el
resultado se explica.

| Enfoque | Aplicación |
|---|---|
| ML supervisado | Probabilidad de posible fraude (XGBoost sobre etiqueta simulada). |
| Detección de anomalías | Casos fuera del comportamiento esperado (Isolation Forest). |
| NLP | Similitud de narrativas (embeddings), extracción de entidades, coherencia. |
| Análisis de redes | Anillos y colusión entre asegurados, proveedores y vehículos. |
| Agente de IA | Consultas en lenguaje natural; investigación multipaso con herramientas. |

## Explicabilidad

- Desglose del score por regla y por variable (SHAP para la parte ML).
- El agente redacta una justificación citando la evidencia (trazabilidad).

## Métricas

- Supervisado: precision, recall, F1, matriz de confusión, AUC-ROC.
- Anomalías: % de casos marcados, ranking de rareza, validación con reglas.
- NLP: calidad de extracción, similitud, coherencia de resúmenes.

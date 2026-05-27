"""Modelo ML supervisado (E2): RandomForest sobre las features.

Se entrena SOLO con el split=train. Las redes (rings) del test usan proveedores
distintos a los del train, así que el modelo se evalúa sobre variantes no vistas
(evita métricas circulares). No se usa el id de proveedor como feature, solo el
flag genérico `proveedor_en_lista`, que sí generaliza.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

FEATURES = [
    "dias_desde_inicio_poliza", "dias_entre_ocurrencia_reporte", "historial_siniestros_asegurado",
    "es_robo", "ratio_monto_suma", "proveedor_en_lista", "asegurado_en_lista",
    "freq_proveedor", "freq_vehiculo", "distancia_geo_km", "clima_inconsistente",
    "documentos_completos", "doc_inconsistente", "doc_no_entregado", "narrativa_repetidos",
]


def _X(F) -> pd.DataFrame:
    X = F[FEATURES].copy()
    for c in X.columns:
        if X[c].dtype == bool:
            X[c] = X[c].astype(int)
    return X


def entrenar(F):
    """Entrena con split=train. Devuelve (modelo, prob) donde prob es la
    probabilidad de fraude para TODAS las filas (Series alineada a F.index)."""
    X = _X(F)
    y = F["etiqueta_fraude_simulada"].astype(int)
    tr = (F["split"] == "train").values
    modelo = RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=42,
        class_weight="balanced", n_jobs=-1,
    )
    modelo.fit(X[tr], y[tr])
    prob = pd.Series(modelo.predict_proba(X)[:, 1], index=F.index)
    return modelo, prob


def importancias(modelo) -> dict:
    """Importancia global de cada feature (proxy de explicabilidad del modelo)."""
    pares = sorted(zip(FEATURES, modelo.feature_importances_), key=lambda kv: kv[1], reverse=True)
    return {k: round(float(v), 3) for k, v in pares}

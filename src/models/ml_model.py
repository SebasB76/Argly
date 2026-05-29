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
    "freq_proveedor", "freq_vehiculo", "freq_conductor", "freq_solo_rc",
    "distancia_geo_km", "clima_inconsistente", "evento_sin_tercero", "es_ptxrb",
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


def _shap_matriz(modelo, X):
    """Devuelve la matriz SHAP de la clase positiva (n, n_features) o None si shap no está."""
    try:
        import numpy as np
        import shap

        sv = shap.TreeExplainer(modelo).shap_values(X)
        arr = np.asarray(sv[1] if isinstance(sv, list) else sv)
        if arr.ndim == 3:                       # (n, features, clases) -> clase positiva
            arr = arr[:, :, -1]
        if arr.shape[1] != len(FEATURES) and arr.shape[0] == len(FEATURES):
            arr = arr.T
        return arr
    except Exception:
        return None


def explicacion_global(modelo, F=None) -> dict:
    """Explicabilidad GLOBAL del modelo. Usa SHAP (|valor| medio) si está instalado;
    si no, cae a feature_importances_ del RandomForest (siempre disponible)."""
    if F is not None:
        import numpy as np

        X = _X(F)
        tr = (F["split"] == "train").values
        M = _shap_matriz(modelo, X[tr][:500])
        if M is not None:
            vals = np.abs(M).mean(axis=0)
            pares = sorted(zip(FEATURES, vals), key=lambda kv: kv[1], reverse=True)
            return {"metodo": "shap", "importancias": {k: round(float(v), 4) for k, v in pares}}
    return {"metodo": "feature_importances", "importancias": importancias(modelo)}


def explicacion_local(modelo, fila: dict, top: int = 6) -> dict:
    """Explicabilidad LOCAL de UNA instancia: qué features empujan su riesgo.

    SHAP local si está disponible (firma por instancia); si no, cae a
    importancia_global * valor_de_la_feature como aproximación transparente.
    """
    import pandas as pd

    X = _X(pd.DataFrame([{k: fila.get(k) for k in FEATURES}]))
    M = _shap_matriz(modelo, X)
    if M is not None:
        pares = sorted(zip(FEATURES, M[0], X.iloc[0].values), key=lambda t: abs(t[1]), reverse=True)
        return {"metodo": "shap", "factores": [
            {"feature": k, "impacto": round(float(v), 4), "valor": round(float(val), 3)}
            for k, v, val in pares[:top]]}
    imp = dict(zip(FEATURES, modelo.feature_importances_))
    pares = sorted(zip(FEATURES, X.iloc[0].values), key=lambda t: imp[t[0]] * abs(t[1]), reverse=True)
    return {"metodo": "feature_importances", "factores": [
        {"feature": k, "impacto": round(float(imp[k]), 4), "valor": round(float(val), 3)}
        for k, val in pares[:top]]}

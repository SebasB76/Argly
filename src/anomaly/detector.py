"""Detección de anomalías (E2): Isolation Forest no supervisado.

Captura siniestros 'no evidentes' (fuera del comportamiento esperado) que las
reglas y el modelo supervisado podrían no marcar.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from src.models.ml_model import FEATURES, _X


def detectar(F) -> pd.Series:
    """Devuelve un score de rareza normalizado 0-1 (1 = más anómalo)."""
    X = _X(F)
    tr = (F["split"] == "train").values
    iso = IsolationForest(n_estimators=200, contamination=0.2, random_state=42)
    iso.fit(X[tr])
    raw = -iso.score_samples(X)            # mayor = más anómalo
    lo, hi = raw.min(), raw.max()
    norm = (raw - lo) / (hi - lo) if hi > lo else raw * 0.0
    return pd.Series(norm, index=F.index)

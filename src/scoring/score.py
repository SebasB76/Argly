"""Fusión de contribuciones a score 0-100 + semáforo (E1).

Política de scoring versionada (v1):
1. Hard gates (RF-01..04) -> nivel ROJO con precedencia sobre la suma.
2. Suma de las contribuciones.
3. Tope total a 100.
4. Semáforo por umbrales (ver src/config.py).

El desglose es exactamente la lista de contribuciones (explicable por diseño).
"""
from __future__ import annotations

from dataclasses import asdict

from src import config
from src.rules.fraud_rules import Contribucion, evaluar_reglas

VERSION = "v1"


def puntuar(contribuciones: list[Contribucion]) -> dict:
    total = sum(c.puntos for c in contribuciones)
    score = min(int(total), 100)            # tope 100
    hay_gate = any(c.gate for c in contribuciones)
    if hay_gate:                            # precedencia: el gate fuerza ROJO
        score = max(score, 76)
        nivel = "ROJO"
    else:
        nivel = config.clasificar_riesgo(score)
    return {
        "score": score,
        "nivel": nivel,
        "gate": hay_gate,
        "version": VERSION,
        "contribuciones": [asdict(c) for c in contribuciones],
    }


def puntuar_siniestro(row) -> dict:
    return puntuar(evaluar_reglas(row))


def contribucion_ml(prob: float):
    """Contribución del modelo ML (no es gate; aporta puntos según la probabilidad)."""
    if prob >= 0.40:
        return Contribucion("Modelo ML", int(round(prob * 50)),
                            f"Probabilidad de fraude del modelo: {prob:.0%}")
    return None


def contribucion_anomalia(anom: float):
    """Contribución por anomalía (Isolation Forest); captura lo 'no evidente'."""
    if anom >= 0.65:
        return Contribucion("Anomalía", int(round((anom - 0.5) * 30)),
                            f"Comportamiento atípico (rareza {anom:.0%})")
    return None


def puntuar_features(F, prob=None, anom=None):
    """Puntúa un DataFrame de features.

    Con prob/anom (Series alineadas a F) suma las contribuciones de ML y anomalía
    (modo híbrido); sin ellas, es scoring solo-reglas (E1).
    """
    import pandas as pd

    res = []
    for i, (_, row) in enumerate(F.iterrows()):
        contribs = evaluar_reglas(row)
        if prob is not None:
            c = contribucion_ml(float(prob.iloc[i]))
            if c:
                contribs.append(c)
        if anom is not None:
            c = contribucion_anomalia(float(anom.iloc[i]))
            if c:
                contribs.append(c)
        res.append(puntuar(contribs))
    data = {
        "id_siniestro": F["id_siniestro"].values,
        "score": [x["score"] for x in res],
        "nivel": [x["nivel"] for x in res],
        "gate": [x["gate"] for x in res],
        "contribuciones": [x["contribuciones"] for x in res],
    }
    if prob is not None:
        data["probabilidad_ml"] = [round(float(x), 3) for x in prob.values]
    if anom is not None:
        data["rareza_anomalia"] = [round(float(x), 3) for x in anom.values]
    return pd.DataFrame(data)

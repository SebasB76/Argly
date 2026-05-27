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


def puntuar_features(F):
    """Puntúa un DataFrame de features. Devuelve id_siniestro, score, nivel, gate, contribuciones."""
    import pandas as pd

    res = [puntuar_siniestro(r) for _, r in F.iterrows()]
    return pd.DataFrame({
        "id_siniestro": F["id_siniestro"].values,
        "score": [x["score"] for x in res],
        "nivel": [x["nivel"] for x in res],
        "gate": [x["gate"] for x in res],
        "contribuciones": [x["contribuciones"] for x in res],
    })

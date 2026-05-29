"""Mapa de calor geográfico: concentración de alertas por ciudad.

Responde la pregunta del reto "¿Qué ciudades presentan mayor concentración de
alertas?" de forma visual. Agrega la bandeja por ciudad (sucursal) y le adjunta
las coordenadas conocidas (`config.CIUDADES`) para pintarlas en el front.

100% offline: las coordenadas están precomputadas, sin APIs de mapas externas
(cumple "tener una alternativa de demo" del documento del reto).
"""
from __future__ import annotations

import pandas as pd

from src import config


def mapa_calor(bandeja: pd.DataFrame) -> dict:
    """Agrega alertas por ciudad y adjunta coordenadas para el mapa de calor."""
    ciudades = []
    for ciudad, sub in bandeja.groupby("sucursal"):
        n = int(len(sub))
        rojos = int((sub["nivel"] == "ROJO").sum())
        amarillos = int((sub["nivel"] == "AMARILLO").sum())
        verdes = int((sub["nivel"] == "VERDE").sum())
        alertas = rojos + amarillos
        coords = config.CIUDADES.get(str(ciudad))
        ciudades.append({
            "ciudad": str(ciudad),
            "n": n, "rojos": rojos, "amarillos": amarillos, "verdes": verdes,
            "alertas": alertas,
            "tasa_alerta": round(alertas / n, 3) if n else 0.0,
            "monto_revision": round(float(sub.loc[sub["nivel"] != "VERDE", "monto_reclamado"].sum()), 2),
            "lat": coords[0] if coords else None,
            "lng": coords[1] if coords else None,
        })
    ciudades.sort(key=lambda c: (c["alertas"], c["rojos"]), reverse=True)

    lats = [v[0] for v in config.CIUDADES.values()]
    lngs = [v[1] for v in config.CIUDADES.values()]
    return {
        "ciudades": ciudades,
        "con_coordenadas": sum(1 for c in ciudades if c["lat"] is not None),
        "sin_coordenadas": [c["ciudad"] for c in ciudades if c["lat"] is None],
        "bbox": {"lat_min": min(lats), "lat_max": max(lats),
                 "lng_min": min(lngs), "lng_max": max(lngs)},
        "max_alertas": max((c["alertas"] for c in ciudades), default=0),
        "max_rojos": max((c["rojos"] for c in ciudades), default=0),
        "total": int(len(bandeja)),
    }

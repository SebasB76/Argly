"""Ingeniería de variables de riesgo (E1).

Consume las tablas y produce un DataFrame de features por siniestro, que el
motor de reglas (`src/rules`) usará para calcular contribuciones al score.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src import config


def _dist_km(c1: str, c2: str) -> float:
    """Distancia aproximada (km) entre dos ciudades; 0 si es la misma o desconocida."""
    if c1 == c2 or c1 not in config.CIUDADES or c2 not in config.CIUDADES:
        return 0.0
    (la1, lo1), (la2, lo2) = config.CIUDADES[c1], config.CIUDADES[c2]
    r = 6371.0
    dla, dlo = math.radians(la2 - la1), math.radians(lo2 - lo1)
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.sin(dlo / 2) ** 2)
    return round(2 * r * math.asin(math.sqrt(h)), 1)


def construir_features(dfs: dict) -> pd.DataFrame:
    """Devuelve un DataFrame (una fila por siniestro) con las variables de riesgo."""
    s = dfs["siniestros"].reset_index(drop=True)
    pol = dfs["polizas"].set_index("id_poliza")
    prov = dfs["proveedores"].set_index("id_proveedor")
    aseg = dfs["asegurados"].set_index("id_asegurado")
    docs = dfs["documentos"]

    f = pd.DataFrame()
    f["id_siniestro"] = s["id_siniestro"]
    f["ramo"] = s["ramo"]
    f["cobertura"] = s["cobertura"]

    # --- Provistos por la ingesta ---
    f["dias_desde_inicio_poliza"] = s["dias_desde_inicio_poliza"]
    f["dias_entre_ocurrencia_reporte"] = s["dias_entre_ocurrencia_reporte"]
    f["historial_siniestros_asegurado"] = s["historial_siniestros_asegurado"]
    f["es_robo"] = s["cobertura"].eq("Robo")

    # --- Monto vs suma asegurada ---
    suma = s["id_poliza"].map(pol["suma_asegurada"]).astype(float)
    f["ratio_monto_suma"] = np.where(suma > 0, s["monto_reclamado"] / suma, 0.0).round(3)

    # --- Listas restrictivas ---
    f["proveedor_en_lista"] = s["id_proveedor"].map(prov["en_lista_restrictiva"]).fillna(False).astype(bool)
    f["asegurado_en_lista"] = s["id_asegurado"].map(aseg["en_lista_restrictiva"]).fillna(False).astype(bool)

    # --- Frecuencias (proveedor recurrente / vehículo repetido) ---
    f["freq_proveedor"] = s.groupby("id_proveedor")["id_siniestro"].transform("count")
    veh = s.loc[s["placa"] != "", "placa"].value_counts()
    f["freq_vehiculo"] = s["placa"].map(lambda p: int(veh.get(p, 0)) if p else 0)

    # --- Frecuencia por conductor (mismo conductor en varios siniestros) ---
    if "id_conductor" in s.columns:
        f["freq_conductor"] = s.groupby("id_conductor")["id_siniestro"].transform("count").fillna(0).astype(int)
    else:
        f["freq_conductor"] = 0

    # --- Frecuencia de reclamos SOLO RC (Responsabilidad Civil) por asegurado ---
    f["es_solo_rc"] = s["cobertura"].eq("Daño a Terceros (RC)")
    f["freq_solo_rc"] = (f["es_solo_rc"].astype(int)
                         .groupby(s["id_asegurado"]).transform("sum").astype(int))

    # --- Evento sin tercero identificado ---
    if "tercero_identificado" in s.columns:
        f["evento_sin_tercero"] = ~s["tercero_identificado"].fillna(True).astype(bool)
    else:
        f["evento_sin_tercero"] = False

    # --- Pérdida Total por Robo (PTxRB): pérdida total + cobertura de robo (RF-01) ---
    perdida = s["perdida_total"].fillna(False).astype(bool) if "perdida_total" in s.columns else False
    f["es_ptxrb"] = perdida & s["cobertura"].isin(["Robo", "Pérdida Total"])

    # --- Geografía y clima (precomputados en los datos) ---
    f["distancia_geo_km"] = [_dist_km(a, b) for a, b in zip(s["ciudad_ocurrencia"], s["ciudad_taller"])]
    f["clima_inconsistente"] = s["clima_declarado"].ne(s["clima_real"])

    # --- Documentos ---
    f["documentos_completos"] = s["documentos_completos"].astype(bool)
    docagg = docs.groupby("id_siniestro").agg(
        doc_inconsistente=("inconsistencia_detectada", "max"),
        doc_no_entregado=("entregado", lambda x: bool((~x.astype(bool)).any())),
    )
    f = f.merge(docagg, on="id_siniestro", how="left")
    f["doc_inconsistente"] = f["doc_inconsistente"].fillna(False).astype(bool)
    f["doc_no_entregado"] = f["doc_no_entregado"].fillna(False).astype(bool)

    # --- Narrativa repetida (conteo exacto; la similitud semántica llega en E4) ---
    f["narrativa_repetidos"] = s.groupby("descripcion")["id_siniestro"].transform("count")

    # --- Etiqueta y split para evaluación aguas abajo ---
    f["etiqueta_fraude_simulada"] = s["etiqueta_fraude_simulada"]
    f["split"] = s["split"]
    return f

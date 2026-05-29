"""Análisis de sesgo / equidad (Explicabilidad y Ética).

Responde a la exigencia del reto: "documenta riesgos, sesgos y garantiza que la
IA sea solo una alerta" + "Sesgo en datos -> análisis de sesgo". Mide si Argly
sobre-alerta sistemáticamente a algún grupo (ciudad, segmento, canal, ramo).

Métricas por grupo:
- tasa_alerta: proporción de casos marcados (no VERDE) dentro del grupo.
- tasa_falsos_positivos (FPR): entre los NO fraude (etiqueta=0), proporción marcada.
  Requiere etiquetas; si no hay, se omite.

Veredicto de paridad: regla de los 4/5 (disparate impact). El cociente entre la
tasa mínima y la máxima entre grupos (con tamaño suficiente) debe ser >= 0.8;
por debajo se marca para revisión. NO es una conclusión, es una alerta de equidad.
"""
from __future__ import annotations

import pandas as pd

REGLA_45 = 0.8           # umbral de la regla de los 4/5 (disparate impact)
MIN_GRUPO = 20           # tamaño mínimo de grupo para entrar al veredicto (evita ruido)


def _enriquecer(bandeja: pd.DataFrame, dfs: dict) -> pd.DataFrame:
    """Agrega al tablero los atributos sensibles (ciudad, segmento, canal)."""
    b = bandeja.copy()
    b["ciudad"] = b.get("sucursal", "—").fillna("—")
    aseg = dfs["asegurados"].set_index("id_asegurado") if not dfs["asegurados"].empty else None
    b["segmento"] = (b["id_asegurado"].map(aseg["segmento"]) if aseg is not None and "segmento" in aseg.columns else "—")
    sin = dfs["siniestros"].set_index("id_siniestro")
    id_pol = b["id_siniestro"].map(sin["id_poliza"]) if "id_poliza" in sin.columns else None
    pol = dfs["polizas"].set_index("id_poliza") if not dfs["polizas"].empty else None
    b["canal_venta"] = (id_pol.map(pol["canal_venta"]) if id_pol is not None and pol is not None and "canal_venta" in pol.columns else "—")
    for c in ("ciudad", "segmento", "canal_venta"):
        b[c] = b[c].fillna("—").replace("", "—")
    return b


def _stats_atributo(b: pd.DataFrame, attr: str, hay_etiquetas: bool) -> dict:
    grupos = []
    for g, sub in b.groupby(attr):
        n = int(len(sub))
        tasa_alerta = round(float((sub["nivel"] != "VERDE").mean()), 3)
        fpr = None
        if hay_etiquetas:
            no_fraude = sub[sub["etiqueta_fraude_simulada"].astype(int) == 0]
            if len(no_fraude):
                fpr = round(float((no_fraude["nivel"] != "VERDE").mean()), 3)
        grupos.append({"grupo": str(g), "n": n, "tasa_alerta": tasa_alerta,
                       "tasa_falsos_positivos": fpr})
    grupos.sort(key=lambda x: x["tasa_alerta"], reverse=True)

    # Disparate impact (regla 4/5) sobre la TASA DE ALERTA (tasa de selección): es la
    # definición estándar y robusta. El FPR se reporta por grupo como contexto ético
    # adicional (no se usa para el cociente: un FPR bajo es deseable, no una disparidad).
    elegibles = [x for x in grupos if x["n"] >= MIN_GRUPO]
    disparidad = veredicto = peor = None
    if len(elegibles) >= 2:
        vals = [x["tasa_alerta"] for x in elegibles]
        mx, mn = max(vals), min(vals)
        disparidad = round(mn / mx, 3) if mx > 0 else 1.0
        veredicto = "equitativo" if disparidad >= REGLA_45 else "revisar"
        peor = max(elegibles, key=lambda x: x["tasa_alerta"])["grupo"]
    return {"grupos": grupos, "metrica_disparidad": "tasa_alerta",
            "disparidad": disparidad, "veredicto": veredicto, "grupo_mas_alertado": peor}


def analizar_sesgo(bandeja: pd.DataFrame, dfs: dict,
                   atributos: tuple[str, ...] = ("ciudad", "segmento", "canal_venta", "ramo")) -> dict:
    """Análisis de equidad por cada atributo sensible. Devuelve métricas + veredicto."""
    b = _enriquecer(bandeja, dfs)
    y = b["etiqueta_fraude_simulada"].astype("Int64") if "etiqueta_fraude_simulada" in b.columns else None
    hay_etiquetas = y is not None and y.fillna(0).nunique() >= 2
    salida = {}
    for attr in atributos:
        if attr in b.columns:
            salida[attr] = _stats_atributo(b, attr, hay_etiquetas)
    revisar = [a for a, v in salida.items() if v["veredicto"] == "revisar"]
    return {
        "atributos": salida,
        "hay_etiquetas": bool(hay_etiquetas),
        "regla": "4/5 (disparate impact): cociente min/max de la métrica debe ser >= 0.8",
        "atributos_a_revisar": revisar,
        "nota": ("Sin etiquetas de fraude se usa la tasa de alerta (no se puede medir el "
                 "falso positivo). El veredicto es una alerta de equidad para revisión humana, "
                 "no una conclusión de discriminación."),
    }

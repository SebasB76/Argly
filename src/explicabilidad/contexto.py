"""Contexto del caso para el analista: resumen en lenguaje natural + casos vinculados.

- `redactar`: arma un párrafo legible (determinista, sin LLM) que cuenta la
  historia del caso: qué es, por qué saltó, con qué se conecta y qué hacer.
- `vinculos_caso`: encuentra otros siniestros relacionados (mismo proveedor,
  asegurado, conductor, placa o narrativa casi idéntica) para investigar el
  caso sin saltar entre pantallas.
"""
from __future__ import annotations

import pandas as pd

from src.nlp.narrative import similares_a

_COLS = ["id_siniestro", "score", "nivel", "monto_reclamado", "motivo_principal"]


def _fila(b: pd.DataFrame, sid: str):
    f = b[b["id_siniestro"] == sid]
    return f.iloc[0] if len(f) else None


def contexto_caso(sid: str, bandeja: pd.DataFrame) -> dict:
    """Conteos baratos (para el resumen): recurrencia de proveedor y asegurado."""
    r = _fila(bandeja, sid)
    if r is None:
        return {}
    bp = bandeja[bandeja["id_proveedor"] == r["id_proveedor"]]
    ba = bandeja[bandeja["id_asegurado"] == r["id_asegurado"]]
    return {
        "proveedor": str(r["id_proveedor"]), "n_proveedor": int(len(bp)),
        "n_proveedor_rojos": int((bp["nivel"] == "ROJO").sum()),
        "asegurado": str(r["id_asegurado"]), "n_asegurado": int(len(ba)),
        "n_asegurado_rojos": int((ba["nivel"] == "ROJO").sum()),
    }


def redactar(d: dict, ctx: dict) -> str:
    """Párrafo en lenguaje natural que resume el caso para el analista."""
    monto = f"${d['monto_reclamado']:,.0f}"
    partes = [f"{d['cobertura']} de {d['ramo'].lower()} en {d['sucursal']} por {monto}.",
              f"Score {d['score']}/100 ({d['nivel']})" + (" por regla crítica (gate)." if d.get("gate") else ".")]

    # Señales principales (usa la evidencia, ya legible)
    contribs = sorted(d.get("contribuciones", []), key=lambda c: c["puntos"], reverse=True)
    evid = [c["evidencia"] for c in contribs if c.get("evidencia")][:3]
    if evid:
        partes.append("Señales: " + "; ".join(evid) + ".")

    # Recurrencia (casos vinculados)
    rec = []
    if ctx.get("n_proveedor", 0) > 1:
        rec.append(f"el proveedor {ctx['proveedor']} aparece en {ctx['n_proveedor']} siniestros"
                   + (f" ({ctx['n_proveedor_rojos']} rojos)" if ctx['n_proveedor_rojos'] else ""))
    if ctx.get("n_asegurado", 0) > 1:
        rec.append(f"el asegurado acumula {ctx['n_asegurado']} reclamos")
    if rec:
        partes.append("Contexto: " + "; ".join(rec) + ".")

    partes.append(f"Recomendación: {d['recomendacion'].lower()}.")
    return " ".join(partes)


def vinculos_caso(sid: str, bandeja: pd.DataFrame, dfs: dict, maximo: int = 6) -> dict:
    """Otros siniestros relacionados con `sid`, agrupados por tipo de vínculo."""
    r = _fila(bandeja, sid)
    if r is None:
        return {}
    sin = dfs["siniestros"]
    srow = sin[sin["id_siniestro"] == sid]
    placa = str(srow.iloc[0]["placa"]) if len(srow) and "placa" in srow.columns else ""
    cond = str(srow.iloc[0]["id_conductor"]) if len(srow) and "id_conductor" in srow.columns else ""

    def _por(col_bandeja, valor):
        if not valor:
            return []
        sub = bandeja[(bandeja[col_bandeja] == valor) & (bandeja["id_siniestro"] != sid)]
        sub = sub.sort_values("score", ascending=False).head(maximo)
        return [_item(x) for _, x in sub.iterrows()]

    # vínculos por placa/conductor: del set de siniestros con ese atributo, traídos a la bandeja
    def _por_siniestro(col, valor):
        if not valor or col not in sin.columns:
            return []
        ids = set(sin.loc[sin[col] == valor, "id_siniestro"]) - {sid}
        sub = bandeja[bandeja["id_siniestro"].isin(ids)].sort_values("score", ascending=False).head(maximo)
        return [_item(x) for _, x in sub.iterrows()]

    # narrativa similar
    nar = []
    for m in similares_a(sin, sid, umbral=0.8, top=maximo):
        it = _fila(bandeja, m["id_siniestro"])
        if it is not None:
            nar.append({**_item(it), "similitud": m["similitud"]})

    return {
        "mismo_proveedor": _por("id_proveedor", str(r["id_proveedor"])),
        "mismo_asegurado": _por("id_asegurado", str(r["id_asegurado"])),
        "mismo_conductor": _por_siniestro("id_conductor", cond),
        "misma_placa": _por_siniestro("placa", placa),
        "narrativa_similar": nar,
    }


def _item(x) -> dict:
    return {"id_siniestro": str(x["id_siniestro"]), "score": int(x["score"]),
            "nivel": str(x["nivel"]), "monto_reclamado": float(x["monto_reclamado"]),
            "motivo_principal": str(x["motivo_principal"])}

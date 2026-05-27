"""Herramientas deterministas del agente (E5).

El agente (con o sin LLM) SIEMPRE obtiene los números de aquí, nunca los inventa.
Cada herramienta opera sobre la bandeja (DataFrame de src.pipeline.construir_bandeja)
y devuelve datos en tipos nativos (JSON-safe).
"""
from __future__ import annotations


def _tiene(contribs, nombre: str) -> bool:
    return any(nombre.lower() in c["regla"].lower() for c in (contribs or []))


def _flagged(b):
    return b[b["nivel"] != "VERDE"]


def top_riesgo(b, n: int = 10):
    out = []
    for _, r in b.head(n).iterrows():
        out.append({"id_siniestro": r["id_siniestro"], "score": int(r["score"]),
                    "nivel": r["nivel"], "motivo": r["motivo_principal"],
                    "monto": round(float(r["monto_reclamado"]), 2)})
    return out


def explicar(b, id_siniestro: str):
    row = b[b["id_siniestro"] == id_siniestro]
    if row.empty:
        return None
    r = row.iloc[0]
    return {"id_siniestro": id_siniestro, "score": int(r["score"]), "nivel": r["nivel"],
            "motivo_principal": r["motivo_principal"],
            "contribuciones": list(r["contribuciones"])}


def proveedores_top(b, n: int = 10):
    f = _flagged(b)
    total = max(len(f), 1)
    g = f.groupby("id_proveedor")
    filas = [(pid, len(grp), float(grp["monto_reclamado"].sum())) for pid, grp in g]
    filas.sort(key=lambda x: x[1], reverse=True)
    return [{"id_proveedor": pid, "alertas": int(a), "monto": round(m, 2),
             "pct_de_alertas": round(100 * a / total, 1)} for pid, a, m in filas[:n]]


def ramos_sospechosos(b):
    out = []
    for ramo, grp in b.groupby("ramo"):
        tot = len(grp)
        sos = int((grp["nivel"] != "VERDE").sum())
        out.append({"ramo": ramo, "total": tot, "sospechosos": sos,
                    "pct": round(100 * sos / tot, 1) if tot else 0.0})
    out.sort(key=lambda x: x["pct"], reverse=True)
    return out


def ciudades_top(b, n: int = 10):
    f = _flagged(b)
    filas = [(c, len(grp)) for c, grp in f.groupby("sucursal")]
    filas.sort(key=lambda x: x[1], reverse=True)
    return [{"ciudad": c, "alertas": int(a)} for c, a in filas[:n]]


def asegurados_frecuentes(b, n: int = 10):
    filas = [(a, len(grp)) for a, grp in b.groupby("id_asegurado")]
    filas.sort(key=lambda x: x[1], reverse=True)
    return [{"id_asegurado": a, "siniestros": int(c)} for a, c in filas[:n] if c >= 2]


def montos_atipicos(b, n: int = 10):
    f = b[b["contribuciones"].map(lambda cs: _tiene(cs, "Monto cercano"))]
    return top_riesgo(f.sort_values("monto_reclamado", ascending=False), n)


def documentos_faltantes(b, n: int = 10):
    f = b[(b["nivel"] == "ROJO") & b["contribuciones"].map(lambda cs: _tiene(cs, "Documento"))]
    return top_riesgo(f, n)


def borde_vigencia(b, n: int = 10):
    f = b[b["contribuciones"].map(lambda cs: _tiene(cs, "Borde de vigencia"))]
    return top_riesgo(f, n)


def patrones_repetidos(b):
    f = _flagged(b)
    conteo = {}
    for m in f["motivo_principal"]:
        conteo[m] = conteo.get(m, 0) + 1
    filas = sorted(conteo.items(), key=lambda x: x[1], reverse=True)
    return [{"patron": k, "casos": int(v)} for k, v in filas]


def resumen_ejecutivo(b):
    f = _flagged(b)
    prov = proveedores_top(b, 1)
    pat = patrones_repetidos(b)
    return {
        "total": int(len(b)),
        "rojo": int((b["nivel"] == "ROJO").sum()),
        "amarillo": int((b["nivel"] == "AMARILLO").sum()),
        "verde": int((b["nivel"] == "VERDE").sum()),
        "monto_en_revision": round(float(f["monto_reclamado"].sum()), 2),
        "proveedor_top": prov[0] if prov else None,
        "patron_top": pat[0] if pat else None,
    }


def recomendar(b, n: int = 5):
    return top_riesgo(b[b["nivel"] == "ROJO"], n)

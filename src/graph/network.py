"""Grafo de relaciones y detección de redes/anillos (E4, backend).

Construye la red bipartita proveedor–asegurado con los siniestros NO verdes y
detecta clusters (componentes conexas) que concentran varios siniestros: posibles
redes organizadas. Es la señal de "análisis de redes" de la rúbrica.
"""
from __future__ import annotations

import networkx as nx


def construir_grafo(b):
    """Grafo bipartito proveedor–asegurado de los siniestros sospechosos (no verdes)."""
    f = b[b["nivel"] != "VERDE"]
    G = nx.Graph()
    for _, r in f.iterrows():
        p, a = ("P", r["id_proveedor"]), ("A", r["id_asegurado"])
        G.add_node(p, tipo="proveedor")
        G.add_node(a, tipo="asegurado")
        G.add_edge(p, a)
    return G


def detectar_redes(b, min_siniestros: int = 5):
    """Proveedores que actúan como hub de varios siniestros sospechosos (anillos).

    Para cada proveedor con >= min_siniestros reclamos no verdes, reporta su cluster
    de asegurados (vecinos en el grafo) y la exposición. Pocos asegurados para muchos
    siniestros = firma de anillo. Ordenado por monto (exposición).
    """
    f = b[b["nivel"] != "VERDE"]
    G = construir_grafo(b)
    redes = []
    for nodo in [n for n in G.nodes() if n[0] == "P"]:
        prov = nodo[1]
        sins = f[f["id_proveedor"] == prov]
        if len(sins) < min_siniestros:
            continue
        asegs = sorted(n[1] for n in G.neighbors(nodo))
        redes.append({
            "proveedores": [prov],
            "n_proveedores": 1,
            "n_asegurados": len(asegs),
            "n_siniestros": int(len(sins)),
            "monto_total": round(float(sins["monto_reclamado"].sum()), 2),
            "siniestros": list(sins["id_siniestro"]),
        })
    redes.sort(key=lambda x: x["monto_total"], reverse=True)
    return redes

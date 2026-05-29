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
        item = {"id_siniestro": r["id_siniestro"], "score": int(r["score"]),
                "nivel": r["nivel"], "motivo": r["motivo_principal"],
                "monto": round(float(r["monto_reclamado"]), 2)}
        if "probabilidad_ml" in b.columns:
            item["probabilidad_ml"] = round(float(r.get("probabilidad_ml", 0.0)), 3)
        if "rareza_anomalia" in b.columns:
            item["rareza_anomalia"] = round(float(r.get("rareza_anomalia", 0.0)), 3)
        out.append(item)
    return out


def explicar(b, id_siniestro: str):
    row = b[b["id_siniestro"] == id_siniestro]
    if row.empty:
        return None
    r = row.iloc[0]
    out = {"id_siniestro": id_siniestro, "score": int(r["score"]), "nivel": r["nivel"],
           "motivo_principal": r["motivo_principal"],
           "contribuciones": list(r["contribuciones"])}
    if "probabilidad_ml" in b.columns:
        out["probabilidad_ml"] = round(float(r.get("probabilidad_ml", 0.0)), 3)
    if "rareza_anomalia" in b.columns:
        out["rareza_anomalia"] = round(float(r.get("rareza_anomalia", 0.0)), 3)
    return out


def resumen_ml(b):
    """Resumen centrado en el modelo ML y la anomalía para explicar el riesgo."""
    if "probabilidad_ml" not in b.columns:
        return {"total": int(len(b)), "mensaje": "La bandeja no trae probabilidades ML aún."}
    top = b.sort_values("probabilidad_ml", ascending=False).head(5)
    riesgo_promedio = float(b["probabilidad_ml"].mean()) if len(b) else 0.0
    anomalia_promedio = float(b["rareza_anomalia"].mean()) if "rareza_anomalia" in b.columns and len(b) else 0.0
    return {
        "total": int(len(b)),
        "riesgo_promedio_ml": round(riesgo_promedio, 3),
        "rareza_promedio": round(anomalia_promedio, 3),
        "top_ml": top_riesgo(top, 5),
    }


def proveedores_top(b, n: int = 10):
    f = _flagged(b)
    total = max(len(f), 1)
    g = f.groupby("id_proveedor")
    filas = [(pid, len(grp), float(grp["monto_reclamado"].sum())) for pid, grp in g]
    filas.sort(key=lambda x: x[1], reverse=True)
    return [{"id_proveedor": pid, "alertas": int(a), "monto": round(m, 2),
             "pct_de_alertas": round(100 * a / total, 1)} for pid, a, m in filas[:n]]


def proveedores_pareto(b, objetivo: float = 0.8, solo_rojos: bool = True):
    """Análisis de Pareto: el grupo mínimo de proveedores que concentra el `objetivo`
    (p. ej. 80%) de las alertas. Responde la prueba de fuego del jurado:
    "¿Qué proveedores concentran el 80% de las alertas rojas?".
    """
    objetivo = float(objetivo)
    if objetivo > 1:                       # admite 80 o 0.8
        objetivo /= 100.0
    base = b[b["nivel"] == "ROJO"] if solo_rojos else _flagged(b)
    nivel_txt = "rojas" if solo_rojos else "totales"
    total = int(len(base))
    if total == 0:
        return {"objetivo_pct": round(objetivo * 100), "nivel": nivel_txt, "total_alertas": 0,
                "n_proveedores_concentran": 0, "proveedores": [],
                "interpretacion": f"No hay alertas {nivel_txt} en la bandeja."}
    filas = [(pid, len(grp), float(grp["monto_reclamado"].sum())) for pid, grp in base.groupby("id_proveedor")]
    filas.sort(key=lambda x: (x[1], x[2]), reverse=True)
    acum, out = 0, []
    for pid, a, m in filas:
        acum += a
        out.append({"id_proveedor": pid, "alertas": int(a), "monto": round(m, 2),
                    "pct_individual": round(100 * a / total, 1),
                    "pct_acumulado": round(100 * acum / total, 1)})
        if acum / total >= objetivo:
            break
    return {
        "objetivo_pct": round(objetivo * 100),
        "nivel": nivel_txt,
        "total_alertas": total,
        "total_proveedores_con_alertas": len(filas),
        "n_proveedores_concentran": len(out),
        "interpretacion": (f"{len(out)} de {len(filas)} proveedores concentran el "
                           f"{round(100 * acum / total)}% de las {total} alertas {nivel_txt}."),
        "proveedores": out,
    }


def simulacion_ahorro(b, tasa_fraude_confirmado: float = 0.35, costo_revision_manual: float = 80.0):
    """Estima el ahorro potencial de priorizar con Argly (impacto de negocio).

    Cifra REFERENCIAL para el pitch, no garantizada: el ahorro se aproxima como el
    monto expuesto en casos ROJOS multiplicado por una tasa estimada de fraude que
    se confirma tras revisión humana, más el ahorro operativo de no revisar a ciegas.
    """
    f = _flagged(b)
    rojos = b[b["nivel"] == "ROJO"]
    monto_revision = float(f["monto_reclamado"].sum())
    monto_rojo = float(rojos["monto_reclamado"].sum())
    ahorro_fraude = monto_rojo * float(tasa_fraude_confirmado)
    # Ahorro operativo: priorizar evita revisar manualmente los verdes.
    verdes = int((b["nivel"] == "VERDE").sum())
    ahorro_operativo = verdes * float(costo_revision_manual)
    return {
        "casos_en_revision": int(len(f)),
        "casos_rojos": int(len(rojos)),
        "monto_en_revision": round(monto_revision, 2),
        "monto_expuesto_rojo": round(monto_rojo, 2),
        "tasa_fraude_confirmado_estimada": round(float(tasa_fraude_confirmado), 2),
        "ahorro_por_fraude_evitado": round(ahorro_fraude, 2),
        "ahorro_operativo_priorizacion": round(ahorro_operativo, 2),
        "ahorro_estimado_total": round(ahorro_fraude + ahorro_operativo, 2),
        "supuestos": (f"Ahorro por fraude = monto en casos ROJOS x {float(tasa_fraude_confirmado):.0%} "
                      f"confirmado tras revisión humana. Ahorro operativo = {verdes} casos verdes "
                      f"x ${costo_revision_manual:.0f} de revisión evitada. Cifra referencial."),
    }


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


def buscar_casos(
    b,
    nivel: str | None = None,
    ramo: str | None = None,
    cobertura: str | None = None,
    id_proveedor: str | None = None,
    id_asegurado: str | None = None,
    id_siniestro: str | None = None,
    score_min: float | None = None,
    score_max: float | None = None,
    monto_min: float | None = None,
    monto_max: float | None = None,
    solo_gate: bool | None = None,
    limit: int = 10,
    offset: int = 0,
):
    """Busca siniestros con filtros simples y devuelve registros tipo top_riesgo.

    Esto sirve como herramienta genérica para que el LLM explore la bandeja sin depender de keywords.
    """
    f = b
    if nivel:
        f = f[f["nivel"] == nivel.upper()]
    if ramo:
        f = f[f["ramo"].str.lower() == ramo.lower()]
    if cobertura:
        f = f[f["cobertura"].str.lower() == cobertura.lower()]
    if id_proveedor:
        f = f[f["id_proveedor"].str.lower() == id_proveedor.lower()]
    if id_asegurado:
        f = f[f["id_asegurado"].str.lower() == id_asegurado.lower()]
    if id_siniestro:
        f = f[f["id_siniestro"].str.lower() == id_siniestro.lower()]
    if score_min is not None:
        f = f[f["score"] >= score_min]
    if score_max is not None:
        f = f[f["score"] <= score_max]
    if monto_min is not None:
        f = f[f["monto_reclamado"] >= monto_min]
    if monto_max is not None:
        f = f[f["monto_reclamado"] <= monto_max]
    if solo_gate is True:
        f = f[f["gate"] == True]  # noqa: E712
    elif solo_gate is False:
        f = f[f["gate"] == False]  # noqa: E712

    if len(f) == 0:
        return []

    f = f.sort_values("score", ascending=False).iloc[offset:offset + limit]
    return top_riesgo(f, len(f))


def detalle_caso(b, id_siniestro: str):
    """Detalle enriquecido de un siniestro concreto."""
    r = b[b["id_siniestro"] == id_siniestro]
    if r.empty:
        return None
    row = r.iloc[0]
    detalle = {
        "id_siniestro": str(row["id_siniestro"]),
        "ramo": str(row["ramo"]),
        "cobertura": str(row["cobertura"]),
        "sucursal": str(row["sucursal"]),
        "monto_reclamado": float(row["monto_reclamado"]),
        "id_asegurado": str(row["id_asegurado"]),
        "id_proveedor": str(row["id_proveedor"]),
        "score": int(row["score"]),
        "nivel": str(row["nivel"]),
        "gate": bool(row["gate"]),
        "motivo_principal": str(row["motivo_principal"]),
        "probabilidad_ml": round(float(row.get("probabilidad_ml", 0.0) or 0.0), 3),
        "rareza_anomalia": round(float(row.get("rareza_anomalia", 0.0) or 0.0), 3),
        "contribuciones": list(row.get("contribuciones", [])),
    }
    return detalle


TOOL_CATALOG = [
    {
        "name": "buscar_casos",
        "description": "Busca siniestros con filtros por score, nivel, ramo, cobertura, proveedor, asegurado o gate.",
        "args": [
            "nivel", "ramo", "cobertura", "id_proveedor", "id_asegurado", "id_siniestro",
            "score_min", "score_max", "monto_min", "monto_max", "solo_gate", "limit", "offset",
        ],
    },
    {
        "name": "detalle_caso",
        "description": "Devuelve el detalle completo de un siniestro concreto por id_siniestro.",
        "args": ["id_siniestro"],
    },
    {"name": "top_riesgo", "description": "Ranking de los siniestros con mayor score.", "args": ["n"]},
    {"name": "explicar", "description": "Explica por qué un siniestro es sospechoso con contribuciones de reglas y ML.", "args": ["id_siniestro"]},
    {"name": "resumen_ejecutivo", "description": "Resumen ejecutivo de la bandeja, rojo/amarillo/verde y monto en revisión.", "args": []},
    {"name": "resumen_ml", "description": "Resumen del riesgo ML y anomalías sobre la bandeja.", "args": []},
    {"name": "proveedores_top", "description": "Proveedores que concentran más alertas.", "args": ["n"]},
    {"name": "proveedores_pareto", "description": "Análisis de Pareto: proveedores que concentran el 80% (objetivo) de las alertas ROJAS. Úsala para '¿qué proveedores concentran el 80% de las alertas rojas?'.", "args": ["objetivo", "solo_rojos"]},
    {"name": "simulacion_ahorro", "description": "Estima el ahorro potencial (impacto de negocio) de priorizar con Argly.", "args": ["tasa_fraude_confirmado"]},
    {"name": "ramos_sospechosos", "description": "Porcentaje de casos sospechosos por ramo.", "args": []},
    {"name": "ciudades_top", "description": "Ciudades con más alertas.", "args": ["n"]},
    {"name": "asegurados_frecuentes", "description": "Asegurados con más siniestros.", "args": ["n"]},
    {"name": "montos_atipicos", "description": "Casos con monto cercano a la suma asegurada.", "args": ["n"]},
    {"name": "documentos_faltantes", "description": "Casos con documentos incompletos o faltantes.", "args": ["n"]},
    {"name": "borde_vigencia", "description": "Casos cerca del borde de vigencia.", "args": ["n"]},
    {"name": "patrones_repetidos", "description": "Patrones repetidos entre sospechosos.", "args": []},
    {"name": "recomendar", "description": "Prioriza los siniestros ROJOS para revisión.", "args": ["n"]},
]


def catalogo_herramientas():
    return TOOL_CATALOG


def ejecutar_herramienta(nombre: str, b, argumentos: dict | None = None):
    argumentos = argumentos or {}
    n = argumentos.get("n", 10)
    if nombre == "buscar_casos":
        return buscar_casos(b, **argumentos)
    if nombre == "detalle_caso":
        return detalle_caso(b, argumentos.get("id_siniestro", ""))
    if nombre == "top_riesgo":
        return top_riesgo(b, int(n))
    if nombre == "explicar":
        return explicar(b, argumentos.get("id_siniestro", ""))
    if nombre == "resumen_ejecutivo":
        return resumen_ejecutivo(b)
    if nombre == "resumen_ml":
        return resumen_ml(b)
    if nombre == "proveedores_top":
        return proveedores_top(b, int(n))
    if nombre == "proveedores_pareto":
        return proveedores_pareto(b, argumentos.get("objetivo", 0.8), argumentos.get("solo_rojos", True))
    if nombre == "simulacion_ahorro":
        return simulacion_ahorro(b, argumentos.get("tasa_fraude_confirmado", 0.35))
    if nombre == "ramos_sospechosos":
        return ramos_sospechosos(b)
    if nombre == "ciudades_top":
        return ciudades_top(b, int(n))
    if nombre == "asegurados_frecuentes":
        return asegurados_frecuentes(b, int(n))
    if nombre == "montos_atipicos":
        return montos_atipicos(b, int(n))
    if nombre == "documentos_faltantes":
        return documentos_faltantes(b, int(n))
    if nombre == "borde_vigencia":
        return borde_vigencia(b, int(n))
    if nombre == "patrones_repetidos":
        return patrones_repetidos(b)
    if nombre == "recomendar":
        return recomendar(b, int(n))
    raise ValueError(f"Herramienta no soportada: {nombre}")

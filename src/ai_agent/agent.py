"""Agente de IA antifraude (E5).

Responde preguntas en lenguaje natural sobre la bandeja. Usa herramientas
DETERMINISTAS (tools.py) para obtener los datos, y un LLM compatible-OpenAI
(DeepSeek/Groq) SOLO para narrar. Si no hay LLM configurado, responde con
plantillas (fallback determinista): así siempre funciona, incluso en la demo.

Variables de entorno para activar el LLM:
    LLM_API_KEY=...            (o OPENAI_API_KEY)
    LLM_BASE_URL=https://api.deepseek.com    (default)
    LLM_MODEL=deepseek-chat                   (default)
"""
from __future__ import annotations

import os
import re

from src.ai_agent import tools

AVISO = "Estas son alertas para revisión humana, no acusaciones de fraude."


def _router(pregunta: str, b):
    """Mapea la pregunta a una herramienta determinista. Devuelve (herramienta, datos, texto)."""
    q = pregunta.lower()
    m = re.search(r"sin\d{3,}", q)

    if any(k in q for k in ["por que", "por qué", "porque", "explica"]) and m:
        ids = m.group(0).upper()
        d = tools.explicar(b, ids)
        if not d:
            return "explicar", {"id": ids}, f"No encontré el siniestro {ids}."
        ev = "; ".join(f"{c['regla']} (+{c['puntos']})" for c in d["contribuciones"])
        return "explicar", d, f"{ids} es {d['nivel']} (score {d['score']}). Señales: {ev}."

    if any(k in q for k in ["redes", "anillo", "ring", "colusion", "colusión"]):
        from src.graph.network import detectar_redes
        d = detectar_redes(b)
        if not d:
            return "redes", d, "No detecté redes con la concentración mínima."
        top = ", ".join(f"{r['proveedores'][0]} ({r['n_siniestros']} sin., {r['n_asegurados']} aseg.)" for r in d[:3])
        return "redes", d, f"Detecté {len(d)} posibles redes/anillos. Top: {top}."

    if "proveedor" in q:
        d = tools.proveedores_top(b)
        top = ", ".join(f"{x['id_proveedor']} ({x['alertas']} alertas, {x['pct_de_alertas']}%)" for x in d[:5])
        return "proveedores_top", d, f"Proveedores que concentran más alertas: {top}."

    if "ramo" in q:
        d = tools.ramos_sospechosos(b)
        return "ramos_sospechosos", d, "% de casos sospechosos por ramo: " + ", ".join(f"{x['ramo']} ({x['pct']}%)" for x in d) + "."

    if "ciudad" in q or "sucursal" in q:
        d = tools.ciudades_top(b)
        return "ciudades_top", d, "Ciudades con más alertas: " + ", ".join(f"{x['ciudad']} ({x['alertas']})" for x in d[:5]) + "."

    if "asegurado" in q or "frecuen" in q:
        d = tools.asegurados_frecuentes(b)
        return "asegurados_frecuentes", d, "Asegurados con más siniestros: " + ", ".join(f"{x['id_asegurado']} ({x['siniestros']})" for x in d[:5]) + "."

    if "documento" in q or "falta" in q:
        d = tools.documentos_faltantes(b)
        return "documentos_faltantes", d, f"{len(d)} casos críticos con documentos incompletos. Top: " + ", ".join(x["id_siniestro"] for x in d[:5]) + "."

    if "monto" in q or "atipic" in q or "atípic" in q:
        d = tools.montos_atipicos(b)
        return "montos_atipicos", d, f"{len(d)} casos con monto atípico (cercano a la suma asegurada). Top: " + ", ".join(x["id_siniestro"] for x in d[:5]) + "."

    if "borde" in q or "vigencia" in q or "inicio de la p" in q:
        d = tools.borde_vigencia(b)
        return "borde_vigencia", d, f"{len(d)} siniestros cerca del borde de vigencia. Top: " + ", ".join(x["id_siniestro"] for x in d[:5]) + "."

    if "patron" in q or "patrón" in q or "repiten" in q or "repite" in q:
        d = tools.patrones_repetidos(b)
        return "patrones_repetidos", d, "Patrones más repetidos en sospechosos: " + ", ".join(f"{x['patron']} ({x['casos']})" for x in d[:5]) + "."

    if "resumen" in q or "ejecutivo" in q:
        d = tools.resumen_ejecutivo(b)
        pat = d["patron_top"]["patron"] if d["patron_top"] else "n/a"
        return "resumen_ejecutivo", d, (f"De {d['total']} siniestros: {d['rojo']} rojos y {d['amarillo']} amarillos, "
                                        f"${d['monto_en_revision']:,.0f} en revisión. Patrón dominante: {pat}.")

    if "recomien" in q or "primero" in q or "revisar" in q or "prioriza" in q:
        d = tools.recomendar(b)
        return "recomendar", d, "Revisa primero: " + ", ".join(f"{x['id_siniestro']} ({x['score']})" for x in d) + "."

    # Default: top de mayor riesgo (toma el número si lo mencionan)
    n = 10
    mm = re.search(r"\b(\d{1,2})\b", q)
    if mm:
        n = min(int(mm.group(1)), 50)
    d = tools.top_riesgo(b, n)
    return "top_riesgo", d, f"Top {len(d)} de mayor riesgo: " + ", ".join(f"{x['id_siniestro']} ({x['score']} {x['nivel']})" for x in d[:10]) + "."


def _llm_key():
    return os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _narrar_llm(pregunta, datos):
    import json
    import httpx

    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    sistema = ("Eres un asistente antifraude de una aseguradora. Responde en español, breve y claro, "
               "USANDO SOLO los datos JSON provistos (no inventes ni cambies números). "
               "Son alertas para revisión humana, nunca acusaciones.")
    usuario = f"Pregunta: {pregunta}\n\nDatos: {json.dumps(datos, ensure_ascii=False)}"
    r = httpx.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {_llm_key()}"},
        json={"model": model, "temperature": 0.2,
              "messages": [{"role": "system", "content": sistema},
                           {"role": "user", "content": usuario}]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def responder(pregunta: str, b) -> dict:
    """Responde una pregunta sobre la bandeja. Narra con LLM si está configurado, si no, plantilla."""
    herramienta, datos, texto = _router(pregunta, b)
    fuente = "reglas"
    if _llm_key():
        try:
            texto = _narrar_llm(pregunta, datos)
            fuente = "llm"
        except Exception:
            fuente = "reglas (LLM no disponible)"
    return {"pregunta": pregunta, "respuesta": texto, "datos": datos,
            "herramienta": herramienta, "fuente": fuente, "aviso": AVISO}

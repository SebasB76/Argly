"""Agente de IA antifraude (E5).

Responde preguntas en lenguaje natural sobre la bandeja. Usa herramientas
DETERMINISTAS (tools.py) solo para obtener datos de soporte, y un LLM
compatible-OpenAI (DeepSeek/Groq/Gemini) para redactar siempre la respuesta.
Si no hay LLM configurado, devuelve un mensaje de indisponibilidad.

Variables de entorno para activar el LLM:
    GEMINI_API_KEY=...         (recomendado si vas a usar Gemini)
    LLM_PROVIDER=gemini        (opcional; también se autodetecta si existe GEMINI_API_KEY)
    LLM_MODEL=gemini-1.5-flash  (opcional)
    LLM_API_KEY=...            (fallback OpenAI-compatible)
    LLM_BASE_URL=https://api.deepseek.com
    LLM_MODEL=deepseek-chat
"""
from __future__ import annotations

import os
import re

from src.ai_agent import tools

AVISO = "Estas son alertas para revisión humana, no acusaciones de fraude."


def _router(pregunta: str, b):
    """Mapea la pregunta a una herramienta determinista. Devuelve (herramienta, datos, texto_base)."""
    q = pregunta.lower()
    m = re.search(r"sin\d{3,}", q)

    if any(k in q for k in ["por que", "por qué", "porque", "explica"]) and m:
        ids = m.group(0).upper()
        d = tools.explicar(b, ids)
        if not d:
            return "explicar", {"id": ids}, f"No encontré el siniestro {ids}."
        ev = "; ".join(f"{c['regla']} (+{c['puntos']})" for c in d["contribuciones"])
        ml = []
        if d.get("probabilidad_ml") is not None:
            ml.append(f"probabilidad ML {d['probabilidad_ml']:.0%}")
        if d.get("rareza_anomalia") is not None:
            ml.append(f"rareza anómala {d['rareza_anomalia']:.0%}")
        extra = f". Evidencia ML: {', '.join(ml)}" if ml else ""
        return "explicar", d, f"{ids} es {d['nivel']} (score {d['score']}). Señales: {ev}{extra}."

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

    if any(k in q for k in ["modelo", "machine learning", "ml", "probabilidad", "anomalia", "anomalía"]):
        d = tools.resumen_ml(b)
        top = ", ".join(f"{x['id_siniestro']} ({x.get('probabilidad_ml', 0):.0%})" for x in d.get("top_ml", [])[:5])
        return "resumen_ml", d, (
            f"El modelo ML concentra un riesgo promedio de {d.get('riesgo_promedio_ml', 0):.0%}. "
            f"Rareza promedio: {d.get('rareza_promedio', 0):.0%}. Top ML: {top}."
        )

    if "recomien" in q or "primero" in q or "revisar" in q or "prioriza" in q:
        d = tools.recomendar(b)
        return "recomendar", d, "Revisa primero: " + ", ".join(f"{x['id_siniestro']} ({x['score']})" for x in d) + "."

    # Default: no consulta determinista; el LLM responderá la pregunta de forma conversacional.
    return "chat", {}, ""


def _llm_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")


def _provider():
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return "openai"


def _narrar_llm(pregunta, datos):
    import json
    import httpx

    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    provider = _provider()

    sistema = ("Eres un asistente antifraude de una aseguradora. Responde en español de forma clara y estructurada. "
               "USANDO SOLO los datos JSON provistos (no inventes ni cambies números). "
               "Incluye siempre evidencia basada en score, probabilidad ML y rareza de anomalía cuando existan. "
               "Devuelve la respuesta en JSON con estas claves: 'respuesta' (texto breve), 'evidencia' (lista o texto), "
               "y 'datos_usados' (qué campos del JSON usaste). Si no hay datos para responder, indícalo claramente. "
               "No recortes la respuesta: proporciona toda la información solicitada. Son alertas para revisión humana, nunca acusaciones.")
    usuario = f"Pregunta: {pregunta}\n\nDatos: {json.dumps(datos, ensure_ascii=False)}"

    # Gemini / Google Generative API
    if provider == "gemini":
        gem_base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        gem_model = os.environ.get("LLM_MODEL", model)
        api_key = _llm_key()

        url = f"{gem_base}/models/{gem_model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": sistema}]},
            "contents": [{"role": "user", "parts": [{"text": usuario}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
        }
        r = httpx.post(url, params={"key": api_key}, json=payload, timeout=60)
        r.raise_for_status()
        j = r.json()

        # Robust extraction: try multiple known shapes and concatenate text parts
        def _extract_text_from_node(node):
            parts = []
            if isinstance(node, dict):
                # 1) candidates / choices arrays
                for key in ("candidates", "choices", "output"):
                    if key in node and isinstance(node[key], list):
                        for c in node[key]:
                            parts.append(_extract_text_from_node(c))
                # 2) content arrays with parts
                if "content" in node:
                    cont = node["content"]
                    if isinstance(cont, list):
                        for item in cont:
                            if isinstance(item, dict):
                                t = item.get("text") or item.get("content")
                                if isinstance(t, str):
                                    parts.append(t)
                                else:
                                    parts.append(_extract_text_from_node(item))
                # 3) message.content.text
                if "message" in node and isinstance(node["message"], dict):
                    msg = node["message"]
                    if "content" in msg and isinstance(msg["content"], dict):
                        t = msg["content"].get("text")
                        if isinstance(t, str):
                            parts.append(t)
                # 4) direct text
                if "text" in node and isinstance(node["text"], str):
                    parts.append(node["text"])
            elif isinstance(node, list):
                for it in node:
                    parts.append(_extract_text_from_node(it))
            elif isinstance(node, str):
                parts.append(node)
            # flatten and join
            flat = []
            for p in parts:
                if isinstance(p, str) and p:
                    flat.append(p)
                elif isinstance(p, list):
                    flat.extend([x for x in p if isinstance(x, str)])
            return "\n".join(flat)

        texto = _extract_text_from_node(j)
        if texto and texto.strip():
            return texto.strip()
        return json.dumps(j, ensure_ascii=False)

    # OpenAI-compatible / DeepSeek path
    if provider in ("openai", "deepseek", "default"):
        r = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {_llm_key()}"},
            json={"model": model, "temperature": 0.2, "max_tokens": 1024,
                  "messages": [{"role": "system", "content": sistema},
                               {"role": "user", "content": usuario}]},
            timeout=60,
        )
        r.raise_for_status()
        j = r.json()
        # flexible parse for OpenAI-like responses
        try:
            return j["choices"][0]["message"]["content"].strip()
        except Exception:
            try:
                return j["choices"][0]["text"].strip()
            except Exception:
                return json.dumps(j, ensure_ascii=False)

    raise RuntimeError(f"LLM provider no soportado: {provider}")
                    url = f"{gem_base}/models/{gem_model}:generateContent"
                    payload = {
                        "systemInstruction": {"parts": [{"text": sistema}]},
                        "contents": [{"role": "user", "parts": [{"text": usuario}]}],
                        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
                    }
                    r = httpx.post(url, params={"key": api_key}, json=payload, timeout=60)
                    r.raise_for_status()
                    j = r.json()

                    # Robust extraction: try multiple known shapes and concatenate text parts
                    def _extract_text_from_node(node):
                        parts = []
                        if isinstance(node, dict):
                            # 1) candidates / choices arrays
                            for key in ("candidates", "choices", "output"):
                                if key in node and isinstance(node[key], list):
                                    for c in node[key]:
                                        parts.append(_extract_text_from_node(c))
                            # 2) content arrays with parts
                            if "content" in node:
                                cont = node["content"]
                                if isinstance(cont, list):
                                    for item in cont:
                                        if isinstance(item, dict):
                                            t = item.get("text") or item.get("content")
                                            if isinstance(t, str):
                                                parts.append(t)
                                            else:
                                                parts.append(_extract_text_from_node(item))
                            # 3) message.content.text
                            if "message" in node and isinstance(node["message"], dict):
                                msg = node["message"]
                                if "content" in msg and isinstance(msg["content"], dict):
                                    t = msg["content"].get("text")
                                    if isinstance(t, str):
                                        parts.append(t)
                            # 4) direct text
                            if "text" in node and isinstance(node["text"], str):
                                parts.append(node["text"])
                        elif isinstance(node, list):
                            for it in node:
                                parts.append(_extract_text_from_node(it))
                        elif isinstance(node, str):
                            parts.append(node)
                        # flatten and join
                        flat = []
                        for p in parts:
                            if isinstance(p, str) and p:
                                flat.append(p)
                            elif isinstance(p, list):
                                flat.extend([x for x in p if isinstance(x, str)])
                        return "\n".join(flat)

                    texto = _extract_text_from_node(j)
                    if texto and texto.strip():
                        return texto.strip()
                    return json.dumps(j, ensure_ascii=False)

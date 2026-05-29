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

    if any(k in q for k in ["mayor riesgo", "mayores riesgos", "top 10", "10 siniestros", "10 casos"]):
        d = tools.top_riesgo(b, 10)
        return "top_riesgo", d, "Top 10 siniestros con mayor riesgo: " + ", ".join(
            f"{x['id_siniestro']} ({x['score']})" for x in d
        ) + "."

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


def _llm_key(provider: str | None = None):
    """Llave del LLM, provider-aware.

    En modo openai/deepseek prioriza LLM_API_KEY/OPENAI_API_KEY sobre GEMINI_API_KEY,
    para no mandar por error la llave de Gemini a un endpoint OpenAI-compatible (DeepSeek/
    Groq) cuando ambas están configuradas. Sin provider mantiene el comportamiento previo.
    """
    gemini = os.environ.get("GEMINI_API_KEY")
    openai_compat = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    p = (provider or "").strip().lower()
    if p in ("openai", "deepseek", "default"):
        return openai_compat or gemini
    if p == "gemini":
        return gemini or openai_compat
    return gemini or openai_compat


def _provider():
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    return "openai"


def _usar_llm() -> bool:
    flag = os.environ.get("AGENT_USE_LLM", "").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return False
    if _llm_key():
        return True
    return False


def _gemini_model_candidates():
    candidates = []
    configured = os.environ.get("LLM_MODEL", "").strip()
    if configured:
        candidates.append(configured)
    for fallback in ("gemini-2.5-flash", "gemini-2.0-flash"):
        if fallback not in candidates:
            candidates.append(fallback)
    return candidates


def _normalizar_texto_llm(texto: str) -> str:
    texto = (texto or "").strip()
    if not texto:
        return ""
    texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*```\s*$", "", texto)
    texto = texto.replace("```json", "").replace("```", "").strip()
    return texto


def _extraer_json(texto: str) -> dict | None:
    texto = _normalizar_texto_llm(texto)
    if not texto:
        return None

    candidates = [texto]
    match = re.search(r"\{[\s\S]*\}", texto)
    if match:
        candidates.insert(0, match.group(0))

    for candidato in candidates:
        try:
            parsed = __import__("json").loads(candidato)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue
    return None


def _json_safe(valor):
    import json
    try:
        json.dumps(valor, ensure_ascii=False)
        return valor
    except Exception:
        if isinstance(valor, dict):
            return {k: _json_safe(v) for k, v in valor.items()}
        if isinstance(valor, list):
            return [_json_safe(v) for v in valor]
        return str(valor)


def _extraer_siniestro_id(pregunta: str):
    m = re.search(r"sin\d{3,}", pregunta.lower())
    return m.group(0).upper() if m else None


def _fila_a_contexto(r) -> dict:
    return {
        "id_siniestro": str(r["id_siniestro"]),
        "score": int(r["score"]),
        "nivel": str(r["nivel"]),
        "gate": bool(r["gate"]),
        "motivo_principal": str(r["motivo_principal"]),
        "ramo": str(r["ramo"]),
        "cobertura": str(r["cobertura"]),
        "sucursal": str(r["sucursal"]),
        "monto_reclamado": float(r["monto_reclamado"]),
        "id_asegurado": str(r["id_asegurado"]),
        "id_proveedor": str(r["id_proveedor"]),
        "probabilidad_ml": float(r.get("probabilidad_ml", 0.0) or 0.0),
        "rareza_anomalia": float(r.get("rareza_anomalia", 0.0) or 0.0),
        "contribuciones": r.get("contribuciones", []),
    }


def _contexto_ia(pregunta: str, b):
    """Construye un contexto compacto pero rico con la bandeja real y las herramientas disponibles."""
    if b is None or len(b) == 0:
        return {
            "pregunta": pregunta,
            "resumen": "No hay datos disponibles.",
            "catalogo_herramientas": tools.catalogo_herramientas(),
            "bandeja": [],
            "ml": {},
        }

    resumen = tools.resumen_ejecutivo(b)
    ml = tools.resumen_ml(b)
    top_riesgo = tools.top_riesgo(b, 12)

    contexto = {
        "pregunta": pregunta,
        "resumen": resumen,
        "ml": ml,
        "catalogo_herramientas": tools.catalogo_herramientas(),
        "columnas_bandeja": list(b.columns),
        "estadisticas_por_nivel": {
            "rojo": int((b["nivel"] == "ROJO").sum()),
            "amarillo": int((b["nivel"] == "AMARILLO").sum()),
            "verde": int((b["nivel"] == "VERDE").sum()),
        },
        "muestras": {
            "top_riesgo": top_riesgo[:8],
            "rojos": tools.top_riesgo(b[b["nivel"] == "ROJO"], 8),
            "amarillos": tools.top_riesgo(b[b["nivel"] == "AMARILLO"], 5),
            "verdes": tools.top_riesgo(b[b["nivel"] == "VERDE"], 5),
            "redes": [],
        },
    }

    try:
        from src.graph.network import detectar_redes
        contexto["muestras"]["redes"] = detectar_redes(b)
    except Exception:
        contexto["muestras"]["redes"] = []

    return contexto


def _llm_generar_texto(sistema: str, usuario: str):
    import json
    import httpx
    import time
    import random

    base = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")
    provider = _provider()

    if provider == "gemini":
        gem_base = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        api_key = _llm_key(provider)
        last_error = None
        max_retries = 3
        base_delay = 1.0
        for gem_model in _gemini_model_candidates():
            try:
                url = f"{gem_base}/models/{gem_model}:generateContent"
                gen_config = {"temperature": 0.2, "maxOutputTokens": 1024}
                # Los modelos 2.5 Flash traen "thinking" ON por defecto: consume parte
                # de maxOutputTokens y puede devolver respuesta VACÍA (finishReason=MAX_TOKENS).
                # La tarea del agente (elegir tool + redactar) no necesita razonamiento
                # extendido, así que lo desactivamos (más rápido, más barato, sin truncados).
                if "2.5" in gem_model and "pro" not in gem_model:
                    gen_config["thinkingConfig"] = {"thinkingBudget": 0}
                payload = {
                    "systemInstruction": {"parts": [{"text": sistema}]},
                    "contents": [{"role": "user", "parts": [{"text": usuario}]}],
                    "generationConfig": gen_config,
                }
                attempt = 0
                while True:
                    attempt += 1
                    r = httpx.post(url, params={"key": api_key}, json=payload, timeout=60)
                    try:
                        r.raise_for_status()
                        break
                    except httpx.HTTPStatusError as http_exc:
                        status = getattr(http_exc.response, "status_code", None)
                        retry_after = None
                        try:
                            retry_after = int(http_exc.response.headers.get("Retry-After") or 0)
                        except Exception:
                            retry_after = None
                        if status in (429, 500, 502, 503, 504) and attempt <= max_retries:
                            delay = retry_after if retry_after and retry_after > 0 else base_delay * (2 ** (attempt - 1))
                            delay = delay + random.random() * 0.5
                            time.sleep(delay)
                            continue
                        if status in (429, 500, 502, 503, 504):
                            return (
                                f"Lo siento, el servicio de LLM no está disponible (código {status}). "
                                "Intenta de nuevo más tarde o revisa las credenciales/limitaciones de cuota."
                            )
                        raise
                j = r.json()

                def _extract_text_from_node(node):
                    parts = []
                    if isinstance(node, dict):
                        for key in ("candidates", "choices", "output"):
                            if key in node and isinstance(node[key], list):
                                for c in node[key]:
                                    parts.append(_extract_text_from_node(c))
                        if "parts" in node and isinstance(node["parts"], list):
                            for item in node["parts"]:
                                if isinstance(item, dict) and isinstance(item.get("text"), str):
                                    parts.append(item["text"])
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
                            elif isinstance(cont, dict):
                                # Gemini: content = {"parts": [{"text": ...}], "role": "model"}
                                parts.append(_extract_text_from_node(cont))
                        if "message" in node and isinstance(node["message"], dict):
                            msg = node["message"]
                            if "content" in msg and isinstance(msg["content"], dict):
                                t = msg["content"].get("text")
                                if isinstance(t, str):
                                    parts.append(t)
                        if "text" in node and isinstance(node["text"], str):
                            parts.append(node["text"])
                    elif isinstance(node, list):
                        for it in node:
                            parts.append(_extract_text_from_node(it))
                    elif isinstance(node, str):
                        parts.append(node)
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
            except Exception as exc:
                last_error = exc
                status = getattr(getattr(exc, "response", None), "status_code", None)
                if status in (429, 500, 502, 503, 504):
                    return (
                        f"Lo siento, el servicio de LLM no está disponible (código {status}). "
                        "Intenta de nuevo más tarde o revisa las credenciales/limitaciones de cuota."
                    )
                if status not in (400, 404):
                    raise
        if last_error is not None:
            raise last_error

    if provider in ("openai", "deepseek", "default"):
        max_retries = 3
        base_delay = 1.0
        attempt = 0
        while True:
            attempt += 1
            r = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {_llm_key(provider)}"},
                json={"model": model, "temperature": 0.2, "max_tokens": 1024,
                      "messages": [{"role": "system", "content": sistema},
                                   {"role": "user", "content": usuario}]},
                timeout=60,
            )
            try:
                r.raise_for_status()
                break
            except httpx.HTTPStatusError as http_exc:
                status = getattr(http_exc.response, "status_code", None)
                retry_after = None
                try:
                    retry_after = int(http_exc.response.headers.get("Retry-After") or 0)
                except Exception:
                    retry_after = None
                if status in (429, 500, 502, 503, 504) and attempt <= max_retries:
                    delay = retry_after if retry_after and retry_after > 0 else base_delay * (2 ** (attempt - 1))
                    delay = delay + random.random() * 0.5
                    time.sleep(delay)
                    continue
                if status in (429, 500, 502, 503, 504):
                    return (
                        f"Lo siento, el servicio de LLM no está disponible (código {status}). "
                        "Intenta de nuevo más tarde o revisa las credenciales/limitaciones de cuota."
                    )
                raise
        j = r.json()
        try:
            return j["choices"][0]["message"]["content"].strip()
        except Exception:
            try:
                return j["choices"][0]["text"].strip()
            except Exception:
                return json.dumps(j, ensure_ascii=False)

    raise RuntimeError(f"LLM provider no soportado: {provider}")


def _planificar_accion(pregunta: str, contexto: dict):
    sistema = (
        "Eres un agente antifraude. Debes decidir si necesitas una herramienta o si puedes responder directamente. "
        "Responde SOLO con JSON válido y sin markdown. Formato: {\"action\":\"tool\"|\"final\",\"tool\":\"nombre\",\"arguments\":{...},\"answer\":\"texto\",\"reason\":\"breve\"}. "
        "Si la pregunta necesita consultar la bandeja, usa action=tool con una herramienta del catálogo. "
        "Si ya tienes suficiente información para responder, usa action=final y redacta la respuesta. "
        "Las herramientas disponibles y el contexto de datos están en el JSON de usuario."
    )
    usuario = __import__("json").dumps({
        "pregunta": pregunta,
        "contexto": contexto,
    }, ensure_ascii=False)
    texto = _llm_generar_texto(sistema, usuario)
    plan = _extraer_json(texto)
    if not plan:
        return {"action": "final", "answer": texto, "reason": "respuesta_directa_sin_json"}
    return plan


def _redactar_respuesta_final(pregunta: str, contexto: dict, plan: dict, resultado_herramienta=None):
    sistema = (
        "Eres un asistente antifraude de una aseguradora. Responde en español con texto natural, claro y breve. "
        "No devuelvas JSON ni markdown salvo que sea estrictamente necesario. "
        "Usa la pregunta, el contexto de la bandeja y, si existe, el resultado de la herramienta. "
        "No inventes datos. Si hay casos sospechosos, nómbralos con score/nivel/motivo. "
        "Son alertas para revisión humana, nunca acusaciones."
    )
    usuario = __import__("json").dumps({
        "pregunta": pregunta,
        "contexto": contexto,
        "plan": plan,
        "resultado_herramienta": _json_safe(resultado_herramienta),
    }, ensure_ascii=False)
    return _llm_generar_texto(sistema, usuario)


def responder(pregunta: str, b):
    contexto_ia = _contexto_ia(pregunta, b)

    if not _usar_llm():
        return {
            "herramienta": "chat",
            "datos": {},
            "contexto_ia": contexto_ia,
            "respuesta": (
                "No hay LLM configurado. Activa `GEMINI_API_KEY` o `LLM_API_KEY` para usar el agente con herramientas."
            ),
            "fuente": "sin_llm",
            "aviso": AVISO,
        }

    plan = _planificar_accion(pregunta, contexto_ia)
    herramienta = plan.get("tool") or plan.get("tool_name") or plan.get("nombre") or "chat"
    argumentos = plan.get("arguments") or plan.get("tool_args") or plan.get("params") or {}
    if not isinstance(argumentos, dict):
        argumentos = {}

    resultado_herramienta = None
    fuente = f"llm:{_provider()}"

    if plan.get("action") == "tool" and herramienta not in (None, "", "chat"):
        try:
            resultado_herramienta = tools.ejecutar_herramienta(herramienta, b, argumentos)
            respuesta = _redactar_respuesta_final(pregunta, contexto_ia, plan, resultado_herramienta)
            fuente = f"llm:{_provider()}+tool:{herramienta}"
        except Exception as exc:
            respuesta = _redactar_respuesta_final(
                pregunta,
                contexto_ia,
                {**plan, "action": "final", "error": str(exc)},
                resultado_herramienta,
            )
    else:
        respuesta = plan.get("answer") or plan.get("respuesta") or _redactar_respuesta_final(
            pregunta, contexto_ia, plan, resultado_herramienta
        )

    return {
        "herramienta": herramienta,
        "datos": resultado_herramienta if resultado_herramienta is not None else argumentos,
        "contexto_ia": contexto_ia,
        "respuesta": respuesta,
        "fuente": fuente,
        "aviso": AVISO,
    }

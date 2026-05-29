"""Tests del agente de IA (E5): planificación LLM + ejecución de herramientas."""
from fastapi.testclient import TestClient

import src.ai_agent.agent as agent_mod
from src.ai_agent.agent import responder
from src.app.main import app
from src.ingestion.generate_synthetic import generar
from src.pipeline import construir_bandeja

_b = construir_bandeja(generar(seed=42))
client = TestClient(app)


def test_sin_llm_devuelve_indicacion_clara(monkeypatch):
    monkeypatch.setattr(agent_mod, "_usar_llm", lambda: False)
    r = responder("¿cuáles son los casos más sospechosos?", _b)
    assert r["fuente"] == "sin_llm"
    assert "LLM" in r["respuesta"]


def test_planifica_y_ejecuta_top_riesgo(monkeypatch):
    monkeypatch.setattr(agent_mod, "_usar_llm", lambda: True)
    monkeypatch.setattr(
        agent_mod,
        "_planificar_accion",
        lambda pregunta, contexto: {"action": "tool", "tool": "top_riesgo", "arguments": {"n": 10}},
    )
    monkeypatch.setattr(
        agent_mod,
        "_redactar_respuesta_final",
        lambda pregunta, contexto, plan, resultado_herramienta=None: f"{len(resultado_herramienta)} casos priorizados",
    )

    r = responder("¿cuáles son los 10 siniestros con mayor riesgo?", _b)
    assert r["fuente"].startswith("llm:")
    assert r["herramienta"] == "top_riesgo"
    assert isinstance(r["datos"], list)
    assert len(r["datos"]) == 10
    assert r["respuesta"] == "10 casos priorizados"


def test_planifica_busqueda_de_sospechosos(monkeypatch):
    monkeypatch.setattr(agent_mod, "_usar_llm", lambda: True)
    monkeypatch.setattr(
        agent_mod,
        "_planificar_accion",
        lambda pregunta, contexto: {"action": "tool", "tool": "buscar_casos", "arguments": {"nivel": "ROJO", "limit": 5}},
    )
    monkeypatch.setattr(
        agent_mod,
        "_redactar_respuesta_final",
        lambda pregunta, contexto, plan, resultado_herramienta=None: ", ".join(x["id_siniestro"] for x in resultado_herramienta),
    )

    r = responder("¿cuáles son los casos más sospechosos?", _b)
    assert r["herramienta"] == "buscar_casos"
    assert len(r["datos"]) == 5
    assert r["respuesta"]
    assert "SIN" in r["respuesta"]


def test_endpoint_preguntar(monkeypatch):
    monkeypatch.setattr(agent_mod, "_usar_llm", lambda: True)
    monkeypatch.setattr(
        agent_mod,
        "_planificar_accion",
        lambda pregunta, contexto: {"action": "final", "answer": "Respuesta directa de prueba"},
    )
    monkeypatch.setattr(
        agent_mod,
        "_redactar_respuesta_final",
        lambda pregunta, contexto, plan, resultado_herramienta=None: plan.get("answer", ""),
    )

    resp = client.post("/api/preguntar", json={"pregunta": "¿qué proveedores concentran las alertas?"})
    assert resp.status_code == 200
    j = resp.json()
    assert j["respuesta"] == "Respuesta directa de prueba"
    assert "contexto_ia" in j
    assert "catalogo_herramientas" in j["contexto_ia"]

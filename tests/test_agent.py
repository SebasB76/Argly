"""Tests del agente de IA (E5): router determinista (sin API key) + endpoint."""
from fastapi.testclient import TestClient

from src.ai_agent.agent import responder
from src.app.main import app
from src.pipeline import construir_bandeja
from src.ingestion.generate_synthetic import generar

_b = construir_bandeja(generar(seed=42))


def test_top_riesgo():
    r = responder("¿cuáles son los 10 siniestros con mayor riesgo?", _b)
    assert r["herramienta"] == "top_riesgo"
    assert len(r["datos"]) == 10
    assert r["fuente"].startswith("reglas")   # sin API key -> fallback determinista


def test_proveedores():
    r = responder("¿qué proveedores concentran más alertas rojas?", _b)
    assert r["herramienta"] == "proveedores_top"
    assert len(r["datos"]) > 0


def test_explicar_un_caso():
    rojo = _b[_b["nivel"] == "ROJO"].iloc[0]["id_siniestro"]
    r = responder(f"¿por qué {rojo} es de alto riesgo?", _b)
    assert r["herramienta"] == "explicar"
    assert len(r["datos"]["contribuciones"]) > 0


def test_resumen_ejecutivo():
    r = responder("dame un resumen ejecutivo de los casos críticos", _b)
    assert r["herramienta"] == "resumen_ejecutivo"
    assert r["datos"]["total"] > 0


def test_aviso_presente():
    r = responder("recomienda qué revisar primero", _b)
    assert "no acusaciones" in r["aviso"]


# --- API ---
client = TestClient(app)


def test_endpoint_preguntar():
    resp = client.post("/api/preguntar", json={"pregunta": "¿qué proveedores concentran las alertas?"})
    assert resp.status_code == 200
    j = resp.json()
    assert "respuesta" in j and "datos" in j and "aviso" in j
    assert j["herramienta"] == "proveedores_top"

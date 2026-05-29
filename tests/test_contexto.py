"""Tests del contexto del caso: resumen en lenguaje natural + casos vinculados."""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_detalle_incluye_resumen_natural():
    rojo = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    d = client.get(f"/api/casos/{rojo}").json()
    assert "resumen" in d and isinstance(d["resumen"], str)
    # el párrafo menciona el nivel y la recomendación
    assert "ROJO" in d["resumen"] and "Recomendación" in d["resumen"]
    assert len(d["resumen"]) > 40


def test_vinculos_estructura():
    rojo = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    v = client.get(f"/api/casos/{rojo}/vinculos").json()
    for grupo in ("mismo_proveedor", "mismo_asegurado", "mismo_conductor", "misma_placa", "narrativa_similar"):
        assert grupo in v and isinstance(v[grupo], list)
    # el propio caso nunca aparece como vínculo
    for grupo in v.values():
        if isinstance(grupo, list):
            assert all(it.get("id_siniestro") != rojo for it in grupo)


def test_vinculos_mismo_proveedor_coherente():
    # un caso de un ring comparte proveedor con otros -> debe traer vínculos
    casos = client.get("/api/casos?limit=300").json()["casos"]
    objetivo = next((c for c in casos if c["nivel"] == "ROJO"), casos[0])
    v = client.get(f"/api/casos/{objetivo['id_siniestro']}/vinculos").json()
    for it in v["mismo_proveedor"]:
        assert "score" in it and "nivel" in it and "monto_reclamado" in it


def test_vinculos_404():
    assert client.get("/api/casos/NO_EXISTE/vinculos").status_code == 404

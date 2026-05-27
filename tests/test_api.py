"""Tests de la API (E3/#7) con TestClient."""
from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_resumen():
    r = client.get("/api/resumen").json()
    assert r["total"] > 0
    assert "ROJO" in r["por_nivel"]
    assert "NO es una acusación" in r["aviso"]


def test_casos_paginado_y_ordenado():
    r = client.get("/api/casos?limit=10").json()
    assert len(r["casos"]) == 10
    scores = [c["score"] for c in r["casos"]]
    assert scores == sorted(scores, reverse=True)


def test_casos_filtra_por_nivel():
    r = client.get("/api/casos?nivel=ROJO&limit=5").json()
    assert all(c["nivel"] == "ROJO" for c in r["casos"])


def test_detalle_con_evidencia():
    rojo = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    d = client.get(f"/api/casos/{rojo}").json()
    assert d["nivel"] == "ROJO"
    assert len(d["contribuciones"]) > 0
    assert "NO es una acusación" in d["aviso"]


def test_detalle_404():
    assert client.get("/api/casos/NO_EXISTE").status_code == 404

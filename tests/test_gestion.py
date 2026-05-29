"""Tests de la cola de trabajo del analista: estados de gestión + filtros/búsqueda."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.ingestion import db, models

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limpiar():
    yield
    models.Feedback.__table__.drop(db.get_engine(), checkfirst=True)
    client.post("/api/dataset/reset")


def _primer_caso():
    return client.get("/api/casos?limit=1").json()["casos"][0]


# --- Estados de gestión ----------------------------------------------------- #
def test_set_estado_y_filtra():
    sid = _primer_caso()["id_siniestro"]
    r = client.post(f"/api/casos/{sid}/estado", json={"estado": "escalado"})
    assert r.status_code == 200, r.text
    assert r.json()["feedback"]["estado"] == "escalado"
    # aparece al filtrar por estado
    ids = [c["id_siniestro"] for c in client.get("/api/casos?estado=escalado&limit=50").json()["casos"]]
    assert sid in ids
    # se refleja en el detalle
    assert client.get(f"/api/casos/{sid}").json()["feedback"]["estado"] == "escalado"


def test_estado_invalido_400():
    sid = _primer_caso()["id_siniestro"]
    assert client.post(f"/api/casos/{sid}/estado", json={"estado": "xxx"}).status_code == 400


def test_estado_404():
    assert client.post("/api/casos/NO_EXISTE/estado", json={"estado": "cerrado"}).status_code == 404


def test_feedback_autoavanza_a_en_revision():
    sid = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    r = client.post(f"/api/casos/{sid}/feedback", json={"veredicto": "confirmado"})
    assert r.json()["feedback"]["estado"] == "en_revision"


def test_resumen_por_estado():
    sid = _primer_caso()["id_siniestro"]
    client.post(f"/api/casos/{sid}/estado", json={"estado": "escalado"})
    res = client.get("/api/resumen").json()
    assert res["por_estado"]["escalado"] >= 1
    suma = sum(res["por_estado"].values())
    assert suma == res["total"]          # toda la bandeja queda clasificada por estado


# --- Filtros / búsqueda ----------------------------------------------------- #
def test_filtro_por_ramo_y_monto():
    r = client.get("/api/casos?ramo=Vehículos&monto_min=10000&limit=100").json()
    assert all(c["ramo"] == "Vehículos" and c["monto_reclamado"] >= 10000 for c in r["casos"])


def test_busqueda_por_id():
    sid = _primer_caso()["id_siniestro"]
    r = client.get(f"/api/casos?q={sid}&limit=50").json()
    assert any(c["id_siniestro"] == sid for c in r["casos"])


def test_orden_por_impacto():
    casos = client.get("/api/casos?orden=impacto&limit=10").json()["casos"]
    ve = [c["score"] * c["monto_reclamado"] for c in casos]
    assert ve == sorted(ve, reverse=True)

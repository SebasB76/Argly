"""Tests del human-in-the-loop: feedback del analista + reentrenamiento."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.ingestion import db, models, store

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limpiar():
    """Deja la DB compartida en sintético y sin feedback para no contaminar otros tests."""
    yield
    engine = db.get_engine()
    models.Feedback.__table__.drop(engine, checkfirst=True)
    client.post("/api/dataset/reset")


def _un_rojo() -> str:
    return client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]


def test_feedback_persiste_y_se_refleja_en_detalle():
    sid = _un_rojo()
    r = client.post(f"/api/casos/{sid}/feedback", json={"veredicto": "confirmado", "nota": "revisado"})
    assert r.status_code == 200, r.text
    assert r.json()["resumen"]["por_veredicto"]["confirmado"] == 1
    d = client.get(f"/api/casos/{sid}").json()
    assert d["feedback"]["veredicto"] == "confirmado"


def test_feedback_404_caso_inexistente():
    assert client.post("/api/casos/NO_EXISTE/feedback", json={"veredicto": "confirmado"}).status_code == 404


def test_feedback_veredicto_invalido_400():
    sid = _un_rojo()
    assert client.post(f"/api/casos/{sid}/feedback", json={"veredicto": "xxx"}).status_code == 400


def test_reentrenar_devuelve_metricas_antes_despues():
    # marca un par de casos como señal de entrenamiento
    casos = client.get("/api/casos?limit=4").json()["casos"]
    client.post(f"/api/casos/{casos[0]['id_siniestro']}/feedback", json={"veredicto": "confirmado"})
    client.post(f"/api/casos/{casos[1]['id_siniestro']}/feedback", json={"veredicto": "falso_positivo"})
    r = client.post("/api/modelo/reentrenar").json()
    assert r["ok"] is True
    assert r["feedback_aplicado"] >= 1
    # dataset sintético es híbrido -> hay métricas antes/después comparables
    assert r["antes"] is not None and r["despues"] is not None
    assert "auc_hibrido" in r["antes"] and "mejora" in r

"""Tests de la bitácora del caso: notas libres + historial automático de cambios."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.ingestion import db, models

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limpiar():
    yield
    eng = db.get_engine()
    models.Bitacora.__table__.drop(eng, checkfirst=True)
    models.Feedback.__table__.drop(eng, checkfirst=True)
    client.post("/api/dataset/reset")


def _un_caso():
    return client.get("/api/casos?limit=1").json()["casos"][0]["id_siniestro"]


def test_bitacora_vacia_al_inicio():
    assert client.get(f"/api/casos/{_un_caso()}/bitacora").json()["bitacora"] == []


def test_agregar_nota_aparece_en_bitacora():
    sid = _un_caso()
    r = client.post(f"/api/casos/{sid}/nota", json={"texto": "Llamé al asegurado, no contesta"})
    assert r.status_code == 200, r.text
    hist = r.json()["bitacora"]
    assert hist[-1]["tipo"] == "nota"
    assert "no contesta" in hist[-1]["texto"]


def test_veredicto_y_estado_se_registran_en_bitacora():
    sid = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    client.post(f"/api/casos/{sid}/feedback", json={"veredicto": "confirmado", "nota": "evidencia clara"})
    client.post(f"/api/casos/{sid}/estado", json={"estado": "escalado"})
    hist = client.get(f"/api/casos/{sid}/bitacora").json()["bitacora"]
    tipos = [e["tipo"] for e in hist]
    assert "veredicto" in tipos and "estado" in tipos
    ev = next(e for e in hist if e["tipo"] == "veredicto")
    assert ev["valor"] == "confirmado"
    est = next(e for e in hist if e["tipo"] == "estado")
    assert est["valor"] == "escalado"
    # orden cronológico (ids crecientes)
    assert [e["id"] for e in hist] == sorted(e["id"] for e in hist)


def test_nota_vacia_400():
    assert client.post(f"/api/casos/{_un_caso()}/nota", json={"texto": "   "}).status_code == 400


def test_nota_404():
    assert client.post("/api/casos/NO_EXISTE/nota", json={"texto": "x"}).status_code == 404

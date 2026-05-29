"""Tests del checklist de investigación y del tablero 'Mi trabajo'."""
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
    for m in (models.Checklist, models.Bitacora, models.Feedback):
        m.__table__.drop(eng, checkfirst=True)
    client.post("/api/dataset/reset")


def _rojo():
    return client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]


# --- Checklist -------------------------------------------------------------- #
def test_checklist_tiene_pasos_base():
    c = client.get(f"/api/casos/{_rojo()}/checklist").json()
    claves = [p["clave"] for p in c["pasos"]]
    assert {"doc", "asegurado", "proveedor"}.issubset(set(claves))
    assert c["completados"] == 0 and c["listo_para_escalar"] is False


def test_checklist_toggle_y_listo_para_escalar():
    sid = _rojo()
    # marca todos los pasos requeridos
    pasos = client.get(f"/api/casos/{sid}/checklist").json()["pasos"]
    for p in pasos:
        if p["requerido"]:
            r = client.post(f"/api/casos/{sid}/checklist", json={"clave": p["clave"], "hecho": True}).json()
    assert r["listo_para_escalar"] is True
    assert r["requeridos_hechos"] == r["requeridos"]
    # desmarcar uno lo vuelve a dejar incompleto
    r2 = client.post(f"/api/casos/{sid}/checklist", json={"clave": "doc", "hecho": False}).json()
    assert r2["listo_para_escalar"] is False


# --- Mi trabajo ------------------------------------------------------------- #
def test_mi_trabajo_estructura():
    r = client.get("/api/mi-trabajo").json()
    for k in ("total", "revisados", "por_estado", "por_veredicto", "monto_confirmado",
              "pendientes_rojos", "pendientes_top", "proveedores_top", "actividad_reciente"):
        assert k in r
    assert sum(r["por_estado"].values()) == r["total"]


def test_mi_trabajo_refleja_gestion_y_actividad():
    sid = _rojo()
    client.post(f"/api/casos/{sid}/feedback", json={"veredicto": "confirmado"})
    client.post(f"/api/casos/{sid}/estado", json={"estado": "escalado"})
    r = client.get("/api/mi-trabajo").json()
    assert r["por_veredicto"]["confirmado"] >= 1
    assert r["por_estado"]["escalado"] >= 1
    assert r["revisados"] >= 1
    # la actividad reciente trae los eventos recién creados
    assert any(e["id_siniestro"] == sid for e in r["actividad_reciente"])

"""Tests del mapa de calor geográfico por ciudad."""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.main import app
from src import config

client = TestClient(app)


def test_mapa_estructura_y_coordenadas():
    r = client.get("/api/mapa").json()
    assert r["total"] > 0
    assert r["ciudades"], "debe haber al menos una ciudad"
    # las ciudades sintéticas son del catálogo -> todas con coordenadas
    assert r["con_coordenadas"] == len(r["ciudades"])
    c0 = r["ciudades"][0]
    for k in ("ciudad", "n", "rojos", "amarillos", "verdes", "alertas", "tasa_alerta", "lat", "lng"):
        assert k in c0
    # coherencia: alertas = rojos + amarillos, y <= n
    assert c0["alertas"] == c0["rojos"] + c0["amarillos"]
    assert c0["alertas"] <= c0["n"]


def test_mapa_ordenado_por_alertas_desc():
    r = client.get("/api/mapa").json()
    alertas = [c["alertas"] for c in r["ciudades"]]
    assert alertas == sorted(alertas, reverse=True)


def test_mapa_bbox_cubre_catalogo():
    r = client.get("/api/mapa").json()
    bbox = r["bbox"]
    lats = [v[0] for v in config.CIUDADES.values()]
    assert bbox["lat_min"] == min(lats) and bbox["lat_max"] == max(lats)

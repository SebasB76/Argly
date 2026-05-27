"""Tests de scoreo de un siniestro NUEVO en vivo (POST /api/scorear) — 3ª prueba de fuego."""
from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def _scorear(**kw):
    return client.post("/api/scorear", json=kw).json()


def test_borde_vigencia_a_24h():
    # Siniestro al día siguiente de contratar, robo reportado tarde, monto casi total
    r = _scorear(dias_desde_inicio_poliza=1, cobertura="Robo", dias_entre_ocurrencia_reporte=6,
                 monto_reclamado=14500, suma_asegurada=15000)
    reglas = [c["regla"] for c in r["contribuciones"]]
    assert any("Borde de vigencia" in x for x in reglas)
    assert r["nivel"] in {"AMARILLO", "ROJO"}


def test_gate_lista_fuerza_rojo():
    r = _scorear(proveedor_en_lista=True)
    assert r["nivel"] == "ROJO" and r["gate"] is True


def test_caso_limpio_no_es_rojo():
    r = _scorear(dias_desde_inicio_poliza=150, cobertura="Choque", dias_entre_ocurrencia_reporte=1,
                 monto_reclamado=1500, suma_asegurada=20000, historial_siniestros_asegurado=1)
    assert r["gate"] is False
    assert r["nivel"] in {"VERDE", "AMARILLO"}


def test_respuesta_completa():
    r = _scorear()
    assert "probabilidad_ml" in r and 0.0 <= r["probabilidad_ml"] <= 1.0
    assert "no es una acusación" in r["aviso"].lower()
    assert "recomendacion" in r

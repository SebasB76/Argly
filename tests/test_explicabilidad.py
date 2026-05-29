"""Tests de Explicabilidad y Ética: análisis de sesgo + explicación contrafactual."""
from __future__ import annotations

from fastapi.testclient import TestClient

from src.app.main import app
from src.explicabilidad.contrafactual import contrafactual

client = TestClient(app)


# --- Sesgo / equidad -------------------------------------------------------- #
def test_sesgo_estructura_y_metricas():
    r = client.get("/api/sesgo").json()
    assert r["hay_etiquetas"] is True            # dataset sintético tiene etiquetas
    for attr in ("ciudad", "segmento", "canal_venta", "ramo"):
        assert attr in r["atributos"]
        grupos = r["atributos"][attr]["grupos"]
        assert grupos and all(0.0 <= g["tasa_alerta"] <= 1.0 for g in grupos)
    # la disparidad (regla 4/5) se mide sobre la tasa de alerta (selección)
    assert r["atributos"]["ciudad"]["metrica_disparidad"] == "tasa_alerta"
    # con etiquetas, además se reporta el falso positivo por grupo como contexto
    assert any(g["tasa_falsos_positivos"] is not None for g in r["atributos"]["ramo"]["grupos"])


def test_sesgo_veredicto_paridad():
    r = client.get("/api/sesgo").json()
    for v in r["atributos"].values():
        if v["veredicto"] is not None:
            assert v["veredicto"] in ("equitativo", "revisar")
            assert 0.0 <= v["disparidad"] <= 1.0


# --- Contrafactual ---------------------------------------------------------- #
def test_contrafactual_unidad_quita_gate_y_llega_a_verde():
    contribs = [
        {"regla": "RF-01 Pérdida Total por Robo (PTxRB)", "puntos": 10, "evidencia": "", "gate": True},
        {"regla": "Borde de vigencia", "puntos": 8, "evidencia": "", "gate": False},
        {"regla": "Reporte tardío", "puntos": 5, "evidencia": "", "gate": False},
    ]
    cf = contrafactual(contribs)
    assert cf["ya_verde"] is False
    # debe incluir el gate entre los cambios y proyectar VERDE
    assert any(c["gate"] for c in cf["cambios"])
    assert cf["nivel_proyectado"] == "VERDE" and cf["alcanzable"] is True
    assert all("accion" in c for c in cf["cambios"])


def test_contrafactual_caso_verde_no_requiere_cambios():
    cf = contrafactual([{"regla": "Reporte tardío", "puntos": 3, "evidencia": "", "gate": False}])
    assert cf["ya_verde"] is True and cf["cambios"] == []


def test_contrafactual_endpoint_en_caso_rojo():
    rojo = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    cf = client.get(f"/api/casos/{rojo}/contrafactual").json()
    assert cf["nivel"] == "ROJO"
    assert len(cf["cambios"]) >= 1
    assert "score_proyectado" in cf and "resumen" in cf

"""Tests del dataset variable (DB como fuente de verdad): normalizar, importar
(reemplazar/anexar) y reset, vía la capa `store` y la API."""
from __future__ import annotations

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.app.main import app
from src.ingestion import store

client = TestClient(app)


@pytest.fixture(autouse=True)
def _restaurar_sintetico():
    """Cada test deja la DB compartida de nuevo en el sintético (evita contaminar
    a los demás tests de API que esperan el dataset de demo)."""
    yield
    client.post("/api/dataset/reset")


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode()


def _mini_dataset(n: int = 6) -> dict[str, pd.DataFrame]:
    sin = pd.DataFrame([{
        "id_siniestro": f"X{i:03d}", "id_poliza": "POLX", "id_asegurado": f"AX{i % 3}",
        "id_proveedor": "PX", "cobertura": "Choque", "ramo": "Vehículos",
        "monto_reclamado": 1000 * (i + 1), "fecha_ocurrencia": "2024-03-01",
        "fecha_reporte": "2024-03-02",
    } for i in range(n)])
    pol = pd.DataFrame([{
        "id_poliza": "POLX", "id_asegurado": "AX0", "ramo": "Vehículos",
        "fecha_inicio": "2024-01-01", "fecha_fin": "2024-12-31", "suma_asegurada": 20000,
    }])
    return {"siniestros": sin, "polizas": pol}


# --- store.normalizar ------------------------------------------------------- #
def test_normalizar_completa_tablas_y_derivados():
    dfs = store.normalizar(_mini_dataset())
    # las 6 tablas existen aunque solo se pasaron 2
    assert set(dfs) == set(store.NOMBRES)
    s = dfs["siniestros"]
    # campo derivado calculado a partir de las fechas de la póliza
    assert (s["dias_desde_inicio_poliza"] == 60).all()  # 1 ene -> 1 mar
    # historial = nº de siniestros del asegurado
    assert s["historial_siniestros_asegurado"].max() >= 1
    # split asignado (sin etiquetas -> reparto simple, pero hay test)
    assert s["split"].isin(["train", "test"]).all()


def test_round_trip_db(tmp_path):
    url = f"sqlite:///{(tmp_path / 'rt.db').as_posix()}"
    store.reemplazar(_mini_dataset(8), url=url)
    dfs = store.cargar_dfs(url=url)
    assert len(dfs["siniestros"]) == 8
    assert store.resumen(url=url)["origen"] == "importado"


def test_admite_hibrido_requiere_dos_clases(tmp_path):
    dfs = store.normalizar(_mini_dataset())  # sin etiquetas -> una sola clase
    assert store.admite_hibrido(dfs) is False


# --- API: estado / importar / reset ----------------------------------------- #
def test_estado_inicial_sintetico():
    d = client.get("/api/dataset").json()
    assert d["origen"] == "sintetico"
    assert d["n_siniestros"] > 0
    assert d["modo"] == "hibrido"
    assert "siniestros" in d["columnas_esperadas"]


def test_importar_reemplaza():
    ds = _mini_dataset(5)
    files = {"siniestros": ("siniestros.csv", _csv(ds["siniestros"]), "text/csv"),
             "polizas": ("polizas.csv", _csv(ds["polizas"]), "text/csv")}
    r = client.post("/api/dataset/importar", data={"modo": "replace"}, files=files)
    assert r.status_code == 200, r.text
    d = r.json()["dataset"]
    assert d["origen"] == "importado"
    assert d["n_siniestros"] == 5
    # la bandeja se reconstruye sobre el dataset nuevo
    casos = client.get("/api/casos?limit=50").json()
    assert casos["total"] == 5


def test_importar_anexa():
    client.post("/api/dataset/importar", data={"modo": "replace"},
                files={"siniestros": ("s.csv", _csv(_mini_dataset(4)["siniestros"]), "text/csv"),
                       "polizas": ("p.csv", _csv(_mini_dataset()["polizas"]), "text/csv")})
    nuevos = _mini_dataset(4)["siniestros"].copy()
    nuevos["id_siniestro"] = [f"N{i}" for i in range(4)]
    r = client.post("/api/dataset/importar", data={"modo": "append"},
                    files={"siniestros": ("s.csv", _csv(nuevos), "text/csv")})
    assert r.status_code == 200, r.text
    assert r.json()["dataset"]["n_siniestros"] == 8


def test_importar_sin_siniestros_400():
    r = client.post("/api/dataset/importar", data={"modo": "replace"},
                    files={"polizas": ("p.csv", _csv(_mini_dataset()["polizas"]), "text/csv")})
    assert r.status_code == 400


def test_reset_vuelve_a_sintetico():
    client.post("/api/dataset/importar", data={"modo": "replace"},
                files={"siniestros": ("s.csv", _csv(_mini_dataset(3)["siniestros"]), "text/csv")})
    r = client.post("/api/dataset/reset").json()
    assert r["dataset"]["origen"] == "sintetico"
    assert r["dataset"]["n_siniestros"] > 100

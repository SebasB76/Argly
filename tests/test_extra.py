"""Tests de los hallazgos implementados: señales nuevas (conductor, solo RC, sin tercero,
RF-01 PTxRB), Pareto 80%, simulación de ahorro, SHAP y NLP de entidades/resúmenes."""
from fastapi.testclient import TestClient

from src.app.main import app
from src.ai_agent import tools
from src.features.build_features import construir_features
from src.ingestion.generate_synthetic import generar
from src.models.ml_model import entrenar, explicacion_global, explicacion_local
from src.nlp.narrative import extraer_entidades, resumen_narrativas
from src.pipeline import construir_bandeja
from src.scoring.score import puntuar_features

_dfs = generar(seed=42)
_S = _dfs["siniestros"].reset_index(drop=True)
_F = construir_features(_dfs)
_P = puntuar_features(_F)
_B = construir_bandeja(_dfs)
client = TestClient(app)


# --- Generador: patrones nuevos plantados ---

def test_patrones_nuevos_presentes():
    for p in ["frecuencia_conductor", "frecuencia_rc", "sin_tercero", "ptxrb"]:
        assert (_S["patron"] == p).sum() > 0, p


def test_campos_sugeridos_asegurados_y_proveedores():
    for c in ["numero_polizas", "reclamos_ultimos_12_meses", "mora_actual"]:
        assert c in _dfs["asegurados"].columns, c
    for c in ["reclamos_asociados", "monto_promedio_reclamado", "porcentaje_casos_observados"]:
        assert c in _dfs["proveedores"].columns, c


# --- Features nuevas ---

def test_features_nuevas_existen_sin_nulos():
    for c in ["freq_conductor", "freq_solo_rc", "evento_sin_tercero", "es_ptxrb", "es_solo_rc"]:
        assert c in _F.columns, c
    assert _F[["freq_conductor", "freq_solo_rc", "evento_sin_tercero", "es_ptxrb"]].isnull().sum().sum() == 0


def test_freq_conductor_dispara_en_patron():
    m = (_S["patron"] == "frecuencia_conductor").values
    assert (_F.loc[m, "freq_conductor"] >= 3).all()


def test_sin_tercero_marca_evento():
    m = (_S["patron"] == "sin_tercero").values
    assert _F.loc[m, "evento_sin_tercero"].all()


def test_ptxrb_marca_feature():
    m = (_S["patron"] == "ptxrb").values
    assert _F.loc[m, "es_ptxrb"].all()


# --- Reglas / scoring ---

def test_ptxrb_es_gate_rojo():
    m = (_S["patron"] == "ptxrb").values
    assert (_P.loc[m, "nivel"] == "ROJO").all()
    assert (_P.loc[m, "gate"]).all()


def test_sin_tercero_suma_contribucion():
    m = (_S["patron"] == "sin_tercero").values
    reglas = _P.loc[m, "contribuciones"].iloc[0]
    assert any("sin tercero" in c["regla"].lower() for c in reglas)


def test_conductor_suma_contribucion():
    m = (_S["patron"] == "frecuencia_conductor").values
    reglas = _P.loc[m, "contribuciones"].iloc[0]
    assert any("conductor" in c["regla"].lower() for c in reglas)


# --- Pareto 80% (prueba de fuego del jurado) ---

def test_pareto_alcanza_objetivo():
    r = tools.proveedores_pareto(_B, objetivo=0.8, solo_rojos=True)
    assert r["objetivo_pct"] == 80
    assert r["nivel"] == "rojas"
    assert r["total_alertas"] > 0
    assert 0 < r["n_proveedores_concentran"] <= r["total_proveedores_con_alertas"]
    assert r["proveedores"][-1]["pct_acumulado"] >= 80
    assert "alertas rojas" in r["interpretacion"]


def test_pareto_admite_porcentaje_entero():
    r = tools.proveedores_pareto(_B, objetivo=80)
    assert r["objetivo_pct"] == 80


# --- Simulación de ahorro ---

def test_simulacion_ahorro_campos():
    a = tools.simulacion_ahorro(_B)
    for k in ["casos_rojos", "monto_expuesto_rojo", "ahorro_por_fraude_evitado",
              "ahorro_operativo_priorizacion", "ahorro_estimado_total", "supuestos"]:
        assert k in a, k
    assert a["ahorro_estimado_total"] >= a["ahorro_por_fraude_evitado"]


# --- SHAP / explicabilidad ---

def test_explicacion_global_local():
    m, _ = entrenar(_F)
    g = explicacion_global(m, _F)
    assert g["metodo"] in ("shap", "feature_importances")
    assert len(g["importancias"]) > 0
    fila = {c: _F.iloc[0][c] for c in _F.columns}
    loc = explicacion_local(m, fila)
    assert len(loc["factores"]) > 0
    assert "feature" in loc["factores"][0]


# --- NLP: entidades + resúmenes ---

def test_extraer_entidades():
    e = extraer_entidades("El vehículo PBA-1234 sufrió daños. Expediente 123456. Av. Amazonas.")
    assert "PBA-1234" in e["placas"]
    assert any("123456" in x for x in e["expedientes"])
    assert "Av. Amazonas" in e["vias"]


def test_resumen_narrativas_detecta_clon():
    grupos = resumen_narrativas(_S, top=5)
    assert len(grupos) > 0
    assert grupos[0]["n_reclamos"] > 1


# --- API: endpoints nuevos ---

def test_api_resumen_incluye_ahorro():
    r = client.get("/api/resumen").json()
    assert "ahorro_estimado" in r and r["ahorro_estimado"] >= 0


def test_api_pareto():
    r = client.get("/api/proveedores-pareto?objetivo=0.8").json()
    assert r["objetivo_pct"] == 80
    assert r["n_proveedores_concentran"] >= 1


def test_api_ahorro():
    r = client.get("/api/ahorro").json()
    assert r["ahorro_estimado_total"] >= 0
    assert "no es una acusación" in r["aviso"].lower()


def test_api_importancias():
    r = client.get("/api/modelo/importancias").json()
    assert r["metodo"] in ("shap", "feature_importances")
    assert len(r["importancias"]) > 0


def test_api_entidades():
    rojo = client.get("/api/casos?nivel=ROJO&limit=1").json()["casos"][0]["id_siniestro"]
    r = client.get(f"/api/casos/{rojo}/entidades").json()
    assert "entidades" in r and "placas" in r["entidades"]


def test_api_narrativas_resumen():
    r = client.get("/api/narrativas/resumen").json()
    assert "grupos" in r


# --- Scoreo en vivo: nuevas reglas exponibles ---

def test_scorear_ptxrb_gate_rojo():
    r = client.post("/api/scorear", json={"cobertura": "Robo", "perdida_total": True,
                                          "monto_reclamado": 14500, "suma_asegurada": 15000}).json()
    assert r["nivel"] == "ROJO" and r["gate"] is True
    assert any("PTxRB" in c["regla"] for c in r["contribuciones"])


def test_scorear_incluye_factores_modelo():
    r = client.post("/api/scorear", json={}).json()
    assert "factores_modelo" in r
    assert r["factores_modelo"]["metodo"] in ("shap", "feature_importances")
    assert len(r["factores_modelo"]["factores"]) > 0


def test_scorear_sin_tercero_suma():
    r = client.post("/api/scorear", json={"cobertura": "Choque", "tercero_identificado": False}).json()
    assert any("sin tercero" in c["regla"].lower() for c in r["contribuciones"])

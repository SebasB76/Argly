"""Tests de reglas + scoring (E1/#4/#5): bordes de semáforo, gates y separación fraude/legítimo."""
from src.scoring.score import puntuar, puntuar_features
from src.rules.fraud_rules import Contribucion
from src.features.build_features import construir_features
from src.ingestion.generate_synthetic import generar


# --- Política de scoring (unitario) ---

def test_vacio_es_verde():
    r = puntuar([])
    assert r["score"] == 0 and r["nivel"] == "VERDE"


def test_bordes_semaforo():
    assert puntuar([Contribucion("x", 40, "e")])["nivel"] == "VERDE"
    assert puntuar([Contribucion("x", 41, "e")])["nivel"] == "AMARILLO"
    assert puntuar([Contribucion("x", 76, "e")])["nivel"] == "ROJO"


def test_tope_100():
    assert puntuar([Contribucion("x", 200, "e")])["score"] == 100


def test_gate_fuerza_rojo():
    r = puntuar([Contribucion("g", 10, "e", gate=True)])
    assert r["nivel"] == "ROJO" and r["score"] >= 76 and r["gate"] is True


def test_desglose_es_lista_de_contribuciones():
    r = puntuar([Contribucion("Borde de vigencia", 8, "evidencia")])
    assert r["contribuciones"][0]["regla"] == "Borde de vigencia"
    assert r["contribuciones"][0]["puntos"] == 8


# --- Integración con datos sintéticos ---

_dfs = generar(seed=42)
_S = _dfs["siniestros"].reset_index(drop=True)
_P = puntuar_features(construir_features(_dfs))


def test_score_en_rango():
    assert _P["score"].between(0, 100).all()


def test_ring_es_rojo():
    m = (_S["patron"] == "red_proveedor").values
    assert (_P.loc[m, "nivel"] == "ROJO").all()


def test_doc_inconsistente_es_rojo():
    m = (_S["patron"] == "doc_inconsistente").values
    assert (_P.loc[m, "nivel"] == "ROJO").all()


def test_fraude_puntua_mas_que_legitimo():
    et = _S["etiqueta_fraude_simulada"].values
    media_fraude = _P.loc[et == 1, "score"].mean()
    media_legit = _P.loc[et == 0, "score"].mean()
    assert media_fraude > media_legit + 5

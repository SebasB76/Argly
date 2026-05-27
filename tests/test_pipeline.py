"""Tests del pipeline E1 (#6): la bandeja prioriza y separa fraude."""
from src.pipeline import construir_bandeja
from src.ingestion.generate_synthetic import generar

_dfs = generar(seed=42)
_B = construir_bandeja(_dfs)


def test_misma_cantidad():
    assert len(_B) == len(_dfs["siniestros"])


def test_ordenada_por_score_desc():
    v = _B["score"].values
    assert (v[:-1] >= v[1:]).all()


def test_columnas_clave():
    for c in ["id_siniestro", "score", "nivel", "gate", "n_alertas", "motivo_principal"]:
        assert c in _B.columns


def test_niveles_validos():
    assert set(_B["nivel"].unique()) <= {"VERDE", "AMARILLO", "ROJO"}


def test_prioriza_fraude_en_top():
    # los 100 casos de mayor score deben ser mayoritariamente fraude (priorización útil)
    assert _B.head(100)["etiqueta_fraude_simulada"].mean() > 0.7

"""Tests de features (E1/#3): valida las variables de riesgo en los bordes."""
from src.ingestion.generate_synthetic import generar
from src.features.build_features import construir_features

_dfs = generar(seed=42)
S = _dfs["siniestros"].reset_index(drop=True)
F = construir_features(_dfs)


def _mask(patron):
    return (S["patron"] == patron).values


def test_sin_nulos():
    assert F.isnull().sum().sum() == 0


def test_misma_longitud():
    assert len(F) == len(S)


def test_ratio_monto_alto():
    m = _mask("monto_alto")
    assert m.sum() > 0
    assert (F.loc[m, "ratio_monto_suma"] >= 0.9).all()


def test_es_robo_en_demora():
    m = _mask("demora_robo")
    assert F.loc[m, "es_robo"].all()


def test_geo_imposible_distancia_grande():
    m = _mask("geo_imposible")
    assert (F.loc[m, "distancia_geo_km"] > 100).all()


def test_clima_inconsistente():
    m = _mask("clima_inconsistente")
    assert F.loc[m, "clima_inconsistente"].all()


def test_ring_proveedor_en_lista_y_frecuente():
    m = _mask("red_proveedor")
    assert F.loc[m, "proveedor_en_lista"].all()
    assert (F.loc[m, "freq_proveedor"] >= 5).all()


def test_narrativa_clonada_repetida():
    m = _mask("narrativa_clonada")
    assert (F.loc[m, "narrativa_repetidos"] > 1).all()


def test_doc_inconsistente_detectado():
    m = _mask("doc_inconsistente")
    assert F.loc[m, "doc_inconsistente"].all()

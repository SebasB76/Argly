"""Tests de ML + anomalías + métricas (E2/#9)."""
from sklearn.metrics import roc_auc_score

from src.ingestion.generate_synthetic import generar
from src.features.build_features import construir_features
from src.models.ml_model import entrenar
from src.anomaly.detector import detectar
from src.pipeline import construir_bandeja, evaluar_metricas

_dfs = generar(seed=42)
_F = construir_features(_dfs)


def test_modelo_auc_alto_en_test():
    _, prob = entrenar(_F)
    test = (_F["split"] == "test").values
    y = _F["etiqueta_fraude_simulada"].values[test]
    assert roc_auc_score(y, prob.values[test]) > 0.8


def test_anomalia_en_rango():
    a = detectar(_F)
    assert a.between(0, 1).all()


def test_hibrido_llena_amarillo():
    b = construir_bandeja(_dfs, hibrido=True)
    assert (b["nivel"] == "AMARILLO").sum() > 0
    assert set(b["nivel"].unique()) <= {"VERDE", "AMARILLO", "ROJO"}


def test_metricas_hibrido():
    m = evaluar_metricas(_dfs)
    assert m["auc_ml"] > 0.8
    assert m["auc_hibrido"] > 0.75
    assert m["auc_hibrido"] >= m["auc_reglas"] - 0.02   # el ML no degrada el ranking
    assert m["recall"] > 0.4

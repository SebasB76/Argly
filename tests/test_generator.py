"""Tests del generador sintético (E0): valida la integridad del ground-truth."""
from src.ingestion.generate_synthetic import generar, NARRATIVA_CLON

dfs = generar(seed=42)
S = dfs["siniestros"]


def _patron(p):
    return S[S["patron"] == p]


def test_tablas_presentes():
    for k in ["asegurados", "proveedores", "polizas", "vehiculos", "siniestros", "documentos"]:
        assert k in dfs and len(dfs[k]) > 0


def test_ambas_etiquetas_presentes():
    assert set(S["etiqueta_fraude_simulada"].unique()) == {0, 1}


def test_borde_vigencia():
    d = _patron("borde_vigencia")
    assert len(d) > 0
    assert (d["dias_desde_inicio_poliza"] <= 10).all()
    assert (d["etiqueta_fraude_simulada"] == 1).all()


def test_demora_robo():
    d = _patron("demora_robo")
    assert len(d) > 0
    assert (d["cobertura"] == "Robo").all()
    assert (d["dias_entre_ocurrencia_reporte"] > 2).all()


def test_frecuencia_asegurado():
    d = _patron("frecuencia_asegurado")
    assert len(d) > 0
    counts = S.groupby("id_asegurado").size()
    for aid in d["id_asegurado"].unique():
        assert counts[aid] >= 3


def test_narrativa_clonada():
    d = _patron("narrativa_clonada")
    assert len(d) > 0
    assert (d["descripcion"] == NARRATIVA_CLON).all()


def test_geo_imposible():
    d = _patron("geo_imposible")
    assert len(d) > 0
    assert (d["ciudad_ocurrencia"] != d["ciudad_taller"]).all()


def test_clima_inconsistente():
    d = _patron("clima_inconsistente")
    assert len(d) > 0
    assert (d["clima_declarado"] != d["clima_real"]).all()


def test_documentos_inconsistentes():
    assert dfs["documentos"]["inconsistencia_detectada"].sum() > 0


def test_rings_separados_train_test():
    rings = _patron("red_proveedor")
    assert {"train", "test"}.issubset(set(rings["split"].unique()))
    prov_train = set(rings[rings["split"] == "train"]["id_proveedor"])
    prov_test = set(rings[rings["split"] == "test"]["id_proveedor"])
    # el proveedor del ring de test no aparece en el ring de train (variante no vista)
    assert prov_train.isdisjoint(prov_test)


def test_split_no_vacio():
    assert (S["split"] == "train").sum() > 0
    assert (S["split"] == "test").sum() > 0


def test_reproducible():
    s2 = generar(seed=42)["siniestros"]
    assert len(s2) == len(S)
    assert int(s2["etiqueta_fraude_simulada"].sum()) == int(S["etiqueta_fraude_simulada"].sum())

"""Tests de carga a la base (E0/#2): verifica esquema + seed contra SQLite."""
from sqlalchemy import text

from src.ingestion.generate_synthetic import generar
from src.ingestion.seed import seed


def test_seed_carga_todas_las_tablas(tmp_path):
    dfs = generar(seed=42)
    url = f"sqlite:///{tmp_path / 'argly_test.db'}"
    engine = seed(url=url, dfs=dfs)
    with engine.connect() as c:
        for nombre in ["asegurados", "proveedores", "polizas", "vehiculos", "siniestros", "documentos"]:
            n = c.execute(text(f"SELECT COUNT(*) FROM {nombre}")).scalar()
            assert n == len(dfs[nombre]), f"{nombre}: {n} != {len(dfs[nombre])}"


def test_seed_preserva_fraude_y_split(tmp_path):
    url = f"sqlite:///{tmp_path / 'argly_test.db'}"
    engine = seed(url=url)
    with engine.connect() as c:
        fraude = c.execute(text("SELECT COUNT(*) FROM siniestros WHERE etiqueta_fraude_simulada = 1")).scalar()
        train = c.execute(text("SELECT COUNT(*) FROM siniestros WHERE split = 'train'")).scalar()
        test = c.execute(text("SELECT COUNT(*) FROM siniestros WHERE split = 'test'")).scalar()
    assert fraude > 0
    assert train > 0 and test > 0


def test_idempotente(tmp_path):
    """Reejecutar el seed no duplica (drop_all + create_all)."""
    url = f"sqlite:///{tmp_path / 'argly_test.db'}"
    seed(url=url)
    engine = seed(url=url)
    with engine.connect() as c:
        n = c.execute(text("SELECT COUNT(*) FROM siniestros")).scalar()
    assert n == 1390

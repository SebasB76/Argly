"""Tests del grafo de redes (E4): detecta los anillos plantados."""
from src.pipeline import construir_bandeja
from src.ingestion.generate_synthetic import generar
from src.graph.network import detectar_redes

_b = construir_bandeja(generar(seed=42))


def test_detecta_alguna_red():
    redes = detectar_redes(_b, min_siniestros=5)
    assert len(redes) >= 1


def test_red_concentrada_es_anillo():
    redes = detectar_redes(_b, min_siniestros=5)
    # un anillo = muchos siniestros concentrados en pocos proveedores
    assert any(r["n_siniestros"] >= 10 and r["n_proveedores"] <= 2 for r in redes)


def test_redes_ordenadas_por_monto():
    redes = detectar_redes(_b, min_siniestros=5)
    montos = [r["monto_total"] for r in redes]
    assert montos == sorted(montos, reverse=True)

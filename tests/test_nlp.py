"""Tests de NLP (E4): la similitud TF-IDF aísla las narrativas clonadas."""
from src.ingestion.generate_synthetic import generar
from src.nlp.narrative import pares_similares

_s = generar(seed=42)["siniestros"]
_clon = set(_s[_s["patron"] == "narrativa_clonada"]["id_siniestro"])


def test_encuentra_pares_similares():
    pares = pares_similares(_s, umbral=0.99)
    assert len(pares) > 0


def test_pares_son_clonados():
    pares = pares_similares(_s, umbral=0.99)
    # debe existir al menos un par donde AMBOS son narrativas clonadas
    assert any(p["a"] in _clon and p["b"] in _clon for p in pares)


def test_legitimos_no_dominan():
    # con narrativas legítimas diversas, los pares de alta similitud son clonados
    pares = pares_similares(_s, umbral=0.99)
    involucran_clon = sum(1 for p in pares if p["a"] in _clon or p["b"] in _clon)
    assert involucran_clon >= len(pares) * 0.5

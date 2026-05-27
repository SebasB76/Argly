"""Análisis NLP de narrativas (E4): similitud semántica vía TF-IDF + coseno.

Detecta descripciones casi idénticas entre reclamos (narrativas clonadas), incluso
si no son copia exacta. Responde la pregunta del jurado: "¿cómo detectan la
similitud entre dos narrativas?" -> vectorización TF-IDF + similitud de coseno.
"""
from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def pares_similares(siniestros, umbral: float = 0.9, max_pares: int = 100):
    """Pares de siniestros con similitud textual >= umbral, ordenados desc."""
    s = siniestros.reset_index(drop=True)
    textos = s["descripcion"].fillna("").tolist()
    if len(textos) < 2:
        return []
    X = TfidfVectorizer().fit_transform(textos)
    sim = cosine_similarity(X)
    np.fill_diagonal(sim, 0.0)
    sim = np.triu(sim)                      # solo mitad superior (sin duplicar pares)
    pares = []
    for i, j in np.argwhere(sim >= umbral):
        pares.append({"a": s.loc[int(i), "id_siniestro"],
                      "b": s.loc[int(j), "id_siniestro"],
                      "similitud": round(float(sim[i, j]), 3)})
    pares.sort(key=lambda x: -x["similitud"])
    return pares[:max_pares]

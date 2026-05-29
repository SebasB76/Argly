"""Análisis NLP de narrativas (E4): similitud semántica vía TF-IDF + coseno.

Detecta descripciones casi idénticas entre reclamos (narrativas clonadas), incluso
si no son copia exacta. Responde la pregunta del jurado: "¿cómo detectan la
similitud entre dos narrativas?" -> vectorización TF-IDF + similitud de coseno.
"""
from __future__ import annotations

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Vías conocidas para el reconocimiento de entidades (NER ligero, basado en reglas).
_VIAS = ["Av. Amazonas", "Av. 6 de Diciembre", "Av. de las Américas", "Vía a Daule",
         "Av. Naciones Unidas", "Av. Ordóñez Lasso", "Panamericana Sur"]


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


def similares_a(siniestros, id_siniestro: str, umbral: float = 0.8, top: int = 5):
    """Siniestros con narrativa más parecida a la de `id_siniestro` (coseno TF-IDF)."""
    s = siniestros.reset_index(drop=True)
    if id_siniestro not in set(s["id_siniestro"]):
        return []
    textos = s["descripcion"].fillna("").tolist()
    if len(textos) < 2:
        return []
    X = TfidfVectorizer().fit_transform(textos)
    i = int(s.index[s["id_siniestro"] == id_siniestro][0])
    sim = cosine_similarity(X[i], X).ravel()
    sim[i] = 0.0
    out = [{"id_siniestro": s.loc[int(j), "id_siniestro"], "similitud": round(float(sim[j]), 3)}
           for j in np.argsort(-sim) if sim[j] >= umbral]
    return out[:top]


def extraer_entidades(texto: str) -> dict:
    """Extracción de entidades de una narrativa (NER ligero basado en reglas).

    Devuelve placas, montos, horas, vías, expedientes y partes policiales hallados,
    para la sección 9 del reto ('extracción de entidades') sin dependencias pesadas.
    """
    t = texto or ""
    return {
        "placas": re.findall(r"\b[A-Z]{3}-\d{3,4}\b", t),
        "montos": re.findall(r"\$\s?\d[\d.,]*", t),
        "horas": re.findall(r"\b\d{1,2}h\d{2}\b", t),
        "vias": [v for v in _VIAS if v.lower() in t.lower()],
        "expedientes": re.findall(r"[Ee]xpediente\s+\d+", t),
        "partes_policiales": re.findall(r"parte policial N?\s*\d+", t, flags=re.IGNORECASE),
        "km": re.findall(r"\bkm\s+\d+\b", t, flags=re.IGNORECASE),
    }


def resumen_narrativas(siniestros, top: int = 5, min_grupo: int = 2):
    """Resume las narrativas repetidas: agrupa descripciones idénticas y reporta
    cuántos reclamos comparten cada 'molde' (coherencia/resúmenes, sección 9)."""
    s = siniestros
    grupos = []
    for descripcion, ids in s.groupby("descripcion")["id_siniestro"].agg(list).items():
        if len(ids) < min_grupo:
            continue
        resumen = descripcion if len(descripcion) <= 140 else descripcion[:140] + "…"
        grupos.append({"resumen": resumen, "n_reclamos": int(len(ids)), "ejemplos": list(ids[:5])})
    grupos.sort(key=lambda g: g["n_reclamos"], reverse=True)
    return grupos[:top]

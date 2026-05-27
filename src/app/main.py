"""API FastAPI (E3/#7): sirve la bandeja priorizada y el detalle explicable de cada caso.

Levantar:
    uvicorn src.app.main:app --reload
"""
from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.pipeline import construir_bandeja
from src.ai_agent.agent import responder

app = FastAPI(title="Argly API", version="0.1.0",
              description="Detección de posible fraude en siniestros. Alertas, no acusaciones.")

_BANDEJA = None


def _bandeja():
    """Construye la bandeja una sola vez (cache en memoria)."""
    global _BANDEJA
    if _BANDEJA is None:
        _BANDEJA = construir_bandeja()
    return _BANDEJA


CASO_COLS = ["id_siniestro", "score", "nivel", "gate", "motivo_principal", "n_alertas",
             "ramo", "cobertura", "sucursal", "monto_reclamado", "id_asegurado", "id_proveedor"]

AVISO = "ALERTA para revisión humana, NO es una acusación de fraude."


def _recomendacion(nivel: str) -> str:
    return {
        "ROJO": "Escalar a Unidad Antifraude para revisión especializada",
        "AMARILLO": "Escalar para revisión documental",
        "VERDE": "Continuar flujo normal",
    }.get(nivel, "")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/resumen")
def resumen():
    b = _bandeja()
    por_nivel = {k: int(v) for k, v in b["nivel"].value_counts().items()}
    monto_revision = float(b.loc[b["nivel"] != "VERDE", "monto_reclamado"].sum())
    return {
        "total": int(len(b)),
        "por_nivel": por_nivel,
        "monto_en_revision": round(monto_revision, 2),
        "aviso": AVISO,
    }


@app.get("/api/casos")
def casos(nivel: str | None = None, limit: int = 50, offset: int = 0):
    b = _bandeja()
    if nivel:
        b = b[b["nivel"] == nivel.upper()]
    page = b[CASO_COLS].iloc[offset:offset + limit]
    return {"total": int(len(b)), "casos": json.loads(page.to_json(orient="records"))}


@app.get("/api/casos/{id_siniestro}")
def caso(id_siniestro: str):
    b = _bandeja()
    row = b[b["id_siniestro"] == id_siniestro]
    if row.empty:
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    r = row.iloc[0]
    return {
        "id_siniestro": str(r["id_siniestro"]),
        "score": int(r["score"]),
        "nivel": str(r["nivel"]),
        "gate": bool(r["gate"]),
        "motivo_principal": str(r["motivo_principal"]),
        "ramo": str(r["ramo"]),
        "cobertura": str(r["cobertura"]),
        "sucursal": str(r["sucursal"]),
        "monto_reclamado": float(r["monto_reclamado"]),
        "id_asegurado": str(r["id_asegurado"]),
        "id_proveedor": str(r["id_proveedor"]),
        "contribuciones": r["contribuciones"],
        "recomendacion": _recomendacion(str(r["nivel"])),
        "aviso": AVISO,
    }


class Pregunta(BaseModel):
    pregunta: str


@app.post("/api/preguntar")
def preguntar(p: Pregunta):
    """Agente de IA: responde una pregunta en lenguaje natural sobre la bandeja."""
    return responder(p.pregunta, _bandeja())

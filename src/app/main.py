"""API FastAPI (E3/#7): sirve la bandeja priorizada y el detalle explicable de cada caso.

Levantar:
    uvicorn src.app.main:app --reload
"""
from __future__ import annotations

import json

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

# Carga .env al arrancar la app para que el proceso vea GEMINI_API_KEY/LLM_PROVIDER
load_dotenv(find_dotenv(), override=False)

from src.pipeline import construir_bandeja
from src.ingestion.generate_synthetic import generar
from src.graph.network import detectar_redes
from src.nlp.narrative import pares_similares
from src.ai_agent.agent import responder
from src.channels.pdf_dossier import generar_dossier
from src.channels import notify
from src.features.build_features import construir_features
from src.models.ml_model import entrenar, FEATURES, _X
from src.rules.fraud_rules import evaluar_reglas
from src.scoring.score import puntuar, contribucion_ml

app = FastAPI(title="Argly API", version="0.1.0",
              description="Detección de posible fraude en siniestros. Alertas, no acusaciones.")

_DFS = None
_BANDEJA = None
_MODELO = None


def _datos():
    """Genera los datos, entrena el modelo y construye la bandeja una vez (cache)."""
    global _DFS, _BANDEJA, _MODELO
    if _BANDEJA is None:
        _DFS = generar()
        _MODELO, _ = entrenar(construir_features(_DFS))
        _BANDEJA = construir_bandeja(_DFS)
    return _DFS, _BANDEJA


def _bandeja():
    return _datos()[1]


def _modelo():
    _datos()
    return _MODELO


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


def _detalle(id_siniestro: str) -> dict:
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


@app.get("/api/casos/{id_siniestro}")
def caso(id_siniestro: str):
    return _detalle(id_siniestro)


class Pregunta(BaseModel):
    pregunta: str


@app.post("/api/preguntar")
def preguntar(p: Pregunta):
    """Agente de IA: responde una pregunta en lenguaje natural sobre la bandeja."""
    return responder(p.pregunta, _bandeja())


@app.get("/api/redes")
def redes(min_siniestros: int = 5):
    """Anillos: proveedores que concentran siniestros sospechosos (análisis de redes)."""
    return {"redes": detectar_redes(_bandeja(), min_siniestros=min_siniestros), "aviso": AVISO}


@app.get("/api/narrativas-similares")
def narrativas(umbral: float = 0.95):
    """Pares de reclamos con narrativas casi idénticas (NLP TF-IDF + coseno)."""
    dfs, _ = _datos()
    return {"pares": pares_similares(dfs["siniestros"], umbral=umbral), "aviso": AVISO}


@app.get("/api/casos/{id_siniestro}/dossier")
def dossier(id_siniestro: str):
    """PDF de investigación del caso, listo para auditoría."""
    pdf = generar_dossier(_detalle(id_siniestro))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="dossier_{id_siniestro}.pdf"'})


@app.get("/api/casos/{id_siniestro}/aviso")
def aviso(id_siniestro: str):
    """Vista previa de las notificaciones (WhatsApp / correo) del caso."""
    d = _detalle(id_siniestro)
    return {"whatsapp": notify.formato_whatsapp(d), "correo": notify.formato_correo(d)}


@app.post("/api/casos/{id_siniestro}/push")
def push(id_siniestro: str):
    """Mock: empuja el score/alerta al core de siniestros (integración futura)."""
    d = _detalle(id_siniestro)
    return {"ok": True, "id_siniestro": d["id_siniestro"], "score": d["score"], "nivel": d["nivel"],
            "mensaje": f"Score {d['score']} ({d['nivel']}) enviado al core de siniestros (receptor mock)."}


class NuevoSiniestro(BaseModel):
    ramo: str = "Vehículos"
    cobertura: str = "Choque"
    monto_reclamado: float = 10000
    suma_asegurada: float = 15000
    dias_desde_inicio_poliza: int = 5         # 1 = siniestro al día siguiente de contratar
    dias_entre_ocurrencia_reporte: int = 1
    historial_siniestros_asegurado: int = 1
    documentos_completos: bool = True
    proveedor_en_lista: bool = False
    clima_inconsistente: bool = False
    doc_inconsistente: bool = False
    distancia_geo_km: float = 0.0
    freq_vehiculo: int = 1


def _features_de_input(c: NuevoSiniestro) -> dict:
    suma = c.suma_asegurada or 1.0
    return {
        "dias_desde_inicio_poliza": c.dias_desde_inicio_poliza,
        "dias_entre_ocurrencia_reporte": c.dias_entre_ocurrencia_reporte,
        "historial_siniestros_asegurado": c.historial_siniestros_asegurado,
        "es_robo": c.cobertura == "Robo",
        "ratio_monto_suma": round(c.monto_reclamado / suma, 3),
        "proveedor_en_lista": c.proveedor_en_lista,
        "asegurado_en_lista": False,
        "freq_proveedor": 1,
        "freq_vehiculo": c.freq_vehiculo,
        "distancia_geo_km": c.distancia_geo_km,
        "clima_inconsistente": c.clima_inconsistente,
        "documentos_completos": c.documentos_completos,
        "doc_inconsistente": c.doc_inconsistente,
        "doc_no_entregado": not c.documentos_completos,
        "narrativa_repetidos": 1,
        "ramo": c.ramo,
        "cobertura": c.cobertura,
    }


def _prob_ml(fila: dict) -> float:
    import pandas as pd
    df = pd.DataFrame([{k: fila.get(k) for k in FEATURES}])
    return float(_modelo().predict_proba(_X(df))[0, 1])


@app.post("/api/scorear")
def scorear(c: NuevoSiniestro):
    """Puntúa un siniestro NUEVO en vivo y explica el riesgo (prueba de fuego del jurado)."""
    fila = _features_de_input(c)
    contribs = evaluar_reglas(fila)
    prob = _prob_ml(fila)
    cml = contribucion_ml(prob)
    if cml:
        contribs.append(cml)
    res = puntuar(contribs)
    res["probabilidad_ml"] = round(prob, 3)
    res["recomendacion"] = _recomendacion(res["nivel"])
    res["aviso"] = AVISO
    return res

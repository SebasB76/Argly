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
from src.nlp.narrative import pares_similares, extraer_entidades, resumen_narrativas
from src.ai_agent.agent import responder
from src.ai_agent import tools
from src.channels.pdf_dossier import generar_dossier
from src.channels import notify
from src.features.build_features import construir_features
from src.models.ml_model import entrenar, FEATURES, _X, explicacion_global, explicacion_local
from src.rules.fraud_rules import evaluar_reglas
from src.scoring.score import puntuar, contribucion_ml

app = FastAPI(title="Argly API", version="0.1.0",
              description="Detección de posible fraude en siniestros. Alertas, no acusaciones.")

_DFS = None
_BANDEJA = None
_MODELO = None
_FEATURES = None


def _datos():
    """Genera los datos, entrena el modelo y construye la bandeja una vez (cache)."""
    global _DFS, _BANDEJA, _MODELO, _FEATURES
    if _BANDEJA is None:
        _DFS = generar()
        _FEATURES = construir_features(_DFS)
        _MODELO, _ = entrenar(_FEATURES)
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
    ahorro = tools.simulacion_ahorro(b)
    return {
        "total": int(len(b)),
        "por_nivel": por_nivel,
        "monto_en_revision": round(monto_revision, 2),
        "ahorro_estimado": ahorro["ahorro_estimado_total"],
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


@app.get("/api/narrativas/resumen")
def narrativas_resumen(top: int = 5):
    """Resumen de narrativas repetidas: moldes de descripción y cuántos reclamos los comparten."""
    dfs, _ = _datos()
    return {"grupos": resumen_narrativas(dfs["siniestros"], top=top), "aviso": AVISO}


@app.get("/api/casos/{id_siniestro}/entidades")
def entidades(id_siniestro: str):
    """Entidades extraídas de la narrativa del siniestro (placas, montos, vías, expedientes)."""
    dfs, _ = _datos()
    s = dfs["siniestros"]
    row = s[s["id_siniestro"] == id_siniestro]
    if row.empty:
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    desc = str(row.iloc[0]["descripcion"])
    return {"id_siniestro": id_siniestro, "descripcion": desc, "entidades": extraer_entidades(desc)}


@app.get("/api/proveedores-pareto")
def proveedores_pareto(objetivo: float = 0.8, solo_rojos: bool = True):
    """Pareto: proveedores que concentran el `objetivo` (80%) de las alertas rojas."""
    return {**tools.proveedores_pareto(_bandeja(), objetivo=objetivo, solo_rojos=solo_rojos), "aviso": AVISO}


@app.get("/api/ahorro")
def ahorro(tasa_fraude_confirmado: float = 0.35):
    """Simulación de ahorro potencial (impacto de negocio) de priorizar con Argly."""
    return {**tools.simulacion_ahorro(_bandeja(), tasa_fraude_confirmado=tasa_fraude_confirmado), "aviso": AVISO}


@app.get("/api/modelo/importancias")
def modelo_importancias():
    """Explicabilidad GLOBAL del modelo ML (SHAP si está instalado; si no, importancia del RF)."""
    _datos()
    return explicacion_global(_MODELO, _FEATURES)


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
    freq_conductor: int = 1
    freq_solo_rc: int = 0
    tercero_identificado: bool = True
    perdida_total: bool = False


def _features_de_input(c: NuevoSiniestro) -> dict:
    suma = c.suma_asegurada or 1.0
    es_robo = c.cobertura == "Robo"
    es_solo_rc = c.cobertura == "Daño a Terceros (RC)"
    return {
        "dias_desde_inicio_poliza": c.dias_desde_inicio_poliza,
        "dias_entre_ocurrencia_reporte": c.dias_entre_ocurrencia_reporte,
        "historial_siniestros_asegurado": c.historial_siniestros_asegurado,
        "es_robo": es_robo,
        "ratio_monto_suma": round(c.monto_reclamado / suma, 3),
        "proveedor_en_lista": c.proveedor_en_lista,
        "asegurado_en_lista": False,
        "freq_proveedor": 1,
        "freq_vehiculo": c.freq_vehiculo,
        "freq_conductor": c.freq_conductor,
        "es_solo_rc": es_solo_rc,
        "freq_solo_rc": c.freq_solo_rc,
        "evento_sin_tercero": not c.tercero_identificado,
        "es_ptxrb": bool(c.perdida_total) and c.cobertura in ("Robo", "Pérdida Total"),
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
    res["factores_modelo"] = explicacion_local(_modelo(), fila)
    res["recomendacion"] = _recomendacion(res["nivel"])
    res["aviso"] = AVISO
    return res

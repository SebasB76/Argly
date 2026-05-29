"""API FastAPI (E3/#7): sirve la bandeja priorizada y el detalle explicable de cada caso.

Levantar:
    uvicorn src.app.main:app --reload
"""
from __future__ import annotations

import io
import json

import pandas as pd
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel

# Carga .env al arrancar la app para que el proceso vea GEMINI_API_KEY/LLM_PROVIDER
load_dotenv(find_dotenv(), override=False)

from src.pipeline import construir_bandeja, evaluar_metricas
from src.ingestion import store
from src.graph.network import detectar_redes
from src.nlp.narrative import pares_similares, extraer_entidades, resumen_narrativas
from src.ai_agent.agent import responder
from src.ai_agent import tools
from src.channels.pdf_dossier import generar_dossier
from src.channels.reporte import generar_reporte_pdf, generar_reporte_excel
from src.channels import notify
from src.features.build_features import construir_features
from src.models.ml_model import entrenar, FEATURES, _X, explicacion_global, explicacion_local
from src.explicabilidad.sesgo import analizar_sesgo
from src.explicabilidad.contrafactual import contrafactual
from src.explicabilidad.contexto import contexto_caso, redactar, vinculos_caso
from src.explicabilidad.checklist import estado_checklist
from src.geo.mapa import mapa_calor
from src.rules.fraud_rules import evaluar_reglas
from src.scoring.score import puntuar, contribucion_ml

app = FastAPI(title="Argly API", version="0.1.0",
              description="Detección de posible fraude en siniestros. Alertas, no acusaciones.")

# CORS: el front (Vercel) vive en otro dominio. CORS_ORIGINS = lista separada por
# comas (p. ej. "https://argly.vercel.app"); por defecto "*" para facilitar la demo.
import os as _os
from fastapi.middleware.cors import CORSMiddleware

_origins = [o.strip() for o in _os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DFS = None
_BANDEJA = None
_MODELO = None
_FEATURES = None
_HIBRIDO = True


def _datos():
    """Carga el dataset desde la DB (fuente de verdad), entrena el modelo si el
    dataset lo admite y construye la bandeja una vez (cache). Si la DB está vacía
    se siembra con el sintético; si el dataset no tiene etiquetas usables, opera
    en modo solo-reglas (sin ML)."""
    global _DFS, _BANDEJA, _MODELO, _FEATURES, _HIBRIDO
    if _BANDEJA is None:
        store.inicializar()
        _DFS = store.cargar_dfs()
        F = construir_features(_DFS)
        # Etiquetas del analista (human-in-the-loop) -> entran al entrenamiento.
        F, _ = store.aplicar_feedback(F)
        _FEATURES = F
        _HIBRIDO = store.admite_hibrido_F(F)
        _MODELO = entrenar(F)[0] if _HIBRIDO else None
        _BANDEJA = construir_bandeja(_DFS, hibrido=_HIBRIDO, F=F)
    return _DFS, _BANDEJA


def _invalidar():
    """Descarta la cache para que el próximo request recargue el dataset desde la DB."""
    global _DFS, _BANDEJA, _MODELO, _FEATURES
    _DFS = _BANDEJA = _MODELO = _FEATURES = None


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
    total = int(len(b))
    por_nivel = {k: int(v) for k, v in b["nivel"].value_counts().items()}
    monto_revision = float(b.loc[b["nivel"] != "VERDE", "monto_reclamado"].sum())
    ahorro = tools.simulacion_ahorro(b)
    pe = store.feedback_resumen()["por_estado"]
    gestionados = pe["en_revision"] + pe["escalado"] + pe["cerrado"]
    por_estado = {"sin_revisar": max(0, total - gestionados), "en_revision": pe["en_revision"],
                  "escalado": pe["escalado"], "cerrado": pe["cerrado"]}
    return {
        "total": total,
        "por_nivel": por_nivel,
        "por_estado": por_estado,
        "monto_en_revision": round(monto_revision, 2),
        "ahorro_estimado": ahorro["ahorro_estimado_total"],
        "aviso": AVISO,
    }


# --- Dataset variable: estado, importación (reemplazar/anexar) y reset --------- #
_TABLAS_IMPORTABLES = ["siniestros", "polizas", "proveedores", "asegurados",
                       "vehiculos", "documentos"]


@app.get("/api/dataset")
def dataset():
    """Estado del dataset actual: origen, conteos por tabla y modo (híbrido/solo-reglas)."""
    return store.resumen()


@app.post("/api/dataset/importar")
async def importar_dataset(
    modo: str = Form("replace"),
    siniestros: UploadFile | None = File(None),
    polizas: UploadFile | None = File(None),
    proveedores: UploadFile | None = File(None),
    asegurados: UploadFile | None = File(None),
    vehiculos: UploadFile | None = File(None),
    documentos: UploadFile | None = File(None),
):
    """Importa un dataset propio. `modo=replace` reemplaza todo; `modo=append`
    anexa filas (omite IDs ya existentes). Cada tabla es un CSV; al menos
    `siniestros` es obligatorio. Tras importar se recalcula todo el pipeline."""
    if modo not in ("replace", "append"):
        raise HTTPException(status_code=400, detail="modo debe ser 'replace' o 'append'")
    archivos = {"siniestros": siniestros, "polizas": polizas, "proveedores": proveedores,
                "asegurados": asegurados, "vehiculos": vehiculos, "documentos": documentos}
    dfs: dict[str, pd.DataFrame] = {}
    for nombre, up in archivos.items():
        if up is None:
            continue
        try:
            contenido = await up.read()
            dfs[nombre] = pd.read_csv(io.BytesIO(contenido))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo leer '{nombre}': {e}")
    if "siniestros" not in dfs or dfs["siniestros"].empty:
        raise HTTPException(status_code=400,
                            detail="Debes incluir al menos la tabla 'siniestros' con filas.")
    try:
        detalle = store.anexar(dfs) if modo == "append" else (store.reemplazar(dfs) and None)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al importar: {e}")
    _invalidar()
    return {"ok": True, "modo": modo, "insertados": detalle, "dataset": store.resumen()}


@app.post("/api/dataset/reset")
def reset_dataset():
    """Vuelve al dataset sintético de demo (descarta lo importado)."""
    store.resetear()
    _invalidar()
    return {"ok": True, "dataset": store.resumen()}


def _bandeja_estado():
    """Bandeja + columnas `estado` (gestión) y `veredicto` (analista) por caso."""
    b = _bandeja().copy()
    fb = store.cargar_feedback()
    b["estado"] = b["id_siniestro"].map(lambda s: fb.get(s, {}).get("estado", "sin_revisar"))
    b["veredicto"] = b["id_siniestro"].map(lambda s: fb.get(s, {}).get("veredicto", "pendiente"))
    return b


@app.get("/api/casos")
def casos(nivel: str | None = None, estado: str | None = None, ramo: str | None = None,
          ciudad: str | None = None, proveedor: str | None = None, motivo: str | None = None,
          q: str | None = None, monto_min: float | None = None, monto_max: float | None = None,
          score_min: int | None = None, score_max: int | None = None,
          orden: str = "score", limit: int = 200, offset: int = 0):
    """Bandeja filtrable y buscable (cola de trabajo del analista)."""
    b = _bandeja_estado()
    if nivel:
        b = b[b["nivel"] == nivel.upper()]
    if estado:
        b = b[b["estado"] == estado]
    if ramo:
        b = b[b["ramo"] == ramo]
    if ciudad:
        b = b[b["sucursal"] == ciudad]
    if proveedor:
        b = b[b["id_proveedor"] == proveedor]
    if motivo:
        b = b[b["motivo_principal"].str.contains(motivo, case=False, na=False)]
    if monto_min is not None:
        b = b[b["monto_reclamado"] >= monto_min]
    if monto_max is not None:
        b = b[b["monto_reclamado"] <= monto_max]
    if score_min is not None:
        b = b[b["score"] >= score_min]
    if score_max is not None:
        b = b[b["score"] <= score_max]
    if q:
        ql = q.strip().lower()
        mask = False
        for col in ("id_siniestro", "id_asegurado", "id_proveedor"):
            mask = mask | b[col].astype(str).str.lower().str.contains(ql, na=False)
        b = b[mask]
    if orden == "impacto":                       # valor esperado = riesgo x monto
        b = b.assign(_ve=b["score"] * b["monto_reclamado"]).sort_values("_ve", ascending=False)
    else:
        b = b.sort_values("score", ascending=False)
    total = int(len(b))
    page = b[CASO_COLS + ["estado", "veredicto"]].iloc[offset:offset + limit]
    return {"total": total, "casos": json.loads(page.to_json(orient="records"))}


def _detalle(id_siniestro: str) -> dict:
    b = _bandeja()
    row = b[b["id_siniestro"] == id_siniestro]
    if row.empty:
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    r = row.iloc[0]
    d = {
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
        "feedback": store.cargar_feedback().get(id_siniestro, {"veredicto": "pendiente", "estado": "sin_revisar", "nota": "", "fecha": ""}),
        "aviso": AVISO,
    }
    d["resumen"] = redactar(d, contexto_caso(id_siniestro, b))   # resumen en lenguaje natural
    return d


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
    if _MODELO is None:
        return {"metodo": "no_disponible", "importancias": {},
                "nota": "Dataset sin etiquetas de fraude usables: Argly opera en modo solo-reglas."}
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


@app.get("/api/casos/{id_siniestro}/contrafactual")
def caso_contrafactual(id_siniestro: str):
    """Explicación contrafactual: qué tendría que cambiar para que el caso pase a VERDE."""
    d = _detalle(id_siniestro)
    return {"id_siniestro": id_siniestro, "score": d["score"], "nivel": d["nivel"],
            **contrafactual(d["contribuciones"]), "aviso": AVISO}


@app.get("/api/casos/{id_siniestro}/vinculos")
def caso_vinculos(id_siniestro: str):
    """Casos relacionados: mismo proveedor/asegurado/conductor/placa y narrativa similar."""
    dfs, b = _datos()
    if not (b["id_siniestro"] == id_siniestro).any():
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    return {"id_siniestro": id_siniestro, **vinculos_caso(id_siniestro, b, dfs), "aviso": AVISO}


@app.get("/api/mapa")
def mapa():
    """Mapa de calor: concentración de alertas por ciudad (con coordenadas)."""
    return {**mapa_calor(_bandeja()), "aviso": AVISO}


def _datos_reporte(dfs, b) -> dict:
    """Consolida todas las secciones del reporte ejecutivo desde la bandeja."""
    from datetime import datetime, timezone
    por_nivel = {k: int(v) for k, v in b["nivel"].value_counts().items()}
    monto_rev = float(b.loc[b["nivel"] != "VERDE", "monto_reclamado"].sum())
    ahorro = tools.simulacion_ahorro(b)
    top = (b.sort_values("score", ascending=False)
           [["id_siniestro", "score", "nivel", "motivo_principal", "monto_reclamado"]]
           .head(15).to_dict("records"))
    meta = store.resumen()
    return {
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "origen": meta.get("origen"), "modo": meta.get("modo"),
        "resumen": {"total": int(len(b)), "por_nivel": por_nivel,
                    "monto_en_revision": round(monto_rev, 2),
                    "ahorro_estimado": ahorro["ahorro_estimado_total"]},
        "metricas": (evaluar_metricas(F=_FEATURES) if _HIBRIDO and _FEATURES is not None else None),
        "top": [{"id_siniestro": str(t["id_siniestro"]), "score": int(t["score"]),
                 "nivel": str(t["nivel"]), "motivo_principal": str(t["motivo_principal"]),
                 "monto_reclamado": float(t["monto_reclamado"])} for t in top],
        "pareto": tools.proveedores_pareto(b),
        "ramos": tools.ramos_sospechosos(b),
        "ciudades": mapa_calor(b)["ciudades"],
        "sesgo": analizar_sesgo(b, dfs),
        "aviso": AVISO,
    }


@app.get("/api/reporte/pdf")
def reporte_pdf():
    """Reporte ejecutivo consolidado en PDF (CU-06): panorama, top de casos,
    Pareto de proveedores, distribución, equidad y métricas."""
    dfs, b = _datos()
    pdf = generar_reporte_pdf(_datos_reporte(dfs, b))
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'inline; filename="reporte_ejecutivo_argly.pdf"'})


@app.get("/api/reporte/excel")
def reporte_excel():
    """Exporta la bandeja completa a Excel multi-hoja para auditoría."""
    dfs, b = _datos()
    por_nivel = {k: int(v) for k, v in b["nivel"].value_counts().items()}
    resumen = {"total": int(len(b)), "por_nivel": por_nivel,
               "monto_en_revision": round(float(b.loc[b["nivel"] != "VERDE", "monto_reclamado"].sum()), 2),
               "ahorro_estimado": tools.simulacion_ahorro(b)["ahorro_estimado_total"]}
    xlsx = generar_reporte_excel(b, pareto=tools.proveedores_pareto(b),
                                 ramos=tools.ramos_sospechosos(b), resumen=resumen)
    return Response(content=xlsx,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="argly_bandeja.xlsx"'})


@app.get("/api/sesgo")
def sesgo():
    """Análisis de sesgo/equidad: tasa de alerta y de falsos positivos por ciudad,
    segmento, canal y ramo, con veredicto de paridad (regla 4/5)."""
    dfs, b = _datos()
    return {**analizar_sesgo(b, dfs), "aviso": AVISO}


@app.post("/api/casos/{id_siniestro}/push")
def push(id_siniestro: str):
    """Mock: empuja el score/alerta al core de siniestros (integración futura)."""
    d = _detalle(id_siniestro)
    return {"ok": True, "id_siniestro": d["id_siniestro"], "score": d["score"], "nivel": d["nivel"],
            "mensaje": f"Score {d['score']} ({d['nivel']}) enviado al core de siniestros (receptor mock)."}


# --- Human-in-the-loop: feedback del analista + reentrenamiento --------------- #
class Feedback(BaseModel):
    veredicto: str          # confirmado | falso_positivo | descartado | pendiente
    nota: str = ""


@app.post("/api/casos/{id_siniestro}/feedback")
def feedback(id_siniestro: str, fb: Feedback):
    """Registra el veredicto del analista sobre un caso (señal de entrenamiento).

    No reentrena al instante: el veredicto se acumula y se incorpora con
    `POST /api/modelo/reentrenar`. Es una etiqueta de revisión humana, no una
    decisión automática."""
    b = _bandeja()
    if not (b["id_siniestro"] == id_siniestro).any():
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    if fb.veredicto not in store.VERDICTOS:
        raise HTTPException(status_code=400,
                            detail=f"veredicto inválido (use {list(store.VERDICTOS)})")
    from datetime import datetime, timezone
    guardado = store.guardar_feedback(id_siniestro, fb.veredicto, fb.nota,
                                      datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"ok": True, "feedback": guardado, "resumen": store.feedback_resumen()}


@app.get("/api/feedback")
def feedback_resumen():
    """Resumen del feedback acumulado: conteos por veredicto/estado y etiquetas disponibles."""
    return store.feedback_resumen()


class EstadoGestion(BaseModel):
    estado: str             # sin_revisar | en_revision | escalado | cerrado


@app.post("/api/casos/{id_siniestro}/estado")
def set_estado(id_siniestro: str, e: EstadoGestion):
    """Cambia el estado de gestión del caso (cola de trabajo del analista)."""
    b = _bandeja()
    if not (b["id_siniestro"] == id_siniestro).any():
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    if e.estado not in store.ESTADOS_GESTION:
        raise HTTPException(status_code=400,
                            detail=f"estado inválido (use {list(store.ESTADOS_GESTION)})")
    from datetime import datetime, timezone
    guardado = store.guardar_estado(id_siniestro, e.estado,
                                    datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"ok": True, "feedback": guardado, "resumen": store.feedback_resumen()}


class Nota(BaseModel):
    texto: str
    autor: str = "Analista"


@app.post("/api/casos/{id_siniestro}/nota")
def agregar_nota(id_siniestro: str, n: Nota):
    """Añade una nota libre del analista a la bitácora del caso."""
    b = _bandeja()
    if not (b["id_siniestro"] == id_siniestro).any():
        raise HTTPException(status_code=404, detail="Siniestro no encontrado")
    if not n.texto.strip():
        raise HTTPException(status_code=400, detail="La nota no puede estar vacía")
    from datetime import datetime, timezone
    hist = store.agregar_nota(id_siniestro, n.texto.strip(), n.autor or "Analista",
                              datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"ok": True, "bitacora": hist}


@app.get("/api/casos/{id_siniestro}/bitacora")
def bitacora(id_siniestro: str):
    """Bitácora del caso: notas + historial de cambios de veredicto/estado."""
    return {"id_siniestro": id_siniestro, "bitacora": store.historial(id_siniestro)}


@app.get("/api/casos/{id_siniestro}/checklist")
def checklist(id_siniestro: str):
    """Pasos de investigación del caso + cuáles están completados."""
    d = _detalle(id_siniestro)
    return {"id_siniestro": id_siniestro,
            **estado_checklist(d["contribuciones"], store.checklist_hechos(id_siniestro))}


class PasoChecklist(BaseModel):
    clave: str
    hecho: bool = True


@app.post("/api/casos/{id_siniestro}/checklist")
def set_checklist(id_siniestro: str, p: PasoChecklist):
    """Marca/desmarca un paso de investigación del caso."""
    d = _detalle(id_siniestro)
    from datetime import datetime, timezone
    hechos = store.toggle_checklist(id_siniestro, p.clave, p.hecho,
                                    datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {"ok": True, "id_siniestro": id_siniestro,
            **estado_checklist(d["contribuciones"], hechos)}


@app.get("/api/mi-trabajo")
def mi_trabajo():
    """Tablero operativo del analista: productividad, pendientes y novedades."""
    be = _bandeja_estado()
    total = int(len(be))
    fbres = store.feedback_resumen()
    pe = fbres["por_estado"]
    gestionados = pe["en_revision"] + pe["escalado"] + pe["cerrado"]
    por_estado = {"sin_revisar": max(0, total - gestionados), "en_revision": pe["en_revision"],
                  "escalado": pe["escalado"], "cerrado": pe["cerrado"]}

    confirmados = be[be["veredicto"] == "confirmado"]
    pendientes_rojos = be[(be["nivel"] == "ROJO") & (be["estado"] == "sin_revisar")]
    top_pend = (pendientes_rojos.assign(_ve=pendientes_rojos["score"] * pendientes_rojos["monto_reclamado"])
                .sort_values("_ve", ascending=False)
                [["id_siniestro", "score", "nivel", "motivo_principal", "monto_reclamado", "sucursal"]]
                .head(6))
    return {
        "total": total,
        "revisados": total - por_estado["sin_revisar"],
        "por_estado": por_estado,
        "por_veredicto": fbres["por_veredicto"],
        "monto_confirmado": round(float(confirmados["monto_reclamado"].sum()), 2),
        "monto_escalado": round(float(be.loc[be["estado"] == "escalado", "monto_reclamado"].sum()), 2),
        "pendientes_rojos": int(len(pendientes_rojos)),
        "pendientes_top": json.loads(top_pend.to_json(orient="records")),
        "proveedores_top": tools.proveedores_top(be, n=5),
        "actividad_reciente": store.actividad_reciente(12),
        "aviso": AVISO,
    }


@app.post("/api/modelo/reentrenar")
def reentrenar():
    """Reentrena incorporando las etiquetas del analista y devuelve métricas
    ANTES vs DESPUÉS, medidas sobre el mismo test held-out (sin fuga)."""
    dfs, _ = _datos()
    F0 = construir_features(dfs)                       # sin feedback (línea base)
    F1, aplicados = store.aplicar_feedback(F0.copy())  # con feedback del analista
    resp = {
        "feedback_aplicado": aplicados,
        "resumen_feedback": store.feedback_resumen(),
        "antes": evaluar_metricas(F=F0) if store.admite_hibrido_F(F0) else None,
        "despues": evaluar_metricas(F=F1) if store.admite_hibrido_F(F1) else None,
    }
    a, d = resp["antes"], resp["despues"]
    if a and d:
        resp["mejora"] = {k: round((d[k] or 0) - (a[k] or 0), 3)
                          for k in ("auc_hibrido", "auc_ml", "precision", "recall", "f1")
                          if a.get(k) is not None and d.get(k) is not None}
    _invalidar()        # la próxima carga usa el modelo reentrenado con feedback
    resp["ok"] = True
    return resp


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


def _prob_ml(fila: dict) -> float | None:
    """Probabilidad de fraude del modelo, o None si el dataset corre en solo-reglas."""
    m = _modelo()
    if m is None:
        return None
    df = pd.DataFrame([{k: fila.get(k) for k in FEATURES}])
    return float(m.predict_proba(_X(df))[0, 1])


@app.post("/api/scorear")
def scorear(c: NuevoSiniestro):
    """Puntúa un siniestro NUEVO en vivo y explica el riesgo (prueba de fuego del jurado)."""
    fila = _features_de_input(c)
    contribs = evaluar_reglas(fila)
    prob = _prob_ml(fila)
    if prob is not None:
        cml = contribucion_ml(prob)
        if cml:
            contribs.append(cml)
    res = puntuar(contribs)
    if prob is not None:
        res["probabilidad_ml"] = round(prob, 3)
        res["factores_modelo"] = explicacion_local(_modelo(), fila)
    res["recomendacion"] = _recomendacion(res["nivel"])
    res["aviso"] = AVISO
    return res

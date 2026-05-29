"""Acceso al dataset persistido (DB = fuente de verdad).

La API ya no trabaja sobre `generar()` en memoria: lee las tablas desde la base
(SQLite por defecto, o Postgres vía DATABASE_URL). Esto hace que el dataset sea
VARIABLE: se puede reemplazar por uno propio o anexarle casos, y los cambios
sobreviven reinicios.

Flujo:
- `inicializar()`  -> si la DB está vacía, la siembra con el sintético (demo
  sigue siendo cero-fricción: no hay que correr seed a mano).
- `cargar_dfs()`   -> lee las 6 tablas al mismo dict que devuelve `generar()`.
- `normalizar()`   -> deja cualquier dataset (importado) listo para el pipeline:
  rellena columnas derivadas y columnas/tablas faltantes con defaults.
- `reemplazar()` / `anexar()` -> escriben a la DB y registran el origen.
- `resumen()`      -> conteos por tabla + origen + si admite modo híbrido (ML).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import Boolean, Date, Float, Integer, String, inspect, text

from src import config
from src.ingestion import models
from src.ingestion.db import Base, get_engine, get_sessionmaker

# (nombre lógico, modelo SQLAlchemy) en orden de dependencia (padres primero).
TABLAS: list[tuple[str, type]] = [
    ("asegurados", models.Asegurado),
    ("proveedores", models.Proveedor),
    ("polizas", models.Poliza),
    ("vehiculos", models.Vehiculo),
    ("siniestros", models.Siniestro),
    ("documentos", models.Documento),
]
NOMBRES = [n for n, _ in TABLAS]
_MODELO = {n: m for n, m in TABLAS}

# Columnas de fecha por tabla (para coerción al leer/escribir).
_FECHAS = {
    "polizas": ["fecha_inicio", "fecha_fin"],
    "siniestros": ["fecha_ocurrencia", "fecha_reporte"],
    "documentos": ["fecha_emision"],
}


# --------------------------------------------------------------------------- #
# Esquema / defaults
# --------------------------------------------------------------------------- #
def columnas(nombre: str) -> list[str]:
    return [c.name for c in _MODELO[nombre].__table__.columns]


def _default_por_tipo(col) -> object:
    t = col.type
    if isinstance(t, Boolean):
        return False
    if isinstance(t, Integer):
        return 0
    if isinstance(t, Float):
        return 0.0
    if isinstance(t, Date):
        return pd.NaT
    return ""  # String / otros


def _coercionar(nombre: str, df: pd.DataFrame) -> pd.DataFrame:
    """Asegura que `df` tenga TODAS las columnas del modelo, con tipos coherentes."""
    df = df.copy()
    for col in _MODELO[nombre].__table__.columns:
        if col.name not in df.columns:
            df[col.name] = _default_por_tipo(col)
        s = df[col.name]
        t = col.type
        if isinstance(t, Boolean):
            df[col.name] = s.map(_a_bool).fillna(False).astype(bool)
        elif isinstance(t, Integer):
            df[col.name] = pd.to_numeric(s, errors="coerce").fillna(0).astype("int64")
        elif isinstance(t, Float):
            df[col.name] = pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)
        elif isinstance(t, Date):
            df[col.name] = pd.to_datetime(s, errors="coerce")
    return df[columnas(nombre)]


def _a_bool(v) -> bool | float:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "t", "yes", "si", "sí", "verdadero")
    if pd.isna(v):
        return np.nan
    return bool(v)


# --------------------------------------------------------------------------- #
# Normalización: dejar cualquier dataset listo para el pipeline
# --------------------------------------------------------------------------- #
def normalizar(dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Devuelve un dict con las 6 tablas, columnas completas y campos derivados.

    Tolera datasets importados parciales: las tablas que falten se crean vacías
    (con su esquema) y los campos derivados de siniestros se calculan si faltan.
    """
    out = {n: _coercionar(n, dfs.get(n, pd.DataFrame())) for n in NOMBRES}
    s = out["siniestros"]
    if s.empty:
        return out

    pol = out["polizas"].set_index("id_poliza") if not out["polizas"].empty else None

    # --- Campos derivados de fechas (si vienen vacíos/0) ---
    foc = pd.to_datetime(s["fecha_ocurrencia"], errors="coerce")
    frep = pd.to_datetime(s["fecha_reporte"], errors="coerce")
    if pol is not None:
        fi = pd.to_datetime(s["id_poliza"].map(pol["fecha_inicio"]), errors="coerce")
        ff = pd.to_datetime(s["id_poliza"].map(pol["fecha_fin"]), errors="coerce")
    else:
        fi = ff = pd.Series(pd.NaT, index=s.index)

    s = _rellenar_derivado(s, "dias_desde_inicio_poliza", (foc - fi).dt.days)
    s = _rellenar_derivado(s, "dias_desde_fin_poliza", (ff - foc).dt.days)
    s = _rellenar_derivado(s, "dias_entre_ocurrencia_reporte", (frep - foc).dt.days)
    hist = s.groupby("id_asegurado")["id_siniestro"].transform("count")
    s = _rellenar_derivado(s, "historial_siniestros_asegurado", hist)

    # --- Split: si no hay test, lo deriva de forma estratificada y reproducible ---
    if not s["split"].isin(["test"]).any():
        s = _asignar_split(s)

    out["siniestros"] = _coercionar("siniestros", s)
    return out


def _rellenar_derivado(s: pd.DataFrame, col: str, calc: pd.Series) -> pd.DataFrame:
    """Usa el valor calculado donde el provisto sea 0/NaN; respeta lo que ya venía."""
    provisto = pd.to_numeric(s.get(col), errors="coerce")
    calc = pd.to_numeric(calc, errors="coerce")
    s[col] = provisto.where(provisto.fillna(0) != 0, calc).fillna(0).astype("int64")
    return s


def _asignar_split(s: pd.DataFrame) -> pd.DataFrame:
    """Marca ~30% como test (estratificado por etiqueta si la hay), semilla fija."""
    s = s.copy()
    s["split"] = "train"
    y = pd.to_numeric(s.get("etiqueta_fraude_simulada"), errors="coerce").fillna(0).astype(int)
    rng = np.random.default_rng(config.SEED)
    if y.nunique() >= 2:
        idx = []
        for _, grupo in s.groupby(y.values):
            n = max(1, int(len(grupo) * 0.30))
            idx += list(rng.choice(grupo.index, size=min(n, len(grupo)), replace=False))
        s.loc[idx, "split"] = "test"
    else:
        idx = rng.choice(s.index, size=int(len(s) * 0.30), replace=False)
        s.loc[idx, "split"] = "test"
    return s


def admite_hibrido(dfs: dict[str, pd.DataFrame]) -> bool:
    """True si el dataset permite entrenar ML: hay filas train con ambas clases."""
    s = dfs["siniestros"]
    if s.empty or "etiqueta_fraude_simulada" not in s.columns:
        return False
    tr = s[s["split"] == "train"]
    return tr["etiqueta_fraude_simulada"].astype(int).nunique() >= 2


# --------------------------------------------------------------------------- #
# Lectura / escritura en la DB
# --------------------------------------------------------------------------- #
def _records(df: pd.DataFrame) -> list[dict]:
    """numpy -> tipos nativos; fechas -> date (compatibles con cualquier driver)."""
    out = []
    for row in df.to_dict("records"):
        clean = {}
        for k, v in row.items():
            if isinstance(v, np.integer):
                v = int(v)
            elif isinstance(v, np.floating):
                v = None if pd.isna(v) else float(v)
            elif isinstance(v, (np.bool_, bool)):
                v = bool(v)
            elif isinstance(v, pd.Timestamp):
                v = None if pd.isna(v) else v.date()
            elif v is pd.NaT or (isinstance(v, float) and pd.isna(v)):
                v = None
            clean[k] = v
        out.append(clean)
    return out


def vacio(url: str | None = None) -> bool:
    """True si no hay esquema o la tabla de siniestros está vacía."""
    engine = get_engine(url)
    if not inspect(engine).has_table("siniestros"):
        return True
    with engine.connect() as c:
        return c.execute(text("SELECT COUNT(*) FROM siniestros")).scalar() == 0


def cargar_dfs(url: str | None = None) -> dict[str, pd.DataFrame]:
    """Lee las 6 tablas de la DB y las devuelve normalizadas (listas para el pipeline)."""
    engine = get_engine(url)
    insp = inspect(engine)
    dfs = {}
    for nombre in NOMBRES:
        if insp.has_table(nombre):
            df = pd.read_sql_table(nombre, engine, parse_dates=_FECHAS.get(nombre))
        else:
            df = pd.DataFrame(columns=columnas(nombre))
        dfs[nombre] = df
    return normalizar(dfs)


def _escribir(dfs: dict[str, pd.DataFrame], origen: str, url: str | None = None):
    """Reescribe el esquema completo con `dfs` (drop+create) y registra el origen."""
    engine = get_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = get_sessionmaker(engine)
    with Session() as s:
        for nombre, model in TABLAS:
            df = _coercionar(nombre, dfs[nombre])
            if len(df):
                s.bulk_insert_mappings(model, _records(df))
        s.commit()
    _set_meta({"origen": origen}, url)
    return engine


def reemplazar(dfs: dict[str, pd.DataFrame], url: str | None = None):
    """Importa un dataset COMPLETO: reemplaza todo lo que haya en la DB."""
    return _escribir(normalizar(dfs), "importado", url)


def anexar(dfs_nuevos: dict[str, pd.DataFrame], url: str | None = None) -> dict[str, int]:
    """Anexa filas a las tablas existentes (omite PKs ya presentes). Devuelve conteos."""
    if vacio(url):
        inicializar(url)
    actual = cargar_dfs(url)
    insertados = {}
    fusion = {}
    for nombre, model in TABLAS:
        pk = model.__table__.primary_key.columns.keys()[0]
        base = actual[nombre]
        nuevos = _coercionar(nombre, dfs_nuevos.get(nombre, pd.DataFrame()))
        if nuevos.empty:
            fusion[nombre] = base
            insertados[nombre] = 0
            continue
        existentes = set(base[pk].astype(str))
        nuevos = nuevos[~nuevos[pk].astype(str).isin(existentes)]
        insertados[nombre] = len(nuevos)
        fusion[nombre] = pd.concat([base, nuevos], ignore_index=True)
    _escribir(normalizar(fusion), "importado", url)
    return insertados


def inicializar(url: str | None = None, forzar: bool = False):
    """Si la DB está vacía (o `forzar`), la siembra con el dataset sintético."""
    if forzar or vacio(url):
        from src.ingestion.generate_synthetic import generar
        _escribir(normalizar(generar()), "sintetico", url)


def resetear(url: str | None = None):
    """Vuelve al dataset sintético (descarta lo importado)."""
    inicializar(url, forzar=True)


# --------------------------------------------------------------------------- #
# Metadatos / resumen
# --------------------------------------------------------------------------- #
def _set_meta(pares: dict[str, str], url: str | None = None):
    engine = get_engine(url)
    Base.metadata.create_all(engine, tables=[models.Meta.__table__])
    Session = get_sessionmaker(engine)
    with Session() as s:
        for k, v in pares.items():
            obj = s.get(models.Meta, k)
            if obj:
                obj.valor = str(v)
            else:
                s.add(models.Meta(clave=k, valor=str(v)))
        s.commit()


def _get_meta(clave: str, url: str | None = None) -> str | None:
    engine = get_engine(url)
    if not inspect(engine).has_table("argly_meta"):
        return None
    with get_sessionmaker(engine)() as s:
        obj = s.get(models.Meta, clave)
        return obj.valor if obj else None


# --------------------------------------------------------------------------- #
# Feedback del analista (human-in-the-loop)
# --------------------------------------------------------------------------- #
VERDICTOS = ("confirmado", "falso_positivo", "descartado", "pendiente")
ESTADOS_GESTION = ("sin_revisar", "en_revision", "escalado", "cerrado")
# Mapeo veredicto -> etiqueta de entrenamiento (None = no aporta etiqueta).
_ETIQUETA = {"confirmado": 1, "falso_positivo": 0, "descartado": 0, "pendiente": None}


def _asegurar_esquema_feedback(engine):
    """Crea la tabla de feedback o, si existe con esquema viejo, le agrega columnas
    faltantes (migración ligera para DBs creadas antes de añadir `estado`)."""
    insp = inspect(engine)
    if not insp.has_table("feedback_analista"):
        Base.metadata.create_all(engine, tables=[models.Feedback.__table__])
        return
    cols = {c["name"] for c in insp.get_columns("feedback_analista")}
    if "estado" not in cols:
        with engine.begin() as c:
            c.execute(text("ALTER TABLE feedback_analista ADD COLUMN estado VARCHAR"))


def _upsert_feedback(url, id_siniestro, **campos):
    """Crea/actualiza la fila del analista para un siniestro sin pisar otros campos."""
    engine = get_engine(url)
    _asegurar_esquema_feedback(engine)
    with get_sessionmaker(engine)() as s:
        obj = s.get(models.Feedback, id_siniestro)
        if obj is None:
            obj = models.Feedback(id_siniestro=id_siniestro, veredicto="pendiente",
                                  estado="sin_revisar", nota="", fecha="")
            s.add(obj)
        for k, v in campos.items():
            setattr(obj, k, v)
        s.commit()


def guardar_feedback(id_siniestro: str, veredicto: str, nota: str = "",
                     fecha: str = "", autor: str = "Analista", url: str | None = None) -> dict:
    """Registra el veredicto del analista. Si el caso estaba 'sin_revisar', su
    estado de gestión avanza a 'en_revision' (dar un veredicto = haberlo mirado).
    Deja constancia en la bitácora."""
    if veredicto not in VERDICTOS:
        raise ValueError(f"veredicto inválido: {veredicto} (use {VERDICTOS})")
    actual = cargar_feedback(url).get(id_siniestro, {})
    estado = actual.get("estado") or "sin_revisar"
    if estado == "sin_revisar":
        estado = "en_revision"
    _upsert_feedback(url, id_siniestro, veredicto=veredicto, nota=nota, fecha=fecha, estado=estado)
    agregar_evento(id_siniestro, "veredicto", texto=nota, valor=veredicto, autor=autor, fecha=fecha, url=url)
    return cargar_feedback(url).get(id_siniestro, {"id_siniestro": id_siniestro})


def guardar_estado(id_siniestro: str, estado: str, fecha: str = "",
                   autor: str = "Analista", url: str | None = None) -> dict:
    """Cambia el estado de gestión (cola de trabajo) sin tocar el veredicto.
    Deja constancia en la bitácora."""
    if estado not in ESTADOS_GESTION:
        raise ValueError(f"estado inválido: {estado} (use {ESTADOS_GESTION})")
    _upsert_feedback(url, id_siniestro, estado=estado, fecha=fecha)
    agregar_evento(id_siniestro, "estado", valor=estado, autor=autor, fecha=fecha, url=url)
    return cargar_feedback(url).get(id_siniestro, {"id_siniestro": id_siniestro})


# --- Bitácora del caso (trazabilidad / auditoría) --------------------------- #
def agregar_evento(id_siniestro: str, tipo: str, texto: str = "", valor: str = "",
                   autor: str = "Analista", fecha: str = "", url: str | None = None) -> None:
    """Registra un evento en la bitácora del caso (nota, veredicto o estado)."""
    engine = get_engine(url)
    Base.metadata.create_all(engine, tables=[models.Bitacora.__table__])
    with get_sessionmaker(engine)() as s:
        s.add(models.Bitacora(id_siniestro=id_siniestro, tipo=tipo, texto=texto or "",
                              valor=valor or "", autor=autor or "Analista", fecha=fecha or ""))
        s.commit()


def agregar_nota(id_siniestro: str, texto: str, autor: str = "Analista",
                 fecha: str = "", url: str | None = None) -> list[dict]:
    """Añade una nota libre del analista y devuelve la bitácora actualizada."""
    agregar_evento(id_siniestro, "nota", texto=texto, autor=autor, fecha=fecha, url=url)
    return historial(id_siniestro, url)


def historial(id_siniestro: str, url: str | None = None) -> list[dict]:
    """Eventos de la bitácora de un caso, en orden cronológico."""
    engine = get_engine(url)
    if not inspect(engine).has_table("bitacora"):
        return []
    with get_sessionmaker(engine)() as s:
        filas = (s.query(models.Bitacora)
                 .filter(models.Bitacora.id_siniestro == id_siniestro)
                 .order_by(models.Bitacora.id.asc()).all())
        return [{"id": f.id, "tipo": f.tipo, "texto": f.texto or "", "valor": f.valor or "",
                 "autor": f.autor or "Analista", "fecha": f.fecha or ""} for f in filas]


def actividad_reciente(n: int = 12, url: str | None = None) -> list[dict]:
    """Últimos `n` eventos de bitácora de todos los casos (feed de novedades)."""
    engine = get_engine(url)
    if not inspect(engine).has_table("bitacora"):
        return []
    with get_sessionmaker(engine)() as s:
        filas = s.query(models.Bitacora).order_by(models.Bitacora.id.desc()).limit(n).all()
        return [{"id_siniestro": f.id_siniestro, "tipo": f.tipo, "texto": f.texto or "",
                 "valor": f.valor or "", "autor": f.autor or "Analista", "fecha": f.fecha or ""}
                for f in filas]


# --- Checklist de investigación --------------------------------------------- #
def checklist_hechos(id_siniestro: str, url: str | None = None) -> set[str]:
    """Conjunto de claves de pasos ya completados para un caso."""
    engine = get_engine(url)
    if not inspect(engine).has_table("checklist"):
        return set()
    with get_sessionmaker(engine)() as s:
        return {c.clave for c in s.query(models.Checklist)
                .filter(models.Checklist.id_siniestro == id_siniestro).all()}


def toggle_checklist(id_siniestro: str, clave: str, hecho: bool,
                     fecha: str = "", url: str | None = None) -> set[str]:
    """Marca/desmarca un paso de investigación. Devuelve las claves hechas."""
    engine = get_engine(url)
    Base.metadata.create_all(engine, tables=[models.Checklist.__table__])
    with get_sessionmaker(engine)() as s:
        existe = (s.query(models.Checklist)
                  .filter(models.Checklist.id_siniestro == id_siniestro,
                          models.Checklist.clave == clave).first())
        if hecho and not existe:
            s.add(models.Checklist(id_siniestro=id_siniestro, clave=clave, fecha=fecha))
        elif not hecho and existe:
            s.query(models.Checklist).filter(
                models.Checklist.id_siniestro == id_siniestro,
                models.Checklist.clave == clave).delete()
        s.commit()
    return checklist_hechos(id_siniestro, url)


def cargar_feedback(url: str | None = None) -> dict[str, dict]:
    """Devuelve {id_siniestro: {veredicto, estado, nota, fecha}} con todo el registro."""
    engine = get_engine(url)
    if not inspect(engine).has_table("feedback_analista"):
        return {}
    _asegurar_esquema_feedback(engine)
    with get_sessionmaker(engine)() as s:
        filas = s.query(models.Feedback).all()
        return {f.id_siniestro: {"id_siniestro": f.id_siniestro,
                                 "veredicto": f.veredicto or "pendiente",
                                 "estado": f.estado or "sin_revisar",
                                 "nota": f.nota or "", "fecha": f.fecha or ""} for f in filas}


def feedback_resumen(url: str | None = None) -> dict:
    """Conteos por veredicto y por estado + cuántas etiquetas de analista hay."""
    fb = cargar_feedback(url)
    por_veredicto = {v: 0 for v in VERDICTOS}
    por_estado = {e: 0 for e in ESTADOS_GESTION}
    for d in fb.values():
        por_veredicto[d["veredicto"]] = por_veredicto.get(d["veredicto"], 0) + 1
        por_estado[d["estado"]] = por_estado.get(d["estado"], 0) + 1
    etiquetados = sum(1 for d in fb.values() if _ETIQUETA.get(d["veredicto"]) is not None)
    return {"total": len(fb), "por_veredicto": por_veredicto, "por_estado": por_estado,
            "etiquetas_disponibles": etiquetados}


def aplicar_feedback(F, fb: dict[str, dict] | None = None, url: str | None = None):
    """Sobrescribe la etiqueta de entrenamiento con el veredicto del analista.

    Los siniestros revisados pasan a `split='train'` (su veredicto es señal de
    entrenamiento), de modo que el test held-out NO se contamina con feedback y
    las métricas antes/después son comparables sobre el mismo conjunto de evaluación.
    Devuelve (F2, n_aplicados).
    """
    if fb is None:
        fb = cargar_feedback(url)
    F2 = F.copy()
    n = 0
    for sid, d in fb.items():
        etq = _ETIQUETA.get(d["veredicto"])
        if etq is None:
            continue
        mask = F2["id_siniestro"] == sid
        if mask.any():
            F2.loc[mask, "etiqueta_fraude_simulada"] = etq
            F2.loc[mask, "split"] = "train"
            n += 1
    return F2, n


def admite_hibrido_F(F) -> bool:
    """True si las features admiten ML: hay filas train con ambas clases."""
    tr = F[F["split"] == "train"]
    return len(tr) > 0 and tr["etiqueta_fraude_simulada"].astype(int).nunique() >= 2


def resumen(url: str | None = None) -> dict:
    """Conteos por tabla + origen del dataset + si admite modo híbrido (ML)."""
    inicializar(url)
    engine = get_engine(url)
    insp = inspect(engine)
    conteos = {}
    with engine.connect() as c:
        for nombre in NOMBRES:
            conteos[nombre] = (
                int(c.execute(text(f"SELECT COUNT(*) FROM {nombre}")).scalar())
                if insp.has_table(nombre) else 0
            )
    dfs = cargar_dfs(url)
    s = dfs["siniestros"]
    etiquetados = int(pd.to_numeric(s["etiqueta_fraude_simulada"], errors="coerce").fillna(0).sum())
    return {
        "origen": _get_meta("origen", url) or "sintetico",
        "conteos": conteos,
        "n_siniestros": int(len(s)),
        "n_train": int((s["split"] == "train").sum()),
        "n_test": int((s["split"] == "test").sum()),
        "casos_etiquetados_fraude": etiquetados,
        "modo": "hibrido" if admite_hibrido(dfs) else "solo_reglas",
        "columnas_esperadas": {n: columnas(n) for n in NOMBRES},
    }

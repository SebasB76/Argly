"""
Generador de datos sintéticos para Argly (E0).

Crea un dataset reproducible (semilla fija) de siniestros de seguros con
patrones de posible fraude PLANTADOS y etiquetados (`etiqueta_fraude_simulada`)
para (a) demostrar la detección y (b) medir métricas reales.

Decisiones del plan:
- Señales geo/clima/lista restrictiva se PRECOMPUTAN aquí (no hay APIs en vivo).
- Train/test SEPARADOS: las redes (rings) del test usan proveedores distintos a
  los del train, para evitar métricas circulares (el test ve variantes no vistas).
- 100% sintético, sin PII real. Los identificadores son anónimos.

Uso:
    python -m src.ingestion.generate_synthetic
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src import config

# --- Pools de apoyo ---
MARCAS = [("Chevrolet", "Sail"), ("Kia", "Rio"), ("Toyota", "Hilux"),
          ("Hyundai", "Tucson"), ("Nissan", "Versa"), ("Mazda", "CX-5"),
          ("Renault", "Duster"), ("Volkswagen", "Gol")]
VIAS = ["Av. Amazonas", "Av. 6 de Diciembre", "Av. de las Américas",
        "Vía a Daule", "Av. Naciones Unidas", "Av. Ordóñez Lasso", "Panamericana Sur"]
TIPOS_IMPACTO = ["frontal", "posterior", "lateral", "volcadura", "múltiple"]

NARRATIVAS = {
    "Choque": [
        "El vehículo asegurado fue impactado en la parte {parte} mientras circulaba por {via}.",
        "Colisión {parte} a la altura de {via}; daños considerables en el automotor.",
    ],
    "Robo": [
        "El asegurado reporta la sustracción del vehículo en el sector de {via}.",
        "Robo del bien asegurado mientras se encontraba estacionado en {via}.",
    ],
    "Atención Médica": [
        "El paciente acude por {dolencia} y requiere atención con exámenes.",
        "Atención médica por {dolencia}; se solicita cobertura de gastos.",
    ],
    "_default": [
        "Siniestro reportado por el asegurado con afectación al bien cubierto.",
        "Evento declarado que afecta la cobertura contratada de la póliza.",
    ],
}
DOLENCIAS = ["dolor abdominal", "fractura de tobillo", "cuadro respiratorio", "lumbalgia"]
# Narrativa "molde" para el patrón de narrativa clonada (se repite casi idéntica).
NARRATIVA_CLON = ("El automotor fue colisionado por un tercero que se dio a la fuga "
                  "en la intersección; se reportan daños en la parte frontal y costado.")


def _placa() -> str:
    letras = "".join(random.choice("ABCGHIJOPSTUVZ") for _ in range(3))
    return f"{letras}-{random.randint(1000, 9999)}"


def _chasis() -> str:
    return "".join(random.choice("ABCDEFGHJKLMNPRSTUVWXYZ0123456789") for _ in range(17))


def _motor() -> str:
    return "".join(random.choice("ABCDEFGHJKLMNPRSTUVWXYZ0123456789") for _ in range(10))


def _haversine_km(a: str, b: str) -> float:
    """Distancia aproximada en km entre dos ciudades (para imposibilidad geográfica)."""
    (la1, lo1), (la2, lo2) = config.CIUDADES[a], config.CIUDADES[b]
    r = 6371.0
    dla, dlo = math.radians(la2 - la1), math.radians(lo2 - lo1)
    h = (math.sin(dla / 2) ** 2
         + math.cos(math.radians(la1)) * math.cos(math.radians(la2)) * math.sin(dlo / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(h))


def _narrativa(cobertura: str) -> str:
    plantillas = NARRATIVAS.get(cobertura, NARRATIVAS["_default"])
    base_txt = random.choice(plantillas).format(
        parte=random.choice(["frontal", "posterior", "lateral"]),
        via=random.choice(VIAS),
        dolencia=random.choice(DOLENCIAS),
    )
    # Detalle variable: las narrativas legítimas quedan diversas (evita falsos
    # "clonados"); las narrativas clonadas se sobrescriben aparte (NARRATIVA_CLON).
    detalle = random.choice([
        f"aproximadamente a las {random.randint(6, 22)}h{random.choice(['00', '15', '30', '45'])}",
        f"a la altura del km {random.randint(1, 45)}",
        f"con {random.randint(1, 4)} ocupantes en el vehículo",
        "sin heridos que reportar",
        "con apoyo de grúa en el lugar",
        f"según parte policial N {random.randint(1000, 9999)}",
    ])
    return f"{base_txt} Se reporta {detalle}. Expediente {random.randint(100000, 999999)}."


def generar(seed: int = config.SEED, n_aseg: int = 600, n_prov: int = 80) -> dict[str, pd.DataFrame]:
    """Genera todas las tablas y devuelve un dict de DataFrames."""
    random.seed(seed)
    np.random.seed(seed)
    ciudades = list(config.CIUDADES.keys())

    # --- Asegurados ---
    asegurados = []
    for i in range(1, n_aseg + 1):
        asegurados.append(dict(
            id_asegurado=f"A{i:05d}",
            segmento=random.choice(config.SEGMENTOS),
            ciudad=random.choice(ciudades),
            antiguedad_meses=random.randint(1, 180),
            score_cliente=random.randint(300, 900),
            telefono=f"09{random.randint(10_000_000, 99_999_999)}",
            en_lista_restrictiva=False,
        ))

    # --- Proveedores ---
    proveedores = []
    for i in range(1, n_prov + 1):
        proveedores.append(dict(
            id_proveedor=f"P{i:04d}",
            tipo=random.choice(config.TIPOS_PROVEEDOR),
            ciudad=random.choice(ciudades),
            antiguedad_meses=random.randint(1, 240),
            en_lista_restrictiva=False,
        ))
    prov_normales = [p["id_proveedor"] for p in proveedores]
    ring_ids = [prov_normales[0], prov_normales[1]]      # proveedores de las redes (rings)
    pool_legit = [p for p in prov_normales if p not in ring_ids]

    # --- Pólizas + vehículos ---
    polizas, vehiculos, pol_by_id = [], [], {}
    pol_n = 0
    for a in asegurados:
        for _ in range(random.randint(1, 2)):
            pol_n += 1
            ramo = random.choices(config.RAMOS, weights=[5, 2, 1, 1, 1])[0]
            inicio = date(2024, 1, 1) + timedelta(days=random.randint(0, 365))
            fin = inicio + timedelta(days=365)
            suma = random.choice([8000, 12000, 15000, 20000, 30000, 50000])
            pid = f"POL{pol_n:05d}"
            pol = dict(id_poliza=pid, id_asegurado=a["id_asegurado"], ramo=ramo,
                       fecha_inicio=inicio, fecha_fin=fin,
                       prima=round(suma * random.uniform(0.03, 0.08), 2),
                       suma_asegurada=suma, deducible=round(suma * 0.01, 2),
                       canal_venta=random.choice(config.CANALES_VENTA),
                       ciudad=a["ciudad"], estado_poliza="Vigente")
            polizas.append(pol)
            pol_by_id[pid] = pol
            if ramo == "Vehículos":
                marca, modelo = random.choice(MARCAS)
                vehiculos.append(dict(placa=_placa(), chasis=_chasis(), motor=_motor(),
                                      marca=marca, modelo=modelo, anio=random.randint(2012, 2024),
                                      id_asegurado=a["id_asegurado"], id_poliza=pid))
    placa_by_aseg = {}
    for v in vehiculos:
        placa_by_aseg.setdefault(v["id_asegurado"], v["placa"])

    sin = []
    sid = 0

    def nuevo_id() -> str:
        nonlocal sid
        sid += 1
        return f"SIN{sid:06d}"

    def base(pol: dict, patron: str = "legitimo", etiqueta: int = 0,
             id_prov: str | None = None) -> dict:
        """Construye un siniestro legítimo por defecto (los archetipos lo sobrescriben)."""
        ramo = pol["ramo"]
        cobertura = random.choice(config.COBERTURAS[ramo])
        ini, fin = pol["fecha_inicio"], pol["fecha_fin"]
        ocurr = ini + timedelta(days=random.randint(20, max((fin - ini).days - 20, 21)))
        reporte = ocurr + timedelta(days=random.randint(0, 3))
        suma = pol["suma_asegurada"]
        reclamado = round(suma * random.uniform(0.05, 0.40), 2)
        ciudad = pol["ciudad"]
        return dict(
            id_siniestro=nuevo_id(), id_poliza=pol["id_poliza"], id_asegurado=pol["id_asegurado"],
            id_proveedor=id_prov or random.choice(pool_legit),
            placa=placa_by_aseg.get(pol["id_asegurado"], ""),
            ramo=ramo, cobertura=cobertura,
            fecha_ocurrencia=ocurr, fecha_reporte=reporte,
            monto_reclamado=reclamado, monto_estimado=round(reclamado * random.uniform(0.85, 1.05), 2),
            monto_pagado=0.0, estado="Reserva", sucursal=ciudad,
            descripcion=_narrativa(cobertura), documentos_completos=True,
            beneficiario_tipo=random.choice(config.TIPOS_PROVEEDOR),
            hora_ocurrencia=random.randint(6, 22),
            tipo_impacto=random.choice(TIPOS_IMPACTO) if ramo == "Vehículos" else "",
            tercero_identificado=True,
            ciudad_ocurrencia=ciudad, ciudad_taller=ciudad,
            clima_declarado="Despejado", clima_real="Despejado",
            patron=patron, etiqueta_fraude_simulada=etiqueta, split="train",
        )

    polizas_veh = [p for p in polizas if p["ramo"] == "Vehículos"]

    # --- Base legítima ---
    for _ in range(1100):
        sin.append(base(random.choice(polizas)))

    # --- Patrón: borde de vigencia (ocurrencia <= 10 días del inicio) ---
    for _ in range(60):
        pol = random.choice(polizas)
        s = base(pol, "borde_vigencia", 1)
        s["fecha_ocurrencia"] = pol["fecha_inicio"] + timedelta(days=random.randint(1, 10))
        s["fecha_reporte"] = s["fecha_ocurrencia"] + timedelta(days=random.randint(0, 2))
        sin.append(s)

    # --- Patrón: demora en denuncia de robo (> 48h) ---
    for _ in range(50):
        pol = random.choice(polizas_veh) if polizas_veh else random.choice(polizas)
        s = base(pol, "demora_robo", 1)
        s["cobertura"] = "Robo"
        s["fecha_reporte"] = s["fecha_ocurrencia"] + timedelta(days=random.randint(3, 12))
        sin.append(s)

    # --- Patrón: alta frecuencia por asegurado (>=3 siniestros) ---
    for a in random.sample(asegurados, 12):
        pols_a = [p for p in polizas if p["id_asegurado"] == a["id_asegurado"]]
        if not pols_a:
            continue
        for _ in range(random.randint(3, 4)):
            sin.append(base(random.choice(pols_a), "frecuencia_asegurado", 1))

    # --- Patrón: redes (rings). Ring 1 -> train, Ring 2 -> test (proveedores distintos) ---
    def construir_ring(prov_id: str, split: str, n_aseg_ring: int = 6, n_sin: int = 12):
        for p in proveedores:
            if p["id_proveedor"] == prov_id:
                p["en_lista_restrictiva"] = True
        aseg_ring = random.sample(asegurados, n_aseg_ring)
        for _ in range(n_sin):
            a = random.choice(aseg_ring)
            pols_a = [p for p in polizas if p["id_asegurado"] == a["id_asegurado"]]
            if not pols_a:
                continue
            s = base(random.choice(pols_a), "red_proveedor", 1, id_prov=prov_id)
            s["monto_reclamado"] = round(s["monto_reclamado"] * 1.6, 2)
            s["split"] = split
            sin.append(s)

    construir_ring(ring_ids[0], "train")
    construir_ring(ring_ids[1], "test")

    # --- Patrón: narrativa clonada (descripción casi idéntica) ---
    for _ in range(20):
        s = base(random.choice(polizas), "narrativa_clonada", 1)
        s["descripcion"] = NARRATIVA_CLON
        sin.append(s)

    # --- Patrón: documentos inconsistentes (se marca acá, el doc se crea abajo) ---
    for _ in range(30):
        sin.append(base(random.choice(polizas), "doc_inconsistente", 1))

    # --- Patrón: monto cercano a la suma asegurada ---
    for _ in range(25):
        pol = random.choice(polizas)
        s = base(pol, "monto_alto", 1)
        s["monto_reclamado"] = round(pol["suma_asegurada"] * random.uniform(0.95, 1.05), 2)
        s["monto_estimado"] = round(pol["suma_asegurada"] * 0.5, 2)
        sin.append(s)

    # --- Patrón: imposibilidad geográfica (ocurrencia y taller lejos, mismo día) ---
    for _ in range(20):
        pol = random.choice(polizas)
        s = base(pol, "geo_imposible", 1)
        lejana = max(config.CIUDADES, key=lambda c: _haversine_km(pol["ciudad"], c))
        s["ciudad_taller"] = lejana
        sin.append(s)

    # --- Patrón: clima inconsistente (declara lluvia/volcadura pero estuvo seco) ---
    for _ in range(20):
        s = base(random.choice(polizas), "clima_inconsistente", 1)
        s["clima_declarado"] = "Lluvia fuerte"
        s["clima_real"] = "Despejado"
        s["tipo_impacto"] = "volcadura"
        sin.append(s)

    df = pd.DataFrame(sin)

    # --- Campos derivados ---
    foc = pd.to_datetime(df["fecha_ocurrencia"])
    frep = pd.to_datetime(df["fecha_reporte"])
    fi = pd.to_datetime(df["id_poliza"].map(lambda p: pol_by_id[p]["fecha_inicio"]))
    ff = pd.to_datetime(df["id_poliza"].map(lambda p: pol_by_id[p]["fecha_fin"]))
    df["dias_desde_inicio_poliza"] = (foc - fi).dt.days
    df["dias_desde_fin_poliza"] = (ff - foc).dt.days
    df["dias_entre_ocurrencia_reporte"] = (frep - foc).dt.days
    hist = df.groupby("id_asegurado")["id_siniestro"].transform("count")
    df["historial_siniestros_asegurado"] = hist

    # --- Split train/test: estratificado por etiqueta, respetando los rings ya fijados ---
    forzado = df["patron"] == "red_proveedor"
    libres = df.index[~forzado]
    rng = np.random.default_rng(seed)
    test_libres = rng.choice(libres, size=int(len(libres) * 0.30), replace=False)
    df.loc[test_libres, "split"] = "test"

    # --- Documentos ---
    docs = []
    doc_n = 0
    for _, s in df.iterrows():
        inconsistente_patron = s["patron"] == "doc_inconsistente"
        for tipo in ["Denuncia", "Factura", "Informe"]:
            doc_n += 1
            inconsistencia = inconsistente_patron and tipo == "Factura"
            # factura fechada ANTES del evento => bandera de adulteración
            femision = (s["fecha_ocurrencia"] - timedelta(days=random.randint(2, 8))
                        if inconsistencia else
                        s["fecha_ocurrencia"] + timedelta(days=random.randint(0, 5)))
            docs.append(dict(
                id_documento=f"DOC{doc_n:07d}", id_siniestro=s["id_siniestro"],
                tipo_documento=tipo, entregado=not (inconsistente_patron and tipo == "Informe"),
                legible=not inconsistencia, fecha_emision=femision,
                inconsistencia_detectada=inconsistencia,
                observacion="Fecha previa al evento" if inconsistencia else "",
            ))
    # marca documentos_completos=False donde falta un documento
    faltan = df["patron"] == "doc_inconsistente"
    df.loc[faltan, "documentos_completos"] = False

    return {
        "asegurados": pd.DataFrame(asegurados),
        "proveedores": pd.DataFrame(proveedores),
        "polizas": pd.DataFrame(polizas),
        "vehiculos": pd.DataFrame(vehiculos),
        "siniestros": df,
        "documentos": pd.DataFrame(docs),
    }


def escribir(dfs: dict[str, pd.DataFrame]) -> None:
    config.SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)
    for nombre, df in dfs.items():
        df.to_csv(config.SYNTHETIC_DIR / f"{nombre}.csv", index=False)


def main() -> None:
    dfs = generar()
    escribir(dfs)
    s = dfs["siniestros"]
    print(f"Generado en {config.SYNTHETIC_DIR}")
    for nombre, df in dfs.items():
        print(f"  {nombre:12} {len(df):>6} filas")
    n = len(s)
    fraude = int(s["etiqueta_fraude_simulada"].sum())
    print(f"\nSiniestros: {n} | fraude={fraude} ({fraude / n:.1%}) | "
          f"train={int((s['split'] == 'train').sum())} test={int((s['split'] == 'test').sum())}")
    print("\nPatrones plantados:")
    print(s[s["etiqueta_fraude_simulada"] == 1]["patron"].value_counts().to_string())


if __name__ == "__main__":
    main()

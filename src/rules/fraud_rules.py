"""Motor de reglas (E1).

Cada regla devuelve una Contribución `{regla, puntos, evidencia}` o None.
Basado en la sección 7 (señales ponderadas) y 8 (reglas críticas RF) del reto.
Las reglas RF-01..04 son **hard gates**: fuerzan nivel ROJO (ver `scoring/score.py`).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Contribucion:
    regla: str
    puntos: int
    evidencia: str
    gate: bool = False


# --- Señales ponderadas (sección 7) ---

def _borde_vigencia(r):
    d = r["dias_desde_inicio_poliza"]
    if 0 <= d <= 10:
        return Contribucion("Borde de vigencia", 8, f"Siniestro a {int(d)} días del inicio de la póliza (<=10)")
    if 11 <= d <= 30:
        return Contribucion("Borde de vigencia", 4, f"Siniestro a {int(d)} días del inicio (11-30)")
    return None


def _demora_robo(r):
    if r["es_robo"]:
        d = r["dias_entre_ocurrencia_reporte"]
        if d > 2:
            return Contribucion("Demora denuncia robo", 8, f"Robo reportado {int(d)} días después (>48h)")
        if d == 2:
            return Contribucion("Demora denuncia robo", 4, "Robo reportado entre 24 y 48h")
    return None


def _freq_asegurado(r):
    h = r["historial_siniestros_asegurado"]
    if h >= 3:
        return Contribucion("Alta frecuencia asegurado", 8, f"{int(h)} siniestros del asegurado")
    if h == 2:
        return Contribucion("Alta frecuencia asegurado", 4, "2 siniestros del asegurado")
    return None


def _freq_vehiculo(r):
    v = r["freq_vehiculo"]
    if v >= 3:
        return Contribucion("Alta frecuencia vehículo", 6, f"{int(v)} siniestros del mismo vehículo")
    if v == 2:
        return Contribucion("Alta frecuencia vehículo", 3, "2 siniestros del mismo vehículo")
    return None


def _reporte_tardio(r):
    if not r["es_robo"]:
        d = r["dias_entre_ocurrencia_reporte"]
        if d > 7:
            return Contribucion("Reporte tardío", 5, f"Reportado {int(d)} días después del evento (>7)")
        if 4 <= d <= 7:
            return Contribucion("Reporte tardío", 3, f"Reportado {int(d)} días después (4-7)")
    return None


def _narrativa_clonada(r):
    n = r["narrativa_repetidos"]
    if n > 1:
        return Contribucion("Narrativa clonada", 8, f"Descripción idéntica a otros {int(n) - 1} reclamos")
    return None


def _monto_alto(r):
    ratio = r["ratio_monto_suma"]
    if ratio >= 0.95:
        return Contribucion("Monto cercano a suma asegurada", 5, f"Reclamo = {ratio * 100:.0f}% de la suma asegurada")
    return None


def _docs_incompletos(r):
    if r["doc_no_entregado"] or not r["documentos_completos"]:
        return Contribucion("Documentos incompletos", 4, "Falta un documento obligatorio")
    return None


def _geo_atipica(r):
    km = r["distancia_geo_km"]
    if km > 150:
        return Contribucion("Distancia geográfica atípica", 6, f"Ocurrencia y taller a {km:.0f} km")
    return None


# --- Reglas críticas RF (hard gates -> ROJO) ---

def _rf02_doc(r):
    if r["doc_inconsistente"]:
        return Contribucion("RF-02 Adulteración documental", 10, "Factura con fecha previa al evento", gate=True)
    return None


def _rf03_lista(r):
    if r["proveedor_en_lista"] or r["asegurado_en_lista"]:
        quien = "proveedor" if r["proveedor_en_lista"] else "asegurado"
        return Contribucion("RF-03 Lista Restrictiva", 10, f"Coincidencia de {quien} con Lista Restrictiva", gate=True)
    return None


def _rf04_dinamica(r):
    if r["clima_inconsistente"]:
        return Contribucion("RF-04 Dinámica inconsistente", 6,
                            "Clima declarado no coincide con el real (p. ej. volcadura por lluvia en día seco)",
                            gate=True)
    return None


REGLAS = [
    _borde_vigencia, _demora_robo, _freq_asegurado, _freq_vehiculo, _reporte_tardio,
    _narrativa_clonada, _monto_alto, _docs_incompletos, _geo_atipica,
    _rf02_doc, _rf03_lista, _rf04_dinamica,
]


def evaluar_reglas(row) -> list[Contribucion]:
    """Aplica todas las reglas a una fila de features y devuelve las contribuciones activas."""
    contribuciones = []
    for regla in REGLAS:
        c = regla(row)
        if c is not None:
            contribuciones.append(c)
    return contribuciones

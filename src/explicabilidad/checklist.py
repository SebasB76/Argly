"""Checklist de investigación por caso.

Define los pasos que el analista debería completar antes de escalar. Hay pasos
BASE (siempre, requeridos) y pasos DINÁMICOS que se agregan según las señales
activas del caso (p. ej. si hay inconsistencia documental, aparece 'validar
autenticidad de la factura'). El caso queda 'listo para escalar' cuando se
completan los pasos requeridos.
"""
from __future__ import annotations

_BASE = [
    {"clave": "doc", "label": "Revisar documentación del siniestro", "requerido": True},
    {"clave": "asegurado", "label": "Contactar / verificar al asegurado", "requerido": True},
    {"clave": "proveedor", "label": "Revisar historial del proveedor", "requerido": True},
]

# (palabras clave en la regla -> paso dinámico)
_DINAMICOS = [
    (["documental", "inconsistente", "rf-02", "adulter"],
     {"clave": "factura", "label": "Validar autenticidad de la factura (fechas)", "requerido": False}),
    (["lista restrictiva", "rf-03"],
     {"clave": "lista", "label": "Confirmar coincidencia con lista restrictiva", "requerido": False}),
    (["geo", "distancia"],
     {"clave": "geo", "label": "Verificar ubicación (ocurrencia vs taller)", "requerido": False}),
    (["dinámica", "rf-04", "impacto", "clima"],
     {"clave": "dinamica", "label": "Validar dinámica del accidente", "requerido": False}),
    (["narrativa"],
     {"clave": "narrativa", "label": "Comparar narrativa con casos similares", "requerido": False}),
    (["ptxrb", "rf-01", "pérdida total"],
     {"clave": "ptxrb", "label": "Verificar condiciones de pérdida total por robo", "requerido": False}),
]


def pasos(contribuciones: list[dict]) -> list[dict]:
    """Lista de pasos (base + dinámicos según señales) para un caso."""
    reglas = " ".join(c.get("regla", "").lower() for c in (contribuciones or []))
    out = [dict(p) for p in _BASE]
    vistos = {p["clave"] for p in out}
    for claves, paso in _DINAMICOS:
        if paso["clave"] not in vistos and any(k in reglas for k in claves):
            out.append(dict(paso))
            vistos.add(paso["clave"])
    return out


def estado_checklist(contribuciones: list[dict], hechos: set[str]) -> dict:
    """Combina los pasos con lo ya completado y calcula si está listo para escalar."""
    ps = pasos(contribuciones)
    for p in ps:
        p["hecho"] = p["clave"] in hechos
    requeridos = [p for p in ps if p["requerido"]]
    listo = all(p["hecho"] for p in requeridos) if requeridos else False
    return {
        "pasos": ps,
        "completados": sum(1 for p in ps if p["hecho"]),
        "total": len(ps),
        "requeridos": len(requeridos),
        "requeridos_hechos": sum(1 for p in requeridos if p["hecho"]),
        "listo_para_escalar": listo,
    }

"""Explicación contrafactual (Explicabilidad y Ética).

Responde "¿qué tendría que cambiar para que este caso pase a VERDE?". Como el
score de Argly es transparente (suma de contribuciones + hard gates), el
contrafactual es directo: hay que (1) neutralizar los gates activos y
(2) retirar las mayores contribuciones hasta que la suma quede en rango VERDE.

Es una explicación accionable, NO una recomendación de cómo evadir el control:
le muestra al analista qué factores empujan el riesgo y cuánto pesa cada uno.
"""
from __future__ import annotations

from src import config

# Cada regla -> la condición que, de cambiar, la desactivaría (en lenguaje de negocio).
_ACCIONES = [
    ("borde de vigencia", "el siniestro no ocurriría en los primeros días de vigencia de la póliza"),
    ("demora", "la denuncia se haría dentro de las primeras 24 horas"),
    ("reporte tardío", "el evento se reportaría dentro de los 3 días"),
    ("conductor", "el conductor no acumularía siniestros recientes"),
    ("vehículo", "el vehículo no acumularía siniestros recientes"),
    ("asegurado", "el asegurado no acumularía siniestros recientes"),
    ("solo rc", "no habría frecuencia atípica de reclamos solo de RC"),
    ("monto", "el monto reclamado quedaría bien por debajo de la suma asegurada"),
    ("sin tercero", "el tercero involucrado quedaría identificado"),
    ("documentos incompletos", "se completaría la documentación obligatoria"),
    ("rf-02", "los documentos no presentarían inconsistencias de fecha"),
    ("adulteración", "los documentos no presentarían inconsistencias de fecha"),
    ("rf-03", "ni el asegurado ni el proveedor estarían en lista restrictiva"),
    ("lista restrictiva", "ni el asegurado ni el proveedor estarían en lista restrictiva"),
    ("rf-04", "el relato sería consistente con el tipo de impacto"),
    ("dinámica", "el relato sería consistente con el tipo de impacto"),
    ("rf-01", "no se trataría de pérdida total por robo"),
    ("ptxrb", "no se trataría de pérdida total por robo"),
    ("geo", "ocurrencia y taller estarían en la misma zona geográfica"),
    ("clima", "el clima declarado coincidiría con el real"),
    ("narrativa", "la narrativa no sería casi idéntica a la de otro reclamo"),
    ("proveedor", "el proveedor no concentraría casos observados"),
    ("modelo ml", "bajaría la probabilidad estimada por el modelo (ver factores del modelo)"),
    ("anomalía", "el caso dejaría de ser estadísticamente atípico"),
]


def _accion(regla: str) -> str:
    r = regla.lower()
    for clave, texto in _ACCIONES:
        if clave in r:
            return texto
    return "cambiaría el factor de riesgo asociado"


def contrafactual(contribuciones: list[dict], umbral_verde: int = config.UMBRAL_VERDE) -> dict:
    """Calcula el conjunto mínimo de cambios que llevaría el caso a VERDE.

    `contribuciones` es la lista de dicts {regla, puntos, evidencia, gate}.
    Estrategia: quitar primero los gates (obligatorio para salir de ROJO-por-gate)
    y luego las contribuciones de mayor peso hasta que la suma quede <= umbral.
    """
    suma = sum(int(c["puntos"]) for c in contribuciones)
    gates = [c for c in contribuciones if c.get("gate")]
    no_gate = sorted((c for c in contribuciones if not c.get("gate")),
                     key=lambda c: int(c["puntos"]), reverse=True)

    nivel_actual = ("ROJO" if gates else config.clasificar_riesgo(min(suma, 100)))
    if nivel_actual == "VERDE":
        return {"ya_verde": True, "alcanzable": True, "cambios": [],
                "score_proyectado": min(suma, 100), "nivel_proyectado": "VERDE"}

    cambios, rem = [], suma
    for c in sorted(gates, key=lambda c: int(c["puntos"]), reverse=True):
        cambios.append(_a_cambio(c))
        rem -= int(c["puntos"])
    for c in no_gate:
        if rem <= umbral_verde:
            break
        cambios.append(_a_cambio(c))
        rem -= int(c["puntos"])

    score_proy = max(0, int(rem))
    nivel_proy = config.clasificar_riesgo(score_proy)   # sin gates ya no hay piso ROJO
    return {
        "ya_verde": False,
        "alcanzable": nivel_proy == "VERDE",
        "cambios": cambios,
        "score_proyectado": score_proy,
        "nivel_proyectado": nivel_proy,
        "resumen": _resumen(cambios, score_proy),
    }


def _a_cambio(c: dict) -> dict:
    return {"regla": c["regla"], "puntos": int(c["puntos"]), "gate": bool(c.get("gate")),
            "evidencia": c.get("evidencia", ""), "accion": _accion(c["regla"])}


def _resumen(cambios: list[dict], score_proy: int) -> str:
    if not cambios:
        return "El caso ya está en rango VERDE."
    n = len(cambios)
    return (f"Si {'se neutralizara' if n == 1 else 'se neutralizaran'} {n} "
            f"factor{'es' if n > 1 else ''} de riesgo, el score bajaría a ~{score_proy} (VERDE).")

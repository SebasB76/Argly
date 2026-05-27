"""Notificaciones de alerta (E6).

El envío real por WhatsApp/correo requiere credenciales (fuera de alcance del
prototipo). Aquí se FORMATEAN los mensajes (demoables) y `enviar` es un stub que
devuelve el payload que se enviaría.
"""
from __future__ import annotations


def formato_whatsapp(d: dict) -> str:
    return (
        "🚨 *Alerta Argly*\n"
        f"Siniestro {d['id_siniestro']} — *{d['nivel']}* ({d['score']}/100)\n"
        f"Motivo: {d['motivo_principal']}\n"
        f"Acción: {d['recomendacion']}\n"
        f"_{d['aviso']}_"
    )


def formato_correo(d: dict) -> dict:
    cuerpo = (
        f"Siniestro {d['id_siniestro']} clasificado {d['nivel']} (score {d['score']}/100).\n"
        f"Motivo principal: {d['motivo_principal']}.\n"
        f"Recomendación: {d['recomendacion']}.\n\n"
        f"{d['aviso']}"
    )
    return {"asunto": f"[Argly] Alerta {d['nivel']} — {d['id_siniestro']}", "cuerpo": cuerpo}


def enviar(canal: str, destino: str, d: dict) -> dict:
    """Stub: en producción enviaría por el canal. Aquí devuelve el payload formateado."""
    payload = formato_whatsapp(d) if canal == "whatsapp" else formato_correo(d)
    return {"canal": canal, "destino": destino, "enviado": False,
            "motivo": "stub sin credenciales", "payload": payload}

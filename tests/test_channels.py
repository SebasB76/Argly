"""Tests de canales/salidas (E6): PDF dossier, aviso y push."""
from fastapi.testclient import TestClient

from src.app.main import app, _detalle, _bandeja
from src.channels.pdf_dossier import generar_dossier
from src.channels import notify

client = TestClient(app)


def _un_rojo():
    b = _bandeja()
    return b[b["nivel"] == "ROJO"].iloc[0]["id_siniestro"]


def test_pdf_valido():
    pdf = generar_dossier(_detalle(_un_rojo()))
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000


def test_endpoint_dossier():
    r = client.get(f"/api/casos/{_un_rojo()}/dossier")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"


def test_aviso_formato():
    d = _detalle(_un_rojo())
    wa = notify.formato_whatsapp(d)
    assert "Alerta Argly" in wa and d["id_siniestro"] in wa
    correo = notify.formato_correo(d)
    assert "asunto" in correo and "cuerpo" in correo


def test_endpoint_push():
    r = client.post(f"/api/casos/{_un_rojo()}/push").json()
    assert r["ok"] is True
    assert "core de siniestros" in r["mensaje"]

"""Tests del reporte ejecutivo consolidado (PDF + Excel)."""
from __future__ import annotations

import io
import zipfile

from fastapi.testclient import TestClient

from src.app.main import app

client = TestClient(app)


def test_reporte_pdf_se_genera():
    r = client.get("/api/reporte/pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF" and len(r.content) > 1500


def test_reporte_excel_se_genera_con_hojas():
    r = client.get("/api/reporte/excel")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers["content-type"]
    # un .xlsx es un zip; verificamos que abre y trae las hojas esperadas
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    nombres = zf.read("xl/workbook.xml").decode("utf-8", "ignore")
    for hoja in ("Resumen", "Bandeja", "Top rojos"):
        assert hoja in nombres

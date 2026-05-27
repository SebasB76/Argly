"""Dossier de investigación en PDF por caso (E6, ReportLab).

Toma el detalle de un caso (mismo shape que GET /api/casos/{id}) y arma un PDF
listo para que la Unidad Antifraude lo revise o lo archive (auditoría).
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HEX = {"ROJO": "#c0392b", "AMARILLO": "#b7950b", "VERDE": "#1e8449"}


def generar_dossier(d: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=18 * mm, bottomMargin=18 * mm,
                            leftMargin=18 * mm, rightMargin=18 * mm)
    st = getSampleStyleSheet()
    hexc = _HEX.get(d["nivel"], "#333333")

    e = [
        Paragraph(f"Dossier de investigación — {d['id_siniestro']}", st["Title"]),
        Paragraph(f'Nivel <font color="{hexc}"><b>{d["nivel"]}</b></font> · Score {d["score"]}/100', st["Heading2"]),
        Paragraph(f"<b>Recomendación:</b> {d['recomendacion']}", st["Normal"]),
        Spacer(1, 5 * mm),
    ]

    info = [
        ["Ramo", d["ramo"]], ["Cobertura", d["cobertura"]], ["Sucursal", d["sucursal"]],
        ["Monto reclamado", f"${d['monto_reclamado']:,.2f}"],
        ["Proveedor", d["id_proveedor"]], ["Asegurado", d["id_asegurado"]],
    ]
    ti = Table(info, colWidths=[40 * mm, 120 * mm])
    ti.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    e += [ti, Spacer(1, 5 * mm), Paragraph("Señales detectadas (evidencia)", st["Heading3"])]

    filas = [["Regla", "Pts", "Evidencia"]]
    for c in d["contribuciones"]:
        filas.append([Paragraph(c["regla"], st["BodyText"]), str(c["puntos"]),
                      Paragraph(c["evidencia"], st["BodyText"])])
    tc = Table(filas, colWidths=[45 * mm, 12 * mm, 103 * mm])
    tc.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2030")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    e += [tc, Spacer(1, 6 * mm), Paragraph(f"<i>{d['aviso']}</i>", st["Normal"])]

    doc.build(e)
    return buf.getvalue()

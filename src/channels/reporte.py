"""Reporte ejecutivo CONSOLIDADO de toda la bandeja (E6).

Mientras `pdf_dossier` arma el PDF de UN caso, aquí se genera el resumen
ejecutivo de TODA la operación (CU-06 del reto: "resumen ejecutivo de casos de
mayor riesgo") en dos formatos para auditoría:

- PDF: KPIs + métricas + top de casos + Pareto de proveedores + distribución
  por ramo/ciudad + equidad + aviso ético.
- Excel: libro multi-hoja (Resumen, Bandeja completa, Top rojos, Pareto, Ramos)
  para que un auditor lo filtre y archive.
"""
from __future__ import annotations

from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_HEX = {"ROJO": "#c0392b", "AMARILLO": "#b7950b", "VERDE": "#1e8449"}
_AZUL = colors.HexColor("#1a2030")


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def _tabla(filas, anchos, st, header=True):
    t = Table(filas, colWidths=anchos)
    estilo = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f8")]),
    ]
    if header:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), _AZUL),
                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(estilo))
    return t


def generar_reporte_pdf(d: dict) -> bytes:
    """`d` = dict consolidado (ver `_datos_reporte` en la API)."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="Reporte ejecutivo Argly")
    st = getSampleStyleSheet()
    r = d["resumen"]
    n = r["por_nivel"]
    e = [
        Paragraph("Argly — Reporte ejecutivo antifraude", st["Title"]),
        Paragraph(f"Generado: {d['fecha']} · dataset: {d.get('origen', 'sintetico')} · "
                  f"modo: {d.get('modo', '—')}", st["Normal"]),
        Spacer(1, 4 * mm),
    ]

    # --- KPIs ---
    e.append(Paragraph("Panorama", st["Heading2"]))
    kpis = [["Total", "🔴 Rojo", "🟡 Amarillo", "🟢 Verde", "Monto en revisión", "Ahorro estimado"],
            [f"{r['total']:,}", str(n.get("ROJO", 0)), str(n.get("AMARILLO", 0)),
             str(n.get("VERDE", 0)), f"${r['monto_en_revision']:,.0f}",
             f"${r.get('ahorro_estimado', 0):,.0f}"]]
    e += [_tabla(kpis, [22 * mm, 20 * mm, 26 * mm, 22 * mm, 38 * mm, 36 * mm], st),
          Spacer(1, 4 * mm)]

    # --- Métricas del modelo ---
    m = d.get("metricas")
    if m:
        e.append(Paragraph("Desempeño del modelo (test held-out)", st["Heading3"]))
        mf = [["AUC híbrido", "AUC ML", "Precisión", "Recall", "F1", "n test"],
              [str(m.get("auc_hibrido")), str(m.get("auc_ml")), str(m.get("precision")),
               str(m.get("recall")), str(m.get("f1")), str(m.get("n_test"))]]
        e += [_tabla(mf, [28 * mm] * 6, st), Spacer(1, 4 * mm)]

    # --- Top casos ---
    e.append(Paragraph("Casos de mayor riesgo", st["Heading3"]))
    filas = [["#", "Siniestro", "Score", "Nivel", "Motivo principal", "Monto"]]
    for i, c in enumerate(d["top"], 1):
        hexc = _HEX.get(c["nivel"], "#333")
        filas.append([str(i), c["id_siniestro"], str(c["score"]),
                      Paragraph(f'<font color="{hexc}"><b>{c["nivel"]}</b></font>', st["BodyText"]),
                      Paragraph(c["motivo_principal"], st["BodyText"]),
                      f"${c['monto_reclamado']:,.0f}"])
    e += [_tabla(filas, [8 * mm, 30 * mm, 16 * mm, 22 * mm, 60 * mm, 28 * mm], st),
          Spacer(1, 4 * mm)]

    # --- Pareto de proveedores ---
    p = d.get("pareto")
    if p and p.get("proveedores"):
        e.append(Paragraph("Concentración de proveedores (Pareto)", st["Heading3"]))
        e.append(Paragraph(p["interpretacion"], st["Normal"]))
        filas = [["Proveedor", "Alertas", "% acumulado", "Monto"]]
        for x in p["proveedores"]:
            filas.append([x["id_proveedor"], str(x["alertas"]), f"{x['pct_acumulado']}%",
                          f"${x['monto']:,.0f}"])
        e += [Spacer(1, 2 * mm), _tabla(filas, [40 * mm, 24 * mm, 30 * mm, 36 * mm], st),
              Spacer(1, 4 * mm)]

    # --- Distribución por ramo + ciudades ---
    ramos = d.get("ramos") or []
    if ramos:
        e.append(Paragraph("Por ramo y ciudad", st["Heading3"]))
        fr = [["Ramo", "Total", "Sospechosos", "%"]]
        for x in ramos:
            fr.append([x["ramo"], str(x["total"]), str(x["sospechosos"]), f"{x['pct']}%"])
        e += [_tabla(fr, [40 * mm, 24 * mm, 30 * mm, 22 * mm], st), Spacer(1, 3 * mm)]
    ciudades = d.get("ciudades") or []
    if ciudades:
        fc = [["Ciudad", "Alertas"]]
        for x in ciudades[:8]:
            fc.append([x.get("ciudad", x.get("sucursal", "—")), str(x.get("alertas", x.get("sospechosos", 0)))])
        e += [_tabla(fc, [50 * mm, 30 * mm], st), Spacer(1, 4 * mm)]

    # --- Equidad / sesgo ---
    s = d.get("sesgo")
    if s:
        e.append(Paragraph("Equidad (disparate impact, regla 4/5)", st["Heading3"]))
        rev = s.get("atributos_a_revisar") or []
        txt = ("Sin disparidades relevantes entre grupos." if not rev
               else f"Atributos a revisar por disparidad: <b>{', '.join(rev)}</b>.")
        e.append(Paragraph(txt, st["Normal"]))
        fs = [["Atributo", "Disparidad", "Veredicto"]]
        for attr, v in s.get("atributos", {}).items():
            fs.append([attr, str(v.get("disparidad", "—")), v.get("veredicto", "—") or "—"])
        e += [Spacer(1, 2 * mm), _tabla(fs, [40 * mm, 30 * mm, 30 * mm], st), Spacer(1, 5 * mm)]

    e.append(Paragraph(f"<i>{d['aviso']}</i>", st["Normal"]))
    doc.build(e)
    return buf.getvalue()


# --------------------------------------------------------------------------- #
# Excel
# --------------------------------------------------------------------------- #
_COLS_BANDEJA = {
    "id_siniestro": "Siniestro", "score": "Score", "nivel": "Nivel", "gate": "Gate",
    "motivo_principal": "Motivo principal", "n_alertas": "N alertas", "ramo": "Ramo",
    "cobertura": "Cobertura", "sucursal": "Ciudad", "monto_reclamado": "Monto reclamado",
    "id_proveedor": "Proveedor", "id_asegurado": "Asegurado",
}


def generar_reporte_excel(bandeja: pd.DataFrame, pareto: dict | None = None,
                          ramos: list | None = None, resumen: dict | None = None) -> bytes:
    """Libro Excel multi-hoja para auditoría."""
    cols = [c for c in _COLS_BANDEJA if c in bandeja.columns]
    band = bandeja[cols].rename(columns=_COLS_BANDEJA)
    rojos = band[band["Nivel"] == "ROJO"] if "Nivel" in band.columns else band.head(0)

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        if resumen:
            n = resumen["por_nivel"]
            pd.DataFrame([
                {"Métrica": "Total siniestros", "Valor": resumen["total"]},
                {"Métrica": "Rojo", "Valor": n.get("ROJO", 0)},
                {"Métrica": "Amarillo", "Valor": n.get("AMARILLO", 0)},
                {"Métrica": "Verde", "Valor": n.get("VERDE", 0)},
                {"Métrica": "Monto en revisión", "Valor": resumen["monto_en_revision"]},
                {"Métrica": "Ahorro estimado", "Valor": resumen.get("ahorro_estimado", 0)},
            ]).to_excel(xl, sheet_name="Resumen", index=False)
        band.to_excel(xl, sheet_name="Bandeja", index=False)
        rojos.to_excel(xl, sheet_name="Top rojos", index=False)
        if pareto and pareto.get("proveedores"):
            pd.DataFrame(pareto["proveedores"]).to_excel(xl, sheet_name="Proveedores Pareto", index=False)
        if ramos:
            pd.DataFrame(ramos).to_excel(xl, sheet_name="Por ramo", index=False)
        # ancho de columnas legible
        for ws in xl.book.worksheets:
            for col in ws.columns:
                ancho = max((len(str(c.value)) for c in col if c.value is not None), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max(ancho + 2, 10), 42)
    return buf.getvalue()

"""Genera los 3 notebooks sugeridos por el reto (sección 15) usando el pipeline real.

Ejecutar: python -m scripts.gen_notebooks
"""
from __future__ import annotations

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from src import config

NB_DIR = config.ROOT / "notebooks"

# Celda de arranque: deja `src` importable corra el notebook desde notebooks/ o raíz.
_SETUP = (
    "import sys, pathlib\n"
    "p = pathlib.Path.cwd()\n"
    "while not (p / 'src').exists() and p != p.parent:\n"
    "    p = p.parent\n"
    "sys.path.insert(0, str(p))"
)


def _save(nb, nombre: str) -> None:
    NB_DIR.mkdir(parents=True, exist_ok=True)
    with open(NB_DIR / nombre, "w", encoding="utf-8") as fh:
        nbf.write(nb, fh)
    print(f"  {nombre}")


def exploracion() -> None:
    nb = new_notebook(cells=[
        new_markdown_cell(
            "# 01 · Exploración de datos — Argly\n"
            "Dataset sintético (semilla fija) de siniestros con patrones de posible fraude "
            "**plantados y etiquetados**. 100% sintético, sin PII."),
        new_code_cell(_SETUP),
        new_code_cell(
            "from src.ingestion.generate_synthetic import generar\n"
            "dfs = generar(seed=42)\n"
            "{k: len(v) for k, v in dfs.items()}"),
        new_markdown_cell("## Tablas del reto y sus columnas"),
        new_code_cell(
            "for k, v in dfs.items():\n"
            "    print(f'\\n=== {k} ({len(v)} filas) ===')\n"
            "    print(list(v.columns))"),
        new_markdown_cell("## Distribución de patrones plantados (ground-truth)"),
        new_code_cell(
            "s = dfs['siniestros']\n"
            "print('Fraude simulado:', int(s['etiqueta_fraude_simulada'].sum()), 'de', len(s))\n"
            "s[s['etiqueta_fraude_simulada'] == 1]['patron'].value_counts()"),
        new_markdown_cell("## Train / test separados (rings con proveedores distintos)"),
        new_code_cell("s['split'].value_counts()"),
        new_code_cell(
            "import matplotlib.pyplot as plt\n"
            "s['ramo'].value_counts().plot(kind='bar', title='Siniestros por ramo')\n"
            "plt.tight_layout(); plt.show()"),
    ])
    _save(nb, "01_exploracion_datos.ipynb")


def modelo() -> None:
    nb = new_notebook(cells=[
        new_markdown_cell(
            "# 02 · Modelo de fraude — Argly\n"
            "Scoring **híbrido**: reglas (rúbrica + RF gates) + ML supervisado (RandomForest) "
            "+ anomalías (Isolation Forest). El desglose ES la lista de contribuciones."),
        new_code_cell(_SETUP),
        new_code_cell(
            "from src.ingestion.generate_synthetic import generar\n"
            "from src.features.build_features import construir_features\n"
            "from src.models.ml_model import entrenar, explicacion_global\n"
            "dfs = generar(seed=42)\n"
            "F = construir_features(dfs)\n"
            "modelo, prob = entrenar(F)\n"
            "F.shape"),
        new_markdown_cell("## Explicabilidad global del modelo (SHAP si está instalado)"),
        new_code_cell(
            "exp = explicacion_global(modelo, F)\n"
            "print('método:', exp['metodo'])\n"
            "exp['importancias']"),
        new_markdown_cell("## Bandeja priorizada (score 0-100 + semáforo)"),
        new_code_cell(
            "from src.pipeline import construir_bandeja\n"
            "b = construir_bandeja(dfs)\n"
            "b['nivel'].value_counts()"),
        new_code_cell(
            "b[['id_siniestro','score','nivel','motivo_principal','monto_reclamado']].head(10)"),
    ])
    _save(nb, "02_modelo_fraude.ipynb")


def evaluacion() -> None:
    nb = new_notebook(cells=[
        new_markdown_cell(
            "# 03 · Evaluación del modelo — Argly\n"
            "Métricas sobre el **test held-out** (variantes de patrón no vistas en train)."),
        new_code_cell(_SETUP),
        new_code_cell(
            "from src.ingestion.generate_synthetic import generar\n"
            "from src.pipeline import evaluar_metricas\n"
            "dfs = generar(seed=42)\n"
            "evaluar_metricas(dfs)"),
        new_markdown_cell(
            "**Lectura:** el AUC híbrido supera al de solo-reglas y el ML no degrada el ranking. "
            "Precisión alta = pocas falsas alarmas para el analista."),
        new_markdown_cell("## Matriz de confusión (alerta = amarillo o rojo)"),
        new_code_cell(
            "from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay\n"
            "from src.features.build_features import construir_features\n"
            "from src.models.ml_model import entrenar\n"
            "from src.anomaly.detector import detectar\n"
            "from src.scoring.score import puntuar_features\n"
            "F = construir_features(dfs)\n"
            "_, prob = entrenar(F); anom = detectar(F)\n"
            "P = puntuar_features(F, prob, anom)\n"
            "test = (F['split'] == 'test').values\n"
            "y = F['etiqueta_fraude_simulada'].astype(int).values[test]\n"
            "pred = (P['score'].values[test] >= 41).astype(int)\n"
            "ConfusionMatrixDisplay(confusion_matrix(y, pred)).plot(); None"),
    ])
    _save(nb, "03_evaluacion_modelo.ipynb")


def main() -> None:
    print("Generando notebooks en", NB_DIR)
    exploracion()
    modelo()
    evaluacion()


if __name__ == "__main__":
    main()

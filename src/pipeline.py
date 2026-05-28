"""Pipeline del núcleo: datos -> features -> reglas + ML + anomalía -> score -> bandeja.

La bandeja es la salida central: una fila por siniestro, ordenada por score de
riesgo, con nivel de semáforo, nº de alertas y motivo principal. En modo híbrido
(por defecto) suma al score las contribuciones del modelo ML y de anomalías; en
modo solo-reglas usa únicamente el motor de reglas (E1).

Uso:
    python -m src.pipeline
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.ingestion.generate_synthetic import generar
from src.features.build_features import construir_features
from src.scoring.score import puntuar_features
from src.models.ml_model import entrenar
from src.anomaly.detector import detectar


def construir_bandeja(dfs: dict | None = None, hibrido: bool = True) -> pd.DataFrame:
    if dfs is None:
        dfs = generar()
    F = construir_features(dfs)
    prob = anom = None
    if hibrido:
        _, prob = entrenar(F)
        anom = detectar(F)
    P = puntuar_features(F, prob, anom)
    cols = ["id_siniestro", "ramo", "cobertura", "sucursal", "monto_reclamado",
            "fecha_ocurrencia", "id_asegurado", "id_proveedor", "split", "etiqueta_fraude_simulada"]
    b = dfs["siniestros"][cols].merge(P, on="id_siniestro", how="left")
    b["n_alertas"] = b["contribuciones"].map(len)
    if prob is not None:
        b["probabilidad_ml"] = b["probabilidad_ml"].fillna(0.0)
    if anom is not None and "rareza_anomalia" in b.columns:
        b["rareza_anomalia"] = b["rareza_anomalia"].fillna(0.0)

    def _motivo(cs):
        if not cs:
            return "Sin alertas"
        gates = [c for c in cs if c.get("gate")]   # el gate es la razón decisiva del ROJO
        return max(gates or cs, key=lambda c: c["puntos"])["regla"]

    b["motivo_principal"] = b["contribuciones"].map(_motivo)
    return b.sort_values("score", ascending=False).reset_index(drop=True)


def evaluar_metricas(dfs: dict | None = None) -> dict:
    """Métricas sobre el test held-out: AUC solo-reglas vs híbrido vs ML, y P/R/F1 del híbrido."""
    from sklearn.metrics import roc_auc_score, precision_recall_fscore_support

    if dfs is None:
        dfs = generar()
    F = construir_features(dfs)
    _, prob = entrenar(F)
    anom = detectar(F)
    P_reglas = puntuar_features(F)
    P_hibrido = puntuar_features(F, prob, anom)
    test = (F["split"] == "test").values
    y = F["etiqueta_fraude_simulada"].astype(int).values[test]
    pred_alerta = (P_hibrido["score"].values[test] >= 41).astype(int)   # alerta = amarillo o rojo
    p, r, f1, _ = precision_recall_fscore_support(y, pred_alerta, average="binary", zero_division=0)
    return {
        "n_test": int(test.sum()),
        "auc_reglas": round(float(roc_auc_score(y, P_reglas["score"].values[test])), 3),
        "auc_hibrido": round(float(roc_auc_score(y, P_hibrido["score"].values[test])), 3),
        "auc_ml": round(float(roc_auc_score(y, prob.values[test])), 3),
        "precision": round(float(p), 3),
        "recall": round(float(r), 3),
        "f1": round(float(f1), 3),
    }


def main() -> None:
    dfs = generar()
    b = construir_bandeja(dfs)
    out_dir = config.DATA_DIR / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    cols_csv = ["id_siniestro", "score", "nivel", "gate", "n_alertas", "motivo_principal",
                "ramo", "cobertura", "sucursal", "monto_reclamado", "id_proveedor", "id_asegurado"]
    b[cols_csv].to_csv(out_dir / "bandeja.csv", index=False)
    print(f"Bandeja -> {out_dir / 'bandeja.csv'}  ({len(b)} casos)")
    print("\nDistribución de semáforo:")
    print(b["nivel"].value_counts().to_string())
    print("\nMétricas (test held-out):")
    for k, v in evaluar_metricas(dfs).items():
        print(f"  {k:12} {v}")
    print("\nTop 10 de mayor riesgo:")
    print(b[["id_siniestro", "score", "nivel", "motivo_principal", "monto_reclamado"]]
          .head(10).to_string(index=False))


if __name__ == "__main__":
    main()

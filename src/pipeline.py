"""Pipeline E1: datos -> features -> reglas/score -> bandeja priorizada.

La bandeja es la salida central del núcleo: una fila por siniestro, ordenada por
score de riesgo descendente, con nivel de semáforo, número de alertas y el motivo
principal. La API (E3) la sirve; el analista la revisa.

Uso:
    python -m src.pipeline
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.ingestion.generate_synthetic import generar
from src.features.build_features import construir_features
from src.scoring.score import puntuar_features


def construir_bandeja(dfs: dict | None = None) -> pd.DataFrame:
    if dfs is None:
        dfs = generar()
    P = puntuar_features(construir_features(dfs))
    cols = ["id_siniestro", "ramo", "cobertura", "sucursal", "monto_reclamado",
            "fecha_ocurrencia", "id_asegurado", "id_proveedor", "split", "etiqueta_fraude_simulada"]
    b = dfs["siniestros"][cols].merge(P, on="id_siniestro", how="left")
    b["n_alertas"] = b["contribuciones"].map(len)

    def _motivo(cs):
        if not cs:
            return "Sin alertas"
        gates = [c for c in cs if c.get("gate")]   # el gate es la razón decisiva del ROJO
        return max(gates or cs, key=lambda c: c["puntos"])["regla"]

    b["motivo_principal"] = b["contribuciones"].map(_motivo)
    return b.sort_values("score", ascending=False).reset_index(drop=True)


def main() -> None:
    b = construir_bandeja()
    out_dir = config.DATA_DIR / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    cols_csv = ["id_siniestro", "score", "nivel", "gate", "n_alertas", "motivo_principal",
                "ramo", "cobertura", "sucursal", "monto_reclamado", "id_proveedor", "id_asegurado"]
    b[cols_csv].to_csv(out_dir / "bandeja.csv", index=False)
    print(f"Bandeja -> {out_dir / 'bandeja.csv'}  ({len(b)} casos)")
    print("\nDistribución de semáforo:")
    print(b["nivel"].value_counts().to_string())
    print("\nTop 10 de mayor riesgo:")
    print(b[["id_siniestro", "score", "nivel", "motivo_principal", "monto_reclamado"]]
          .head(10).to_string(index=False))


if __name__ == "__main__":
    main()

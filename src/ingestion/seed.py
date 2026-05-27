"""Carga el dataset sintético a la base de datos (SQLite por defecto, o Postgres).

Uso:
    python -m src.ingestion.seed                  # SQLite local
    DATABASE_URL=postgresql+psycopg2://argly:argly@localhost:5432/argly \\
        python -m src.ingestion.seed              # Postgres (docker compose up -d)
"""
from __future__ import annotations

import numpy as np

from src.ingestion.db import Base, get_engine, get_sessionmaker
from src.ingestion import models

TABLAS = [
    ("asegurados", models.Asegurado),
    ("proveedores", models.Proveedor),
    ("polizas", models.Poliza),
    ("vehiculos", models.Vehiculo),
    ("siniestros", models.Siniestro),
    ("documentos", models.Documento),
]


def _records(df) -> list[dict]:
    """Convierte tipos numpy a tipos nativos de Python (compatibles con cualquier driver)."""
    out = []
    for row in df.to_dict("records"):
        clean = {}
        for k, v in row.items():
            if isinstance(v, np.integer):
                v = int(v)
            elif isinstance(v, np.floating):
                v = float(v)
            elif isinstance(v, (np.bool_, bool)):
                v = bool(v)
            clean[k] = v
        out.append(clean)
    return out


def seed(url: str | None = None, dfs: dict | None = None):
    """Crea el esquema y carga los datos. Devuelve el engine."""
    if dfs is None:
        from src.ingestion.generate_synthetic import generar
        dfs = generar()
    engine = get_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = get_sessionmaker(engine)
    with Session() as s:
        for nombre, model in TABLAS:
            cols = [c.name for c in model.__table__.columns]
            s.bulk_insert_mappings(model, _records(dfs[nombre][cols]))
        s.commit()
    return engine


def main() -> None:
    engine = seed()
    print(f"Seed completado en: {engine.url}")
    for nombre, model in TABLAS:
        with get_sessionmaker(engine)() as s:
            n = s.query(model).count()
        print(f"  {nombre:12} {n:>6} filas")


if __name__ == "__main__":
    main()

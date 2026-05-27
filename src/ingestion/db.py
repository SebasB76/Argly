"""Conexión a la base de datos (DB-agnóstico vía SQLAlchemy).

Por defecto usa SQLite local (cero fricción para dev/tests). En producción/demo
se apunta a Postgres con la variable de entorno DATABASE_URL, p. ej.:

    DATABASE_URL=postgresql+psycopg2://argly:argly@localhost:5432/argly
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src import config

Base = declarative_base()


def default_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///" + str(config.DATA_DIR / "argly.db"))


def get_engine(url: str | None = None):
    return create_engine(url or default_url(), future=True)


def get_sessionmaker(engine=None):
    return sessionmaker(bind=engine or get_engine(), future=True)

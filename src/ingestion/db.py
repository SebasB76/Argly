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


def _normalizar(url: str) -> str:
    """Render/Neon/Heroku entregan 'postgres://', que SQLAlchemy 2 ya no acepta;
    se traduce al driver explícito 'postgresql+psycopg2://'."""
    if url and url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    return url


def default_url() -> str:
    return _normalizar(os.environ.get("DATABASE_URL", "")) or "sqlite:///" + str(config.DATA_DIR / "argly.db")


def get_engine(url: str | None = None):
    return create_engine(_normalizar(url) if url else default_url(), future=True)


def get_sessionmaker(engine=None):
    return sessionmaker(bind=engine or get_engine(), future=True)

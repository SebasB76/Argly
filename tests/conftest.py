"""Configuración de pytest: aísla la DB de los tests.

La API ahora usa la DB como fuente de verdad (auto-siembra el sintético si está
vacía). Apuntamos DATABASE_URL a un SQLite temporal por sesión para no tocar el
`data/argly.db` de desarrollo ni filtrar datos importados entre corridas.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _db_aislada(tmp_path_factory):
    d = tmp_path_factory.mktemp("argly_db")
    os.environ["DATABASE_URL"] = f"sqlite:///{(d / 'argly_test.db').as_posix()}"
    yield

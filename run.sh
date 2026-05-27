#!/usr/bin/env bash
# Argly - arranque. Uso: ./run.sh {setup|test|pipeline|api|web|demo}
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
PY=".venv/bin/python"

setup() {
  if [ ! -x "$PY" ]; then
    python3 -m venv .venv --without-pip
    curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python -
  fi
  .venv/bin/pip install -q -r requirements.txt
  ( cd frontend && npm install )
  echo "Setup completo. Ahora: ./run.sh demo"
}

case "${1:-demo}" in
  setup)    setup ;;
  test)     $PY -m pytest -q ;;
  pipeline) $PY -m src.pipeline ;;
  api)      $PY -m uvicorn src.app.main:app --port 8000 --reload ;;
  web)      ( cd frontend && npm run dev ) ;;
  demo)
    $PY -m uvicorn src.app.main:app --port 8000 >/tmp/argly-api.log 2>&1 &
    echo "API   -> http://localhost:8000/docs"
    echo "Web   -> http://localhost:5173  (Ctrl+C para salir)"
    ( cd frontend && npm run dev )
    ;;
  *) echo "Uso: ./run.sh {setup|test|pipeline|api|web|demo}"; exit 1 ;;
esac

#!/usr/bin/env bash
# Menjalankan REST API SIPD DALEV.
#
#   ./run.sh              -> mode normal
#   ./run.sh --reload     -> mode pengembangan (restart otomatis)
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Membuat virtualenv .venv ..."
  python3 -m venv .venv
  .venv/bin/pip install -q -U pip
  .venv/bin/pip install -q -r requirements.txt
fi

# HOST/PORT dibaca dari .env supaya satu sumber konfigurasi.
HOST=$(.venv/bin/python -c 'from app.config import settings; print(settings.api_host)')
PORT=$(.venv/bin/python -c 'from app.config import settings; print(settings.api_port)')

echo "REST API berjalan di http://${HOST}:${PORT} (dokumentasi: /docs)"
exec .venv/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"

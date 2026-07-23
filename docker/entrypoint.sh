#!/usr/bin/env bash
set -euo pipefail

cd /app/packages/server
uv run alembic upgrade head

if [ "${1:-api}" = "worker" ]; then
  exec uv run celery -A app.workers.celery_app:celery_app worker --loglevel=info
fi

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

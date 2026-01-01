#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "==> Project: $PROJECT_DIR"

# venv
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$PROJECT_DIR/.venv/bin/activate"
else
  echo "ERROR: .venv not found at $PROJECT_DIR/.venv"
  exit 1
fi

# redis server
echo "==> Checking Redis server..."
redis-cli ping | grep -q PONG && echo "OK: Redis is up"

# check python redis lib
echo "==> Checking python 'redis' package..."
python -c "import redis; print('OK: redis-py', getattr(redis,'__version__',None))" >/dev/null

cd "$PROJECT_DIR/gratitude_bot"

echo "==> Starting Celery worker..."
celery -A gratitude_bot worker -l INFO &
WORKER_PID=$!

cleanup() {
  echo "==> Stopping worker..."
  kill "$WORKER_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "==> Starting Celery beat..."
celery -A gratitude_bot beat -l INFO

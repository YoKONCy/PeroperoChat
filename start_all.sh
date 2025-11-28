#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT/Peroperochat/frontend"
BACKEND_DIR="$ROOT/Peroperochat/backend"

MODE="${1:-dev}"
API_BASE="${API_BASE:-http://localhost:8000}"
FRONT_PORT="${FRONT_PORT:-5173}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

mkdir -p "$ROOT/logs"

if [ -x "$BACKEND_DIR/.venv/bin/python" ]; then
  PY_CMD="$BACKEND_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
else
  PY_CMD="python"
fi

cd "$BACKEND_DIR"
"$PY_CMD" -m pip install -r requirements.txt
nohup "$PY_CMD" -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" > "$ROOT/logs/backend.out" 2>&1 &
echo $! > "$ROOT/logs/backend.pid"

cd "$FRONTEND_DIR"
npm install
if [ "$MODE" = "prod" ]; then
  npm run build
  nohup env VITE_API_BASE="$API_BASE" npm run preview -- --port "$FRONT_PORT" > "$ROOT/logs/frontend.out" 2>&1 &
else
  nohup env VITE_API_BASE="$API_BASE" npm run dev -- --port "$FRONT_PORT" > "$ROOT/logs/frontend.out" 2>&1 &
fi
echo $! > "$ROOT/logs/frontend.pid"

echo "frontend http://localhost:$FRONT_PORT"
echo "backend http://localhost:$BACKEND_PORT"

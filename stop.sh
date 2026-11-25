#!/bin/bash
# Stop Wealth Workbench host processes and Docker services.

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Stopping Wealth Workbench..."
echo ""

if [ -f backend.pid ]; then
    BACKEND_PID="$(cat backend.pid)"
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill "$BACKEND_PID" 2>/dev/null || echo "  Backend already stopped"
    rm -f backend.pid
else
    echo "Stopping any running backend processes..."
    pkill -f "uvicorn app.main:app" 2>/dev/null || echo "  No backend process found"
fi

if [ -f frontend.pid ]; then
    FRONTEND_PID="$(cat frontend.pid)"
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill "$FRONTEND_PID" 2>/dev/null || echo "  Frontend already stopped"
    rm -f frontend.pid
else
    echo "Stopping any running frontend processes..."
    pkill -f "next dev" 2>/dev/null || echo "  No frontend process found"
fi

COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
fi

echo "Stopping Docker services..."
$COMPOSE --profile full --profile neo4j stop 2>/dev/null || true
$COMPOSE stop postgres redis 2>/dev/null || true

echo ""
echo "All services stopped."
echo "To remove volumes (wipes DB): $COMPOSE --profile full --profile neo4j down -v"

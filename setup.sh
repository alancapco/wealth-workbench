#!/bin/bash
# One-shot environment bootstrap for Wealth Workbench.
# Prefer ./start.sh for day-to-day local development (hot reload).
# Prefer: docker compose --profile full up -d --build  for a containerized stack.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Setting up Wealth Workbench..."

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "Created .env with demo defaults (AUTH_MODE=fixture)."
    echo "Edit .env to add optional API keys (LLM, Alpha Vantage, news), then re-run."
    echo "  Required for a working local UI: AUTH_MODE=fixture, APP_ENV=development"
    echo "  Database password in .env must match docker-compose POSTGRES_* values."
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker not found. Install Docker Desktop / Engine first."
    exit 1
fi

COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE="docker-compose"
    else
        echo "ERROR: Docker Compose not found."
        exit 1
    fi
fi

MODE="${1:-dev}"

case "$MODE" in
  full|docker)
    echo "Starting full Docker stack (postgres, redis, backend, frontend)..."
    $COMPOSE --profile full up -d --build
    echo ""
    echo "Waiting for backend /health/live (max ~2 minutes)..."
    attempts=0
    until curl -sf http://127.0.0.1:8000/health/live >/dev/null 2>&1; do
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 60 ]; then
            echo "ERROR: Backend did not become healthy."
            $COMPOSE --profile full logs --tail=80 backend || true
            exit 1
        fi
        sleep 2
    done
    echo "Backend is live."
    echo ""
    echo "  Frontend: http://localhost:3000"
    echo "  Backend:  http://localhost:8000"
    echo "  Ready:    http://localhost:8000/health/ready"
    echo ""
    echo "Logs: $COMPOSE --profile full logs -f"
    echo "Stop: $COMPOSE --profile full down"
    ;;
  infra)
    echo "Starting infrastructure only (postgres, redis)..."
    $COMPOSE up -d postgres redis
    echo "Done. Run ./start.sh next, or start API/UI manually."
    ;;
  dev|*)
    echo "Delegating to ./start.sh (infra in Docker + host API/UI)..."
    exec ./start.sh
    ;;
esac

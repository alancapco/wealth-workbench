#!/bin/bash
# Start script for Wealth Workbench
# Runs PostgreSQL and Redis in Docker; backend and frontend from source (uv + npm).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Starting Wealth Workbench..."
echo ""

if [ ! -f .env ]; then
    echo "ERROR: .env file not found."
    echo "  Run: cp .env.example .env"
    echo "  Then set AUTH_MODE=fixture and APP_ENV=development for local demos."
    exit 1
fi

# Export .env so POSTGRES_* / AUTH_MODE are visible to this shell and child processes.
set -a
# shellcheck disable=SC1091
source .env
set +a

POSTGRES_USER="${POSTGRES_USER:-rm_user}"
POSTGRES_DB="${POSTGRES_DB:-rm_workbench}"
AUTH_MODE="${AUTH_MODE:-fixture}"
APP_ENV="${APP_ENV:-development}"
SEED_DEMO_DATA="${SEED_DEMO_DATA:-true}"

if [ "$AUTH_MODE" != "fixture" ]; then
    echo "WARNING: AUTH_MODE=$AUTH_MODE — OIDC is not implemented."
    echo "  Most API routes will return 503 IDENTITY_UNAVAILABLE."
    echo "  For local/demo use AUTH_MODE=fixture and APP_ENV=development."
fi

echo ".env loaded (AUTH_MODE=$AUTH_MODE, APP_ENV=$APP_ENV)"

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # shellcheck disable=SC1091
    source "$HOME/.local/bin/env" 2>/dev/null || source "$HOME/.cargo/env" 2>/dev/null || true
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is required for Postgres and Redis."
    exit 1
fi

COMPOSE="docker compose"
if ! docker compose version >/dev/null 2>&1; then
    COMPOSE="docker-compose"
fi

echo "Starting PostgreSQL and Redis..."
$COMPOSE up -d postgres redis

echo "Waiting for PostgreSQL..."
attempts=0
until $COMPOSE exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [ "$attempts" -ge 45 ]; then
        echo "ERROR: PostgreSQL did not become ready in time."
        $COMPOSE logs --tail=40 postgres || true
        exit 1
    fi
    echo "  still waiting... ($attempts)"
    sleep 2
done
echo "PostgreSQL is ready"
echo "Redis is running"
echo ""

cd backend
echo "Installing Python dependencies with uv..."
uv sync

echo "Running database migrations..."
uv run alembic upgrade head

if [ "$SEED_DEMO_DATA" = "true" ] && [ "$AUTH_MODE" = "fixture" ]; then
    echo "Seeding demo data..."
    uv run python -m app.scripts.seed_demo_data || echo "WARNING: seed failed (continuing)"
fi
cd "$ROOT_DIR"

echo "Starting Backend (FastAPI)..."
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > ../backend.pid
cd "$ROOT_DIR"
echo "Backend started (PID: $BACKEND_PID) — logs: tail -f backend.log"

echo "Starting Frontend (Next.js)..."
cd frontend
if [ ! -d node_modules ]; then
    echo "Installing npm packages..."
    npm install
fi
# Prefer root .env NEXT_PUBLIC_* when frontend/.env.local is absent
if [ ! -f .env.local ] && [ -f ../.env ]; then
    grep -E '^NEXT_PUBLIC_' ../.env > .env.local || true
fi
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > ../frontend.pid
cd "$ROOT_DIR"
echo "Frontend started (PID: $FRONTEND_PID) — logs: tail -f frontend.log"

echo ""
echo "Waiting for backend health..."
ready=0
for _ in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health/live >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
if [ "$ready" -eq 1 ]; then
    echo "Backend is live"
else
    echo "WARNING: backend /health/live not responding yet — check backend.log"
fi

echo ""
echo "All services started."
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API docs:  http://localhost:8000/api/docs"
echo "  Ready:     http://localhost:8000/health/ready"
echo ""
echo "Stop with: ./stop.sh"

# Wealth Workbench

Relationship-manager workbench for wealth management: client books, briefs, priorities, workflows, market data, Shariah tools, and related admin surfaces.

## Prerequisites

- **Docker** and **Docker Compose** (PostgreSQL + Redis)
- **Node.js** 18+ (frontend)
- **[uv](https://docs.astral.sh/uv/)** (Python deps; `start.sh` installs it if missing)
- **Python** 3.11–3.13 (managed by uv)

## Quick start (recommended)

Runs Postgres and Redis in Docker, and the API + Next.js app from source:

```bash
git clone https://github.com/alancapco/wealth-workbench.git
cd wealth-workbench

cp .env.example .env
# Edit .env — set at least DATABASE_URL / POSTGRES_* to match docker-compose,
# plus any API keys you need (LLM, HubSpot, Tiger, news providers).

./start.sh
```

Then open:

| Service    | URL                                      |
| ---------- | ---------------------------------------- |
| Frontend   | http://localhost:3000                    |
| Backend    | http://localhost:8000                    |
| API docs   | http://localhost:8000/api/docs           |

Stop everything:

```bash
./stop.sh
```

Logs while running:

```bash
tail -f backend.log frontend.log
docker-compose logs -f postgres redis
```

## Environment

- **Template (safe to commit):** `.env.example`
- **Local secrets (gitignored):** `.env`, `backend/.env`, `frontend/.env.local`
- **Docker defaults:** `docker-compose.yml` uses demo Postgres credentials (`rm_user` / `demo_password_123`) when env vars are unset. Override them via `.env` for anything beyond local demos.

Copy and fill:

```bash
cp .env.example .env
```

Common keys:

- `POSTGRES_*` / `DATABASE_URL` — must match Compose
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` — AI features
- `HUBSPOT_ACCESS_TOKEN` — CRM integration
- `TIGER_*` — Tiger Broker market data (optional)
- `NEWSFILTER_API_KEY` / `ALPHAVANTAGE_API_KEY` — news/quotes (optional)
- `SECRET_KEY` — app secret (`openssl rand -hex 32`)
- `NEXT_PUBLIC_API_URL` — frontend → API base URL

## Alternative: full Docker setup

`./setup.sh` brings up Compose services and waits for the backend health check. Prefer `./start.sh` for day-to-day local development (hot reload).

```bash
cp .env.example .env   # fill API keys
./setup.sh
```

Infra only:

```bash
docker-compose up -d postgres redis
```

## Manual install

### 1. Infrastructure

```bash
docker-compose up -d postgres redis
```

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project layout

```
backend/     FastAPI + Alembic + uv
frontend/    Next.js (App Router)
demo_data/   Seed / fixture CSVs
mockup/      Static HTML prototypes
deliverables/ Specs and audit notes
```

## Notes

- Real credentials and `*.log` files are gitignored. Do not commit `.env` or key material.
- Demo Docker passwords in Compose are for local use only — change them before any shared or production deploy.

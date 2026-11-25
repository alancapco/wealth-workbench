# Wealth Workbench

Relationship-manager workbench for wealth management: client books, briefs, priorities, workflows, market data, Shariah tools, and related admin surfaces.

## Architecture

### System overview

```mermaid
flowchart TB
  subgraph Client["Browser"]
    UI["Next.js frontend<br/>:3000"]
  end

  subgraph App["Application"]
    API["FastAPI backend<br/>:8000 /api/v1"]
    Worker["Outbox worker<br/>async actions"]
  end

  subgraph Data["Data plane"]
    PG[("PostgreSQL + TimescaleDB<br/>+ pgvector :5432")]
    Redis[("Redis :6379")]
    Neo4j[("Neo4j optional<br/>:7688 / profile neo4j")]
  end

  subgraph External["External providers optional"]
    AV["Alpha Vantage<br/>quotes / history"]
    NF["Newsfilter"]
    YH["Yahoo Finance RSS"]
    FX["FreeCurrencyAPI"]
    LLM["LLM OpenAI-compatible"]
  end

  UI -->|HTTP / REST| API
  API --> PG
  API --> Redis
  API -.->|wealth graph| Neo4j
  Worker --> PG
  API --> AV
  API --> NF
  API --> YH
  API --> FX
  API --> LLM
```

### Runtime components

```mermaid
flowchart LR
  subgraph Frontend["frontend/"]
    Pages["App Router pages<br/>dashboard · briefs · market<br/>journey · family · admin"]
    Lib["lib/endpoints.ts<br/>API client"]
    UIKit["components/"]
  end

  subgraph Backend["backend/app/"]
    EP["api/v1/endpoints/"]
    Core["core/<br/>config · identity · database"]
    Svc["services/<br/>brief · market · journey<br/>priority · product · shariah<br/>family · actions · graph"]
    Models["models/ + alembic/"]
  end

  Pages --> Lib --> EP
  UIKit --> Pages
  EP --> Core
  EP --> Svc
  Svc --> Models
```

### Request / data flow

Typical authenticated read (fixture mode for local demos):

```mermaid
sequenceDiagram
  participant Browser
  participant Next as Next.js
  participant API as FastAPI
  participant Auth as Identity fixture/OIDC
  participant DB as PostgreSQL
  participant Mkt as Market providers

  Browser->>Next: Open workbench page
  Next->>API: GET /api/v1/session
  API->>Auth: Resolve principal
  Auth-->>API: Fixture principal books/tenant
  API-->>Next: Session payload
  Next->>API: GET /api/v1/... domain call
  API->>DB: SQLAlchemy async query
  DB-->>API: Rows
  opt Live market enrichment
    API->>Mkt: Alpha Vantage / Newsfilter / Yahoo
    Mkt-->>API: Quotes or headlines
  end
  API-->>Next: JSON
  Next-->>Browser: Render UI
```

Market quotes path (Tiger Broker removed):

```mermaid
flowchart LR
  UI["/market page"] --> Q["GET /api/v1/market/quotes"]
  Q --> Svc["MarketDataService"]
  Svc -->|ALPHAVANTAGE_API_KEY set| AV["Alpha Vantage GLOBAL_QUOTE"]
  Svc -->|no key| Empty["Empty quotes list"]
  AV --> UI

  UI2["Market news"] --> N["GET /api/v1/market/news"]
  N --> Svc
  Svc --> NF["Newsfilter"]
  NF -->|fallback| YH["Yahoo Finance RSS"]
  YH --> UI2
```

## Prerequisites

- **Docker** and **Docker Compose** (PostgreSQL + Redis; optional full stack)
- **Node.js** 18+ (frontend, when running on the host)
- **[uv](https://docs.astral.sh/uv/)** (Python deps; `start.sh` installs it if missing)
- **Python** 3.11–3.13 (managed by uv)

## Quick start (recommended)

Runs Postgres and Redis in Docker, and the API + Next.js app from source:

```bash
git clone https://github.com/alancapco/wealth-workbench.git
cd wealth-workbench

cp .env.example .env
# Demo defaults already work locally:
#   AUTH_MODE=fixture, APP_ENV=development
#   POSTGRES_* / DATABASE_URL use demo_password_123 (matches Compose)
# Add optional API keys (LLM, Alpha Vantage, news) as needed.

./start.sh
```

`start.sh` will: start Postgres/Redis, `uv sync`, run `alembic upgrade head`, seed demo data (idempotent), then start API + UI.

| Service  | URL                            |
| -------- | ------------------------------ |
| Frontend | http://localhost:3000          |
| Backend  | http://localhost:8000          |
| API docs | http://localhost:8000/api/docs |
| Ready    | http://localhost:8000/health/ready |

Stop:

```bash
./stop.sh
```

Logs:

```bash
tail -f backend.log frontend.log
docker compose logs -f postgres redis
```

## Full Docker stack

Build and run Postgres, Redis, backend, and frontend containers:

```bash
cp .env.example .env
docker compose --profile full up -d --build
# or: ./setup.sh full
```

Optional Neo4j (wealth graph):

```bash
# In .env: NEO4J_ENABLED=true, NEO4J_PASSWORD=changeme
docker compose --profile full --profile neo4j up -d --build
```

Infra only:

```bash
docker compose up -d postgres redis
```

## Environment

| File | Purpose |
| ---- | ------- |
| `.env.example` | Committed template — copy to `.env` |
| `.env` | Local secrets (gitignored) |
| `frontend/.env.local` | Optional Next overrides (gitignored) |
| `docker-compose.yml` | Postgres/Redis always; `full` / `neo4j` profiles for app/graph |

Important keys:

- `AUTH_MODE=fixture` + `APP_ENV=development` — required for local/demo (OIDC is not implemented)
- `POSTGRES_*` / `DATABASE_URL` — must share the same password
- `EXPECTED_SCHEMA_HEAD=j0urn3y0001` — Alembic head for `/health/ready`
- `NEO4J_ENABLED=false` — portable default; enable with the `neo4j` Compose profile
- `LLM_*`, `ALPHAVANTAGE_API_KEY`, `NEWSFILTER_*` — optional integrations
- `NEXT_PUBLIC_API_URL` — browser → API base URL
- `FORCE_SEED=true` — wipe and re-seed demo clients

## Manual install

```bash
docker compose up -d postgres redis

cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.scripts.seed_demo_data
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

cd ../frontend
npm install
npm run dev
```

## Project layout

```
backend/      FastAPI + Alembic + uv (api, services, models)
frontend/     Next.js App Router (pages, components, lib)
demo_data/    Seed / fixture CSVs
mockup/       Static HTML prototypes
deliverables/ Specs and audit notes
```

See **Architecture** above for Mermaid system, component, and data-flow diagrams.

## Notes

- Real credentials and `*.log` files are gitignored. Do not commit `.env` or key material.
- Compose demo passwords are for local/shared demos only — change them before any real production deploy.
- Timescale image is pinned to `timescale/timescaledb:2.28.3-pg15` (includes `pgvector`).

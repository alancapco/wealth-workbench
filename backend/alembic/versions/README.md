# Alembic Migration Configuration

This directory contains the database migrations for the WM Workbench backend.
Run them from `backend/` with the virtualenv active.

## Running Migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head          # apply all pending migrations
alembic current               # show the applied head
alembic revision -m "message" # create a new migration
alembic downgrade -1          # roll back one migration
```

`alembic/env.py` imports `app.models` so autogenerate sees every ORM model and
uses `settings.DATABASE_URL` (asyncpg) as the connection URL. An import failure
is fatal by design: silently skipping models produced empty migrations.

## Migration History

Single linear chain (oldest first):

| Revision | File | Contents |
|---|---|---|
| `c3adee111800` | `20261107_c3adee111800_initial_schema_49_tables.py` | Initial 49-table schema (clients, briefs, audit_logs, workflow/artifact/action/priority/capture/config tables) |
| `df83fca46282` | `20261108_df83fca46282_add_demo_client_tables.py` | Demo client data tables |
| `a1b2c3d4e5f6` | `20261108_aaoifi_knowledge_base.py` | AAOIFI knowledge base (Shariah RAG source) |
| `m3m0ry0001` | `20261109_m3m0ry0001_client_memory_records.py` | `client_memory_records` (API-013 / API-014 memory proposals) |
| `f0und4t10n01` | `20261109_f0und4t10n01_holdings_interactions_client_memories.py` | `holdings`, `interactions`, `client_memories` (idempotent, inspector-guarded) |

The last migration guards each `create_table` with an inspector check, so it
also repairs databases that were bootstrapped with `Base.metadata.create_all`
but never received those three tables.

`EXPECTED_SCHEMA_HEAD` (when set) is the revision `/health/ready` checks
against; update it when a new head is added.

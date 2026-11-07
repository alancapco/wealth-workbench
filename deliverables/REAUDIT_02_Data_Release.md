# RE-AUDIT 02 — Data Layer, Migrations & Release Hygiene

**Repository:** `/Volumes/Orico/code/capco/wealth-workbench`
**Scope:** schema/models, Alembic migrations, clean-start path, dependencies, secrets, repo hygiene, tests/CI
**Auditor:** data-auditor
**Date:** 2026-11-07
**Subject of audit:** the `G-28 Release hygiene` claim in `PROGRESS.md:34-39`
**Mode:** READ-ONLY. No application code, migration, or config file was modified. All Alembic commands were run in offline/dry-run form only; no migration was applied to any database. Live-DB inspection used `SELECT` only.

---

## 1. Executive Verdict

**`G-28 Release hygiene` is NOT fixed. The claim fails on every one of its four sub-claims.**

`PROGRESS.md:34-39` states:

> - Created Alembic migrations (briefs, audit_logs, client_memories)
> - Added .gitignore with HUBSPOT_CREDENTIALS.md
> - Created AuditService for action tracking
> - Migration README with instructions

| Claim | Verdict | Hard evidence |
|---|---|---|
| Alembic migrations created | **Files exist, but unusable.** | Two independent defects make `alembic` non-executable: `alembic.ini:37` raises `ValueError` on every command, and `alembic.ini:33` points at a non-existent `backend/versions` directory, so even after patching the first bug the chain resolves to **zero** revisions. §2.2, §2.3 |
| Migrations describe the schema | **No.** | Migration `001` creates `briefs`/`audit_logs` with a hard FK to `clients.id`, but **no migration creates `clients`, `holdings`, or `interactions`**. `down_revision = None` (`001_add_briefs_audit.py:14`). On an empty database `upgrade head` would fail with `relation "clients" does not exist`. §2.2 |
| .gitignore protects credentials | **Unverifiable and ineffective.** | **The repository is not a Git repository.** `git status` → `fatal: not a git repository`; `.git` does not exist. A `.gitignore` governs nothing. Real credentials remain on disk in `.env` and `HUBSPOT_CREDENTIALS.md`. §4.4 |
| AuditService for action tracking | **Dead code.** | `audit_service` is never imported or called outside its own `__init__.py`. The approval endpoint that claims to "Record the approval in audit log" is a `# TODO` returning a hardcoded 2024 timestamp (`endpoints/briefs.py:48-55`). `audit_logs` table does not exist in the live DB. §3.5 |
| Migration README with instructions | **Instructions do not work.** | `alembic/versions/README.md:11` says `alembic upgrade head`; that command raises `ValueError`. §2.2 |

**Additional release-blocking finding not yet reported by the other auditors:** the live database is not
produced by either the models or the migrations. It uses `jsonb` + `timestamp with time zone`; both the
models (`create_all` DDL) and the migrations emit `JSON` + `timestamp without time zone`. **Three schema
definitions exist and no two agree.** §2.7.

**How to read "migrations exist" in this repo — three independent qualifiers, all required:**

1. The config is **unparseable**: `alembic.ini:37` makes every CLI invocation raise `ValueError` (§2.2).
2. Even repaired, discovery is **zero**: `alembic.ini:33` points at a non-existent directory, so
   `upgrade head` is a **silent no-op returning exit 0** (§2.3).
3. Even discovered, no revision can be **authored**: `alembic/script.py.mako` is missing (§2.4).

**Files on disk are not a migration story.** Any statement of the form "Alembic migrations were created"
must carry all three qualifiers or it is misleading.

---

## 2. Section A — Schema vs Migrations vs Code

### 2.1 Ground truth: there are three competing schema definitions

| Source | Where | Produces |
|---|---|---|
| **S1 Models** | `app/models/models.py` (5 classes) + `app/services/memory/memory_service.py:16` (1 class) | What `Base.metadata.create_all` builds |
| **S2 Migrations** | `alembic/versions/001`, `002` | What `alembic upgrade head` *would* build |
| **S3 Live DB** | running `wealth-workbench-postgres-1` | What the app actually talks to |

I extracted all three. They disagree on **column type families**, **timezone policy**, and **which
tables exist at all**.

### 2.2 Alembic is not executable — defect #1 (`alembic.ini:37`)

```console
$ cd backend && ./venv/bin/alembic history
  File ".../alembic/config.py", line 545, in _get_file_separator_char
    raise ValueError(
ValueError: 'os  # Use os.pathsep. Default configuration used for new projects.' is not a valid value for version_path_separator; expected 'space', 'newline', 'os', ':', ';'
```

`alembic.ini:37` is:

```ini
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.
```

`configparser` does **not** strip inline comments, so the value becomes the entire string including the
comment. `alembic history`, `alembic heads`, and `alembic upgrade head --sql` all die here. This is not an
environment issue — it reproduces on the project's own pinned Alembic and on the installed 1.20.1.

### 2.3 Alembic finds **zero** migrations — defect #2 (`alembic.ini:33`)

```ini
version_locations = %(here)s/versions
```

`%(here)s` is the directory of `alembic.ini`, i.e. `backend/`. So this resolves to **`backend/versions/`** —
which does not exist:

```console
$ ls -d backend/versions
ls: versions: No such file or directory
```

The real migrations live in `backend/alembic/versions/`. Because `version_locations` overrides the default
`<script_location>/versions`, Alembic sees an empty revision tree and **silently succeeds with a no-op**.
I proved this by bypassing defect #1 in memory (no file edited) and running offline SQL generation:

```console
$ ./venv/bin/python /tmp/alembic_probe.py    # sets version_path_separator=os in memory only
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Generating static SQL
BEGIN;

COMMIT;
```

**An empty transaction.** `upgrade head` reports success while creating nothing. This is the worst possible
failure mode for a release gate: a green-looking no-op.

With `version_locations` additionally corrected in memory, the chain runs and emits real DDL (§2.5).

> **Cross-reference (REAUDIT_01_Backend.md):** independently reproduced there as **ND-33 (High) — silent
> no-op**, including the same `BEGIN;`/`COMMIT;` output and the same corrected-path DDL. That report's CI
> recommendation (§12.3) has been revised accordingly: the gate must grep the generated SQL for
> `CREATE TABLE briefs` rather than trust the exit code, because this failure returns 0.

### 2.4 `alembic revision` is also impossible — `script.py.mako` missing

> Cross-reference: logged as **ND-34** in `REAUDIT_01_Backend.md`.

```console
$ find backend/alembic -type f
backend/alembic/env.py
backend/alembic/versions/001_add_briefs_audit.py
backend/alembic/versions/002_add_client_memories.py
backend/alembic/versions/README.md
```

There is no `alembic/script.py.mako`. Alembic requires this template for every `revision` command. So the
migration chain cannot be extended by the normal workflow, and `--autogenerate` is impossible. The two
hand-written files are the only revisions that can ever exist until this is restored.

### 2.5 Column-by-column: migration vs model

Offline DDL actually produced by `command.upgrade(cfg, 'head', sql=True)` with the two config defects
corrected in memory:

```sql
CREATE TABLE briefs (
    id UUID NOT NULL,
    client_id UUID NOT NULL,
    version VARCHAR NOT NULL,
    sections JSON NOT NULL,
    generated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    approved_by VARCHAR,
    approved_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(client_id) REFERENCES clients (id)
);
CREATE TABLE client_memories (
    id UUID NOT NULL,
    client_id UUID NOT NULL,
    memory_type VARCHAR NOT NULL,
    key VARCHAR NOT NULL,
    value TEXT,
    metadata JSON,
    confidence VARCHAR,
    source VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (id),
    FOREIGN KEY(client_id) REFERENCES clients (id)
);
```

#### `briefs` — `models.py:79-86` vs `001_add_briefs_audit.py:21-32`

| Column | Model (`models.py`) | Migration 001 | Match |
|---|---|---|---|
| `id` | `UUID(as_uuid=True)` PK, default `uuid.uuid4` | `postgresql.UUID(as_uuid=True)` PK | Types ✅ / default **not** in DDL (app-side only) |
| `client_id` | `UUID` FK `clients.id`, `nullable=False` | `UUID` NOT NULL, FK | ✅ |
| `version` | `String`, `nullable=False` | `sa.String()` NOT NULL | ✅ model↔migration (**but see §2.6**) |
| `sections` | `JSON`, `nullable=False` | `postgresql.JSON()` NOT NULL | ✅ (both `json`, not `jsonb`) |
| `generated_at` | `DateTime`, `nullable=False` | `sa.DateTime()` NOT NULL | ✅ type, ⚠️ naive |
| `approved_by` | `String` | `sa.String()` | ✅ |
| `approved_at` | `DateTime` | `sa.DateTime()` | ✅ |
| `created_at` | `DateTime`, default `utcnow` | `sa.DateTime()` | ✅ |

Indexes: migration creates `ix_briefs_client_id` (`001:47`). **The model declares no index**, so
`create_all` produces none. The index exists only in a migration that never ran.

#### `audit_logs` — `models.py:93-99` vs `001:35-44`

| Column | Model | Migration 001 | Match |
|---|---|---|---|
| `id` | `UUID` PK | `UUID` PK | ✅ |
| `action_type` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `entity_type` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `entity_id` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `actor` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `details` | `JSON` | `postgresql.JSON()` | ✅ |
| `timestamp` | `DateTime`, default `utcnow` | `sa.DateTime()` | ✅ |

Indexes (`001:48-49`) — `ix_audit_logs_entity`, `ix_audit_logs_timestamp` — again absent from the model.

#### `client_memories` — `memory_service.py:16-29` vs `002:20-33`

| Column | Model | Migration 002 | Match |
|---|---|---|---|
| `id` | `UUID` PK, default `uuid4` | `UUID` PK | ✅ |
| `client_id` | `UUID` FK, NOT NULL | `UUID` NOT NULL, FK | ✅ |
| `memory_type` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `key` | `String` NOT NULL | `String()` NOT NULL | ✅ |
| `value` | `Text` | `sa.Text()` | ✅ |
| `metadata` | `JSON`, default `dict` | `postgresql.JSON()` | ✅ at DDL level, **broken at ORM level — §4.2** |
| `confidence` | `String` | `String()` | ✅ |
| `source` | `String` | `String()` | ✅ |
| `created_at` | `DateTime` | `sa.DateTime()` | ✅ |
| `updated_at` | `DateTime` `onupdate` | `sa.DateTime()` | ✅ |

#### Semantic drift on `confidence` — three incompatible scales

| Layer | Declaration | Scale |
|---|---|---|
| Model / migration | `memory_service.py:26` `Column(String)`, `002:27` `sa.String()` | ordinal string |
| Memory writer | `memory_service.py:40` default `"medium"` | `"low"` / `"medium"` / `"high"` |
| Provenance service | `provenance_service.py:24` `confidence: float = 1.0` | `0.0–1.0` numeric |

The same business concept is a `VARCHAR` holding `"medium"` in one service and a `float` holding `1.0` in
another, with no conversion layer anywhere. This is a schema-level contract violation between two services
that are supposed to share the "confidence" vocabulary.

**Verdict on column shapes:** where a migration exists, columns/types do match the model. The problems are
(a) three tables have **no** migration at all (§2.5), (b) the migrations are unreachable (§2.2–2.4), and
(c) timezone/JSON semantics differ from the live DB (§2.7).

### 2.6 Type drift: `Brief.version` is `String`, the writer passes an `int`

- Model: `version = Column(String, nullable=False)` (`models.py:81`)
- Migration: `sa.Column('version', sa.String(), nullable=False)` (`001:24`)
- Service: `version: Optional[int] = None` (`brief_service.py:22`) and `"version": version or 1`
  (`brief_service.py:66`)

So the API contract is an **integer** (`int`), the column is `VARCHAR NOT NULL`. `asyncpg` will reject an
`int` bound to a `varchar` column (`DataError: invalid input for query argument`). The drift is masked today
only because **`Brief` is never persisted anywhere** — repo-wide, `Brief(` is constructed in zero places;
the only `db.add`/`session.add` calls in `backend/app` are `seed_demo_data.py:98,125,175`,
`audit_service.py:37`, `memory_service.py:56`, `sync_from_hubspot.py:75`. `brief_service.generate_brief`
returns a plain `dict` (`brief_service.py:62-78`) and never touches the `briefs` table.

Consequence: `briefs` is a **write-never** table. Its migration, its model, and its service disagree, and
nothing exercises the disagreement.

### 2.7 FK integrity

All four foreign keys are declared **without `ondelete`** — neither at the model nor the migration level:

| FK | Model | Migration | `ondelete` |
|---|---|---|---|
| `holdings.client_id` | `models.py:40` | none (no migration) | **none** |
| `interactions.client_id` | `models.py:59` | none (no migration) | **none** |
| `briefs.client_id` | `models.py:80` | `001:30` | **none** |
| `client_memories.client_id` | `memory_service.py:21` | `002:31` | **none** |

Type compatibility is correct (`UUID(as_uuid=True)` on both sides everywhere). The behavioural gap is that
`ON DELETE` defaults to `NO ACTION`: deleting a client raises a FK violation instead of cascading or
nulling, and there is no soft-delete column. For a system whose audit table is meant to be immutable,
`audit_logs.entity_id` is a bare `String` (`models.py:96`) with **no FK at all** — polymorphic by design but
with zero referential integrity and no index-backed join guarantee beyond `ix_audit_logs_entity`
(which, per §2.2, was never created).

Also missing: `briefs` has **no unique constraint on `(client_id, version)`**, so the "versioning" the
docstring advertises (`models.py:76`) cannot actually prevent duplicate versions.

### 2.8 Does `create_all` include `client_memories`? — No, unless a service module is imported

`ClientMemory` is declared in a **service file**, not in `models.py` (`memory_service.py:16`). It only joins
`Base.metadata` when that module is imported:

```console
$ python -c "import app.models.models; print(sorted(Base.metadata.tables))"
after models.py only:      ['audit_logs', 'briefs', 'clients', 'holdings', 'interactions']
after + memory_service:    ['audit_logs', 'briefs', 'client_memories', 'clients', 'holdings', 'interactions']
```

- `app/scripts/init_db.py:6-9` imports only `from app.models.models import (...)` → `client_memories` is **not** created.
- `app/main.py` never imports `memory_service` → the service is not even loaded at boot.
- `alembic/env.py:15` imports only `app.models.models` → `target_metadata` is **missing** `client_memories`.

So migration `002` is a hand-written orphan: it is not derivable from `target_metadata`, and any
`--autogenerate` run (already impossible, §2.4) would propose **`DROP TABLE client_memories`**. There is no
single source of truth for the schema.

Worse, `app/services/memory/__init__.py:2` does `from ...memory_service import memory_service`, which makes
`app.services.memory.memory_service` resolve to the **instance**, not the module. This is why
`import app.services.memory.memory_service as m; m.ClientMemory` raises
`AttributeError: 'MemoryService' object has no attribute 'ClientMemory'` — a latent shadowing bug on top of
the schema problem.

### 2.9 Live DB says all of this is academic: the migrations were never applied

```console
$ docker compose exec -T postgres psql -U rm_user -d rm_workbench -c "\dt"
 public | clients      | table | rm_user
 public | holdings     | table | rm_user
 public | interactions | table | rm_user
(3 rows)
```

`briefs`, `audit_logs`, `client_memories`, and `alembic_version` **do not exist**. A column query for each
of the four new tables returns `(0 rows)`.

> Cross-reference: the jsonb/timestamptz divergence below is logged as **ND-35** in `REAUDIT_01_Backend.md`,
> independently reproduced by direct query. Corollary recorded there and here: **the only working database
> on this machine is reproducible from no artifact in the repository.**

Live column types also **contradict both S1 and S2**:

| Column | Live DB | Model `create_all` | Migration |
|---|---|---|---|
| `clients.created_at` | `timestamp with time zone` | `TIMESTAMP WITHOUT TIME ZONE` | (no migration) |
| `clients.preferences` | `jsonb` | `JSON` | (no migration) |
| `clients.family_entities` | `jsonb` | `JSON` | (no migration) |
| `holdings.as_of` | `timestamp with time zone` | `TIMESTAMP WITHOUT TIME ZONE` | (no migration) |
| `interactions.preferences_extracted` | `jsonb` | `JSON` | (no migration) |

I confirmed the model-side DDL by compiling `CreateTable` against the PostgreSQL dialect offline:

```sql
CREATE TABLE clients ( ... preferences JSON, ... created_at TIMESTAMP WITHOUT TIME ZONE, ... );
CREATE TABLE holdings ( ... as_of TIMESTAMP WITHOUT TIME ZONE, ... );
```

Therefore the running database was **not** produced by the current models and **not** by these migrations.
Its provenance is unknown — most likely a hand-edited or older `create_all` run. Whoever next runs
`alembic upgrade head` against it would be applying DDL designed for a different schema.

---

## 3. Section B — Boot / Clean-Start Path

### 3.1 Fresh clone walkthrough (derived from the scripts, then verified)

| Step | Command | Result |
|---|---|---|
| 1 | `cp .env.example .env` | Required; `start.sh:13-17` aborts without it |
| 2 | `./start.sh` | Runs `docker-compose up -d postgres redis` (`start.sh:30`) |
| 3 | `uv sync` (`start.sh:49`) | Creates `.venv`, resolves `uv.lock` (SQLAlchemy **2.1.8**) |
| 4 | `uv run uvicorn app.main:app` (`start.sh:56`) | **Crashes on import** — see below |
| 5 | tables created? | **No.** `start.sh` contains no `alembic`, `create_all`, `init_db`, or `seed_demo_data` |
| 6 | demo data seeded? | **No.** Nothing invokes `seed_demo_data.py` |

`grep -rn "alembic|upgrade head|create_all|init_db|seed_demo" start.sh setup.sh docker-compose.yml` →
**zero matches.** The startup path and the schema path are entirely disconnected.

Confirmed crash, reproduced live (`app/main.py` import) and corroborated by the current `backend.log`
(16:30 today, from the `.venv`):

```
File ".../app/services/market/market_service.py", line 13, in <module>
    from app.models.models import MarketTick, SourceKind
ImportError: cannot import name 'MarketTick' from 'app.models.models'
```

### 3.2 `setup.sh` hangs indefinitely

`setup.sh:43` runs `docker-compose up -d`, which per §3.4 starts **only** postgres and redis. It then loops
until `curl -f http://localhost:8000/health` succeeds (`setup.sh:63-66`). Nothing in Compose starts a backend,
so that loop **never exits**. `setup.sh:58` additionally claims the wait "includes table creation and demo
data seeding" — there is no service capable of doing either.

### 3.3 `docker-compose.yml` has no application services — README instructions are invalid

```console
$ docker compose config --services
postgres
redis
```

`backend/Dockerfile` exists but is orphaned — no Compose service references it. Therefore every documented
command of the form `docker-compose exec backend ...` fails with `no such service: backend`:

- `README.md:63` — `docker-compose exec backend alembic upgrade head`
- `README.md:66` — `docker-compose exec backend python -m app.scripts.seed_demo_data`
- `README.md:259` — `docker-compose exec backend alembic upgrade head`
- `QUICKSTART.md:142`, `REGISTRATION_GUIDE.md:139` — same pattern

`README.md:44-48` also promises `docker-compose up -d` starts "(PostgreSQL, Redis, Backend, Frontend)". It does not.

### 3.4 `backend/init.sql` — extensions only; does not conflict with migrations, but is not a schema

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;   -- init.sql:4
CREATE EXTENSION IF NOT EXISTS vector;        -- init.sql:5
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- init.sql:6
```

No `CREATE TABLE`, so no conflict with migrations. Observed state of the running container:

```console
$ psql -c "SELECT extname, extversion FROM pg_extension ORDER BY 1;"
 plpgsql       | 1.0
 timescaledb   | 2.28.3
 uuid-ossp     | 1.1
 vector        | 0.8.1
```

All three requested extensions **are** present — the earlier concern that `timescale/timescaledb:latest-pg15`
might not ship pgvector is **not** borne out in this environment. Two caveats remain:

- `pgvector` is installed and its Python wheel is declared (`requirements.txt:14`), but **no code uses it**:
  repo-wide grep for `pgvector|Vector(|embedding` in `backend/app` returns **zero matches**. There is no
  vector column anywhere. It is dead weight and a container-size/reproducibility cost for nothing.
- The image tag is **`latest-pg15`** (`docker-compose.yml:3`) — a floating tag. The exact schema-affecting
  extensions cannot be reproduced reliably. It is also not the image that guarantees `vector`; that it
  happened to be present here is luck, not specification.

### 3.5 `audit_logs` is wired to nothing

The endpoint that promises audit persistence does not persist:

```python
# app/api/v1/endpoints/briefs.py:44-55
"""Approve a brief (Gate 1)
Records the approval in audit log
"""
try:
    # TODO: Store approval in database with audit trail
    return {
        ...
        "approved_at": "2024-11-07T12:00:00Z",
```

`audit_service` (`audit_service.py:47`) is imported by nothing outside `services/audit/__init__.py`.
Combined with §2.9 (`audit_logs` table absent), the entire audit-trail claim is unsupported.

### 3.6 Health/readiness (relevant to release gating)

- `app/api/health.py:14-63` is an accurate, DB-probing health check — **but it is never mounted**:
  `app/api/v1/__init__.py:5-15` includes six routers, none of them `health`. `grep -rn "health" app/api app/main.py`
  shows no `include_router` reference.
- The route that actually serves is `app/main.py:44-54`, which returns a hardcoded
  `"database": "connected"` with `# TODO: Add actual DB health check` at `main.py:48`.
- There is no separate liveness vs readiness endpoint, and no `/readyz`.

---

## 4. Section C — Dependencies / Secrets / Repo Hygiene

### 4.1 Two dependency manifests disagree — and the disagreement is behaviour-changing

`backend/requirements.txt` (used by `backend/Dockerfile:9-10`) pins exact versions.
`backend/pyproject.toml` uses open `>=` ranges, and `backend/uv.lock` resolves **much newer** versions.
`start.sh:49` uses `uv sync`, i.e. **the lock, not requirements.txt**.

| Package | `requirements.txt` | `uv.lock` (actual) | Drift |
|---|---|---|---|
| SQLAlchemy | `==2.0.25` (line 8) | `2.1.8` | 2 minor |
| FastAPI | `==0.109.0` (line 1) | `0.162.0` | 53 minors |
| Pydantic | `==2.5.3` (line 4) | `2.14.3` | 9 minors |
| Alembic | `==1.13.1` (line 9) | `1.20.1` | 7 minors |
| openai | `==1.10.0` (line 20) | `3.46.0` | **major version jump** |

This is not cosmetic. It changes whether the application can even import:

- Under **SQLAlchemy 2.1.8**, `class ClientMemory` with an attribute named `metadata` emits only
  `SAWarning: Attribute name 'metadata' should be left reserved...`.
- Under **SQLAlchemy 2.0.25 — the version `requirements.txt` pins, i.e. the version the Docker image
  installs** — it is a **hard failure**. Verified in an isolated environment:

```console
$ uv run --python 3.11 --with "sqlalchemy==2.0.25" python -c "<declarative class with metadata = Column(JSON)>"
sqlalchemy 2.0.25
ERROR: InvalidRequestError Attribute name 'metadata' is reserved when using the Declarative API.
```

So `docker build` produces an image in which `app.services.memory.memory_service` (and therefore the
`client_memories` model) **cannot be imported at all**, while `./start.sh` produces an environment where it
imports with a warning. Two supported install paths, two different failure modes. Neither is validated.

`pyproject.toml:5` declares `requires-python = ">=3.11,<3.14"`, yet the checked-in `backend/venv/` is
Python **3.14.7** — outside the declared range and inconsistent with `backend/.venv/` (3.13.13). There is no
`.python-version` file.

### 4.2 `metadata` as a column name is a latent ORM defect (`memory_service.py:25`)

```python
metadata = Column(JSON, default=dict)
```

`metadata` is reserved on declarative classes. Even on 2.1.8, where it degrades to a warning, the mapping is
semantically wrong: `ClientMemory.metadata` becomes an `InstrumentedAttribute`, shadowing the
`MetaData` that Alembic and `create_all` rely on for that class. This should be `metadata_` mapped to a
different attribute, or `Column("metadata", JSON)` under a non-reserved attribute name.

### 4.3 Pin quality (requirements.txt)

- Mixed philosophy: every line pins `==`, but the same set is re-declared with `>=` in `pyproject.toml:6-27`,
  and `uv.lock` ignores both. There is no single authoritative lock for the Docker path.
- `psycopg2-binary==2.9.9` (`requirements.txt:10`) is declared but the app only uses the **async** driver
  (`database.py:1,15` `create_async_engine` + `asyncpg`). Unused sync driver in the production image.
- `pgvector==0.2.4` (`requirements.txt:14`) is unused (§3.4).
- `pgvector` appears as `0.2.4` in requirements but `0.5.1` in `uv.lock` — another silent major-ish drift.
- `openai==1.10.0` vs `3.46.0` is the most dangerous: the `AsyncOpenAI` call site
  (`copilot_service.py:20`) is written against the 1.x SDK surface. Nothing verifies it still works on 3.x.

### 4.4 Repository hygiene — **there is no repository**

```console
$ git status
fatal: not a git repository (or any of the parent directories): .git
$ ls -d .git
ls: .git: No such file or directory
```

The `.gitignore` that `PROGRESS.md:36` cites as the G-28 fix **governs nothing**, because the project was
never initialised as a Git repository. Consequences:

- "Tracked" vs "untracked" cannot be evaluated. No file in this tree is tracked.
- If the deliverable is a directory copy or archive — which it must be, absent Git — then **`.gitignore` is
  bypassed entirely** and every credential file ships with it.
- The claimed "26 files changed" cannot be verified against any diff or history. There is no commit, no
  author attribution, and no way to review the change set.

`.gitignore` content review (`/.gitignore`):

| Pattern | Line | Effect |
|---|---|---|
| `.env` | 12 | Matches `.env` at any depth → covers root `.env` and `backend/.env` ✅ |
| `HUBSPOT_CREDENTIALS.md` | 38 | Would work if Git existed |
| `HUBSPOT_SETUP.md` | — | **NOT ignored** (it contains only placeholders — see below, so low risk) |
| `*.log`, `backend.pid` | 23-24, 45-46 | Would work if Git existed |

### 4.5 Credentials still on disk (values redacted)

`.env` and `backend/.env` both exist and both contain credential-shaped values. Keys present (values masked):

```
DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB,
TIGER_CLIENT_ID, TIGER_PRIVATE_KEY, TIGER_ACCOUNT, TIGER_TOKEN,
HUBSPOT_API_KEY, HUBSPOT_ACCESS_TOKEN, HUBSPOT_PERSONAL_ACCESS_KEY,
LLM_API_KEY, SECRET_KEY, REDIS_URL
```

| File | Line | Finding |
|---|---|---|
| `backend/.env` | 20 | `LLM_API_KEY=sk-<REDACTED>` — a live API-key-shaped value |
| `.env` (root) | — | `TIGER_PRIVATE_KEY`, `HUBSPOT_ACCESS_TOKEN`, `SECRET_KEY`, `LLM_API_KEY` populated |
| `HUBSPOT_CREDENTIALS.md` | 6, 7, 44 | Two real HubSpot tokens documented in plaintext (`pat-<REDACTED>` form at :44) |
| `HUBSPOT_SETUP.md` | 35 | `HUBSPOT_ACCESS_TOKEN=your_token_here` — **placeholder only, no leak** ✅ |

Two additional credential-bearing paths are **not covered by `.gitignore` at all** and are not obviously
secret by filename: a future `git add .` would include them unless the operator remembers `.env` patterns.
The only real mitigation is out-of-band and unverifiable here. **Recommendation:** rotate every token in
`.env`, `backend/.env`, and `HUBSPOT_CREDENTIALS.md`; these have been sitting in a deliverable directory.

---

## 5. Section D — Tests / CI

### 5.1 Test count: **zero**

```console
$ find . -type f -name 'test_*.py' | grep -Ev '/(venv|\.venv|node_modules)/'
(no output)
$ find . -type f \( -name '*.test.ts' -o -name '*.spec.ts*' \) | grep -Ev '/(venv|\.venv|node_modules)/'
(no output)
```

Every glob match resolves inside `.venv/`, `venv/`, or `node_modules/` (third-party packages). There is not
a single project test file — backend or frontend.

### 5.2 Test configuration: **none**

- `backend/pytest.ini` — absent
- `backend/setup.cfg` — absent
- `pytest` section in `backend/pyproject.toml` — absent (only `[tool.uv]` dev-dependencies at `pyproject.toml:36-40`)
- No `asyncio_mode` setting, despite `pytest-asyncio` being declared (`requirements.txt:34`)
- `frontend/package.json:5-10` has **no `test` script** (`dev`, `build`, `start`, `lint` only)

So `pytest` would collect zero tests and exit 5 ("no tests ran"), which in most CI setups is a failure — but
there is no CI to catch it.

### 5.3 CI: **none**

- `.github/workflows` — does not exist
- `docker-compose.test.yml` — does not exist
- No `.gitlab-ci.yml`, `Jenkinsfile`, `azure-pipelines.yml`, or `Makefile`

There is no automated gate of any kind: no lint, no type check, no import smoke test, no migration check.
Given §3.1 — the backend cannot import — a **single** `python -c "import app.main"` step would have caught it.

---

## 6. Section E — Release Dimensions Never Previously Audited

| # | Dimension | State | Evidence / gap |
|---|---|---|---|
| E1 | **Migration rollback path** | 🟡 Declared, unexercised, unsafe | `001:52-57` and `002:39-42` have `downgrade()`, but neither can run (`alembic.ini:37`). More importantly, `001.downgrade` drops `briefs`/`audit_logs` — fine — but there is **no migration at all** for `clients/holdings/interactions`, so a full `downgrade base` is undefined territory. No test, no rehearsal, no documented rollback runbook. |
| E2 | **Backup / restore** | 🔴 Absent | `docker-compose.yml:10-11` defines a named volume `postgres_data` and nothing else. No `pg_dump` script, no restore procedure, no retention window, no offsite copy. Volume deletion (`stop.sh:37` suggests `docker-compose down -v`) is the only documented "reset" and it is irreversible. |
| E3 | **Health vs readiness separation** | 🔴 Absent | Only `main.py:44` (hardcoded healthy). No `/readyz`, no dependency-gated readiness. `api/health.py` implements the right thing but is unmounted (§3.6). |
| E4 | **Structured logging** | 🔴 Absent | `main.py:9` uses `logging.basicConfig(level=INFO)` — plain text to stderr. No JSON formatter, no request ID / correlation ID, no tenant or actor context. Service logs use f-strings (`audit_service.py:41`, `memory_service.py:59`) rather than `%s` parameterisation, so log-injection via `key`/`client_id` is possible. `database.py:17` enables `echo=True` whenever `ENVIRONMENT == "development"`, which logs every SQL statement and bound parameter — including PII — to stdout. |
| E5 | **Config validation** | 🟡 Minimal, fails at import | `config.py:5-60`: 11 fields are required with no defaults (`SECRET_KEY:9`, `DATABASE_URL:19`, four `POSTGRES_*:20-22`, three `TIGER_*:25-27`, two `HUBSPOT_*:33-34`, `LLM_API_KEY:38`). A missing value raises `pydantic.ValidationError` at import time — the process dies with a stack trace rather than an actionable message. `ENVIRONMENT` is a free string, never validated against an enum. `config.py:55-58` still uses the **deprecated** `class Config` form in pydantic-settings v2 (should be `model_config = SettingsConfigDict(...)`). `env_file = "../.env"` (`config.py:56`) is CWD-relative, so the app only finds config if launched from `backend/`. |
| E6 | **DB connection pooling** | 🟡 Hardcoded | `database.py:15-22`: `pool_size=10, max_overflow=20, pool_pre_ping=True`. No environment override, no `pool_recycle`, no statement timeout, no `pool_timeout`. Alembic uses `NullPool` (`env.py:47`) which is correct for migrations. Total connection ceiling (30) is baked in and unrelated to `POSTGRES_*` capacity. |
| E7 | **Timezone policy** | 🔴 Contradictory across three layers | Migrations: `TIMESTAMP WITHOUT TIME ZONE` (`001:26,28,29`, `002:29,30`). Models: `DateTime` → naive DDL. Live DB: `timestamp with time zone` (§2.9). Application writes `datetime.now(timezone.utc)` (`memory_service.py:53`, `audit_service.py:34`) — **aware** values — into columns that are declared **naive** in both model and migration. asyncpg will either coerce silently or raise depending on the column; either way the policy is undefined. No `timezone` setting on the server, no `SET TIME ZONE` in `init.sql`, no documented UTC-only rule. |
| E8 | **Index review** | 🔴 Under-indexed where it matters | Verified against `pg_indexes`: `holdings.client_id` and `interactions.client_id` have **no index**, yet every portfolio/interaction query filters on them (`brief_service.py:87`, `:37`). `interactions.interaction_date` unindexed but ordered/sorted. `holdings.symbol` unindexed. The better-designed indexes live only in migrations (`ix_briefs_client_id` `001:47`, `ix_audit_logs_entity` `001:48`, `ix_audit_logs_timestamp` `001:49`, `ix_client_memories_*` `002:35-36`) — i.e. **in the artifacts that never ran**. `create_all` would produce **none** of them. So the deployed schema has strictly worse indexing than the intended schema. |
| E9 | **Data retention / deletion** | 🔴 Absent | No retention policy on `audit_logs` (which, per compliance framing in `models.py:90`, is the one table that must be retained). No `deleted_at`/soft-delete column on any table. No GDPR/PDPA erasure path: with `ondelete` unset (§2.7), deleting a `clients` row is blocked by FK violations from `holdings`/`interactions`, so even a manual erasure request fails. No archival job, no TTL. |
| E10 | **Schema drift detection** | 🔴 Absent (and impossible) | No `alembic check` in any script, no schema snapshot, no `pg_dump --schema-only` artifact in the repo. `--autogenerate` cannot run (`script.py.mako` missing, §2.4) and would be wrong anyway (`target_metadata` lacks `client_memories`, §2.8). The live DB already differs from both definitions and nothing would notice. |
| E11 | **Migration ↔ app deploy ordering** | 🔴 Undefined | `start.sh:56` starts uvicorn without running migrations first; there is no entrypoint that runs `alembic upgrade head` and then execs the server. No `depends_on: condition: service_healthy` gate (there is no app service at all, §3.3). No version handshake between app code and `alembic_version`. |

---

## 7. Consolidated Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| D-01 | **P0** | `alembic.ini:37` inline comment breaks every Alembic command | `ValueError: 'os  # Use os.pathsep...' is not a valid value` |
| D-02 | **P0** | `alembic.ini:33` points `version_locations` at non-existent `backend/versions`; `upgrade head` is a silent no-op | offline SQL = `BEGIN; COMMIT;` |
| D-03 | **P0** | No baseline migration for `clients/holdings/interactions`; `001` has `down_revision=None` yet FKs `clients.id` → fails on empty DB | `001:14,30`, emitted DDL |
| D-04 | **P0** | Migrations never applied; `alembic_version`, `briefs`, `audit_logs`, `client_memories` absent from live DB | `\dt` output §2.9 |
| D-05 | **P0** | Backend cannot boot (`MarketTick` ImportError); no tables are created on any path | `backend.log`, live import |
| D-06 | **P0** | `create_all` omits `client_memories`; Alembic `target_metadata` omits it too | metadata table list §2.8 |
| D-07 | **P0** | `ClientMemory.metadata` reserved name: warning on 2.1.8, **hard `InvalidRequestError` on pinned 2.0.25** | isolated SQLAlchemy 2.0.25 repro §4.1 |
| D-08 | **P0** | Schema drift: live DB (`jsonb`/`timestamptz`) ≠ models (`JSON`/naive) ≠ migrations (naive) | §2.9 comparison table |
| D-09 | P1 | `alembic/script.py.mako` missing → `alembic revision` impossible | `find alembic -type f` |
| D-10 | P1 | `Brief.version` is `VARCHAR` in schema, `int` in service contract | `models.py:81` vs `brief_service.py:66` |
| D-11 | P1 | No `ondelete` on any FK; no soft delete; erasure path fails | §2.7 |
| D-12 | P1 | `briefs` unpersisted and unindexed; `audit_logs` never written | §2.6, §3.5 |
| D-13 | P1 | `docker-compose.yml` has no app services; 5 documented commands are invalid | §3.3 |
| D-14 | P1 | `setup.sh` blocks forever waiting for a backend that Compose never starts | `setup.sh:43,63-66` |
| D-15 | P1 | Two dependency manifests resolve differently; Docker path installs a crashing SQLAlchemy | §4.1 |
| D-16 | P1 | Untracked/unverifiable change set — **no Git repository at all** | `git status` → fatal |
| D-17 | P1 | Live credentials in `.env`, `backend/.env`, `HUBSPOT_CREDENTIALS.md`; `.gitignore` inert | §4.5 |
| D-18 | P1 | Zero tests, zero test config, zero CI | §5 |
| D-19 | P2 | `pgvector` + `psycopg2-binary` declared but unused | §3.4, §4.3 |
| D-20 | P2 | Missing FK indexes on `holdings.client_id`, `interactions.client_id` | `pg_indexes` |
| D-21 | P2 | Timezone policy undefined across three layers; aware values into naive columns | §6 E7 |
| D-22 | P2 | No backup/restore, no retention, no readiness split, no structured logging, no drift check | §6 |
| D-23 | P2 | `Dockerfile` uses `--reload` in `CMD` and is orphaned by Compose | `Dockerfile:24` |
| D-24 | P3 | `main.py:58` `uvicorn.run("main:app")` — wrong module path if run as script | `main.py:56-63` |
| D-25 | P3 | Memory package `__init__` shadows the submodule with the instance | `services/memory/__init__.py:2` |

---

## 8. Verdict on G-28

`PROGRESS.md:34-39` marks **G-28 Release hygiene ✓**. That is **false**.

The change set added two migration files, a `.gitignore`, and an `AuditService`. None of the four
deliverables is operational:

1. The migrations **cannot execute** (two independent `alembic.ini` defects), **would fail if they did**
   (no baseline for `clients`), and **have never been applied** (live DB has no `alembic_version`).
2. The `.gitignore` **protects nothing** because the project is not a Git repository, while real
   credentials remain in three on-disk files.
3. `AuditService` is **never called**; the endpoint that claims to use it is a `# TODO` with a hardcoded
   timestamp.
4. The migration README's sole command (`alembic upgrade head`) either throws or silently does nothing.

Net effect on release readiness: **negative**. Before this change set the project had no migrations and
created tables via `create_all`. Now it has a migration directory that *looks* authoritative, will silently
no-op, and would (if forced to run) apply DDL that contradicts the live database. A reviewer who trusts
`PROGRESS.md` would ship a schema that does not exist.

**Grade: FAIL. G-28 remains open at P0.**

Minimum to close it:

1. Fix `alembic.ini:33` → `version_locations = %(here)s/alembic/versions`, and `:37` → `version_path_separator = os`.
2. Add `alembic/script.py.mako`.
3. Add a baseline migration `000` creating `clients`, `holdings`, `interactions` with the **live** types
   (`jsonb`, `timestamptz`), then re-derive `001`/`002` from it.
4. Move `ClientMemory` into `app/models/models.py` (rename the `metadata` attribute), and import the model
   package from `env.py` so `target_metadata` is complete.
5. Run `alembic upgrade head` inside `start.sh` (or a container entrypoint) before launching uvicorn, and
   `alembic downgrade base && alembic upgrade head` in CI to prove reversibility.
6. Unify dependencies on **one** manifest; delete `requirements.txt` or make `pyproject.toml` exact.
7. Initialise Git, commit without `.env`/credential files, and rotate every token that has been sitting here.
8. Add at minimum a smoke test (`import app.main`) and a migration-apply test to CI.

---

## Appendix — Commands Executed (all read-only / offline)

```console
# Boot
$ ./venv/bin/python -c "import app.main"                     # ImportError: MarketTick
$ ./venv/bin/python -c "import app.services.memory.memory_service"   # SAWarning: metadata reserved

# Alembic (never applied to any DB)
$ ./venv/bin/alembic history                                 # ValueError (alembic.ini:37)
$ ./venv/bin/alembic heads                                   # ValueError (same)
$ ./venv/bin/alembic upgrade head --sql                      # ValueError (same); no DB contact
$ ./venv/bin/python /tmp/alembic_probe.py                    # in-memory config fix → "BEGIN; COMMIT;" (0 revisions)

# Offline DDL generation (no connection opened)
$ python -c "command.upgrade(cfg,'head',sql=True)"           # briefs/audit_logs/client_memories DDL
$ python -c "CreateTable(...).compile(postgresql.dialect())" # model-side DDL for comparison

# Metadata coverage
$ python -c "import app.models.models; Base.metadata.tables"
$ python -c "...; import app.services.memory.memory_service; Base.metadata.tables"

# Live DB (SELECT only)
$ docker compose exec -T postgres psql ... -c "\dt"
$ docker compose exec -T postgres psql ... -c "SELECT column_name,data_type,is_nullable FROM information_schema.columns WHERE table_name='<t>'"
$ docker compose exec -T postgres psql ... -c "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public'"
$ docker compose exec -T postgres psql ... -c "SELECT extname,extversion FROM pg_extension"
$ docker compose config --services

# Hygiene
$ git status                                                 # fatal: not a git repository
$ find . -name 'test_*.py' | grep -v venv                    # none
$ grep -rInE "<credential patterns>"                          # values redacted in this report
```

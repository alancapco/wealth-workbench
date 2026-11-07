# RM Workbench — Re-Audit (Iteration 1 Change Set)

**Prepared for:** Alan
**Date:** 7 November 2026
**Scope:** 26 files identified by modification time after 14:20 on 7 Nov 2026, plus targeted review of additional release, data, dependency and frontend dimensions. This is not a Git-verified change set or an exhaustive security assessment.
**Baseline:** `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` (30-row gap register G-01…G-30), `01_PRD_Requirement_Inventory.md`, `02_Implementation_Feature_Audit.md`, `03_Copilot_Capability_Review.md`.
**Inputs:** `deliverables/REAUDIT_01_Backend.md`, `deliverables/REAUDIT_02_Data_Release.md`, `deliverables/REAUDIT_03_Frontend.md`, plus first-hand reproduction by the team lead.
**Method:** static review, import tests, `tsc --noEmit`, Alembic CLI invocation, database schema inspection, endpoint enumeration and call-site tracing on both sides of the API. Runtime observations below describe the audit snapshot, not a fresh health check at report publication. **No application code was modified.**

---

## 0. Verdict

> ### 🔴 The change set is a regression, not remediation.
> The repo **cannot start**. `import app.main` raises `ImportError: cannot import name 'MarketTick'`. The backend process is dead (pid 14829), nothing listens on `:8000`, and the frontend type-check fails.
>
> **Of the 9 gaps `PROGRESS.md` marks "✅ Completed": 0 are fully fixed, 4 are partially fixed, 4 are not fixed, and 1 has regressed.**
> `PROGRESS.md` self-reports "9/11 P0 addressed (82%)". The evidenced figure is **0 fully fixed**.
>
> **No new PRD requirement has moved from Absent to Implemented.** The functional coverage of the PRD is unchanged at **0 of 28 FRs fully implemented**.

The dominant pattern is **additive, not substitutive**: five new service modules were written **beside** the old code path rather than into it. Four of the five have no caller outside their own `__init__.py`. The old broken paths are still the ones wired to the API.

---

## 1. What actually changed

| Measure | Before | After | Note |
|---|---:|---:|---|
| Backend `app/` LOC | 2,631 | 3,249 | **+618 — exactly the size of the 5 new modules + `health.py`** |
| Frontend LOC | 1,330 | 1,330 | **unchanged** (all frontend files 12:07–12:42; backend edited 15:31–15:37) |
| New service modules | 0 | 5 | `brief`, `memory`, `audit`, `provenance`, `workflow` |
| Registered endpoints | 26 | 26 | 24 under `/api/v1` + `GET /` + `GET /health`; `api/health.py:14` is a 25th definition, **unregistered** |
| DB writes in API layer | 0 | **0** | `grep -rn "db.add\|\.commit()" backend/app/api` → 0 matches |
| Project tests | 0 | **0** | 155 `test_*.py` files exist, all under `backend/.venv` |
| Alembic migrations | 0 | 2 | both non-executable (see §4.1) |
| App boots? | yes | **no** | `ImportError: MarketTick` |

**Interpretation:** effort went into new files, not into fixing the wired paths. That is why `PROGRESS.md` and the runtime disagree so completely.

---

## 2. Claim-by-claim verification

| # | `PROGRESS.md` claim | Actual | Verdict |
|---|---|---|---|
| G-04 | Timezone errors fixed; ranking returns real priorities | Timezone handling genuinely corrected (`ranking_service.py:118-121,144-147,197-201`: `replace(tzinfo=timezone.utc)`). **But the whole method is still wrapped in `except Exception: return []` (`:81-83`)**, so any other exception again yields an empty Top 10 with HTTP 200. | **Partially fixed** |
| G-25 | Accurate `/health` with real checks | `api/health.py` implements a real `SELECT 1`, but is **never registered** — `main.py` and `api/v1/__init__.py` do not import it. `main.py:44-54` still serves the old endpoint with `# TODO: Add actual DB health check` and hardcoded `"database": "connected"`. It also returns HTTP 200 even when it reports `unhealthy`. | **Not fixed** (dead code) |
| G-01 | Briefs built from real data, no hardcoded client | Portfolio and interactions **are** now genuine DB reads (`brief_service.py:84-115,150-178`) — real progress, credited. But: `_build_material_changes` and `_build_market_news` call the `hash()`-based mock market service and stamp `source_kind: "LIVE_FEED"` / `"TigerBroker News · LIVE"` / confidence 1.0 (`:117-148,180-201`); `_build_proposed_agenda` claims `source: "AI Generated"` / 0.85 with **no LLM call** (`:203-237`); the brief is returned as a dict and **never persisted**, so "versioning" does not exist. | **Partially fixed** |
| G-22 | Real workflow state machine | `workflow_orchestrator.py` is an in-memory dict plus a transition map. No DB, no stage execution, `transition_stage` mutates a caller-supplied dict, and **no endpoint imports it**. The live `/workflow/start` still uses `copilot_service` and returns `"stages": []` (`copilot_service.py:192`). | **Not fixed** (dead code) |
| G-28 | Migrations, `.gitignore`, audit service | Migrations 001/002 exist and `.gitignore` now covers `HUBSPOT_CREDENTIALS.md` — both genuine. But migrations are **non-executable** (§4.1), the live DB has no `briefs`/`audit_logs`/`client_memories` tables, and there is no migration baseline.`HUBSPOT_SETUP.md` is still not ignored. | **Partially fixed** |
| G-13 | Persistent D5 memory | `ClientMemory` is declared **inside the service file** with an attribute literally named `metadata` (SQLAlchemy reserved name — warning on inspected 2.1.8, hard error on pinned 2.0.25), `confidence = Column(String)` while provenance uses float, and the table **does not exist** in the live DB. No endpoint imports `memory_service`. | **Not fixed** (dead code) |
| G-26 | Frontend contract fixed, no more 422 | **Inverted.** Backend routes changed to `POST /briefs/generate/{client_id}` and `POST /briefs/approve/{brief_id}`; the frontend still posts JSON bodies to `/briefs/generate`, `/briefs/approve`, and `GET /briefs/{id}` (route deleted). All three would return **404** under the inspected route definitions once startup is repaired; the observed current result was connection failure. The `/workflow/*` 422 defect is **unfixed but latent**: `workflow/start` and `workflow/extract-insights` declare query parameters the frontend fills as JSON, but `workflowApi` is never imported, so **no live call site emits 422 today — only because that code is dead**. "No more 422" is true in the narrowest possible sense and false as a claim of repair. | **Regressed** |
| G-11 | Real HubSpot sync | `fetch_contacts_from_hubspot` and `sync_from_hubspot.py` added; the outbound call is real. Cannot be exercised because nothing boots; idempotency, pagination and rate-limit handling not demonstrated. | **Partially fixed** |
| G-23 | Provenance validation prevents fabrication | `validate_provenance()` checks only that four keys exist and `source_kind` is an enum member (`provenance_service.py:39-58`). It returns **True** for the fabricated stamps in `brief_service.py`. It is never called. Meanwhile fabrication is now present at **two layers** (§3). | **Not fixed — integrity regressed** |

**Score: 0 fixed · 4 partial · 4 not fixed · 1 regressed.**

**Scoring boundary — G-28:** “partial” credits artifacts (`.gitignore` and migration files), not delivered migration or release capability. On the capability axis, G-28 remains undelivered and the silent no-op adds a false-green regression risk. This reconciles the backend report's artifact-level credit with the data/release report's net-regression assessment; neither interpretation supports marking G-28 complete. `.gitignore` does not remove existing credentials or revoke them.

---

## 3. The brief path now fails in three independent layers

The brief is the flagship P0 capability. It fails three times over, and the failures mask each other.

| Layer | Defect | Evidence |
|---|---|---|
| **Transport** | Route moved to a path parameter; frontend still posts a body to the old URL → **404** on generate, approve and get | `briefs.py:14,36` vs `frontend/lib/api.ts:62-69` |
| **Envelope** (ND-31) | Backend returns `{"brief": {"sections": {…}}}`; frontend reads `briefData.portfolio_overview` — one level too shallow. Every lookup is `undefined`, so the **hardcoded enrichment branches execute whenever this nested payload reaches the renderer**, while flat-access panels fall back to placeholders | `briefs.py:29`, `brief_service.py:62-75` vs `BriefModal.tsx:32,47,63`, `page.tsx:23,75,86,99,107` |
| **Identity** (ND-32) | Backend mints `uuid4()` (`brief_service.py:32`); the client discards `brief_id` and approves the literal `'brief-123'` as `'Sarah Chen'`. `POST /briefs/approve` accepts any ID and any approver and returns a hardcoded `"approved_at": "2024-11-07T12:00:00Z"` | `BriefModal.tsx:77`, `brief/[clientId]/page.tsx:33`, `briefs.py:36-55` |

**Root cause of the transport break — two competing generators.** There are now **two** `generate_brief` implementations: `copilot_service.py:27` (flat envelope, and **zero callers**) and `brief_service.py:18` (nested `sections` envelope, wired at `briefs.py:28`). The endpoint was repointed at the new service *and* its URL shape changed in the same edit, but the frontend was never touched. The frontend's accessor path matches the **old, now-unused** generator. So this is not a typo — it is an unwired migration, the direct return of the G-27 four-layer disconnect.

**Why this matters more than a 404:** **three of the four** placeholder strings rendered by the broken panels are byte-identical to the `_generate_fallback_brief` strings at `copilot_service.py:157-175`, and the fourth is a prefix of one. A structurally broken brief is therefore indistinguishable from a legitimately degraded one.

**And the brief can fail before a payload exists at all.** `Client.aum` and `Holding.current_value` are nullable (`models.py:19,44`) but are formatted with `:,.0f` with no guard (`brief_service.py:96,104,133`), so a null value can raise `TypeError`. This is a source-derived latent HTTP 500, not a successful request observed during this audit. The dashboard's separate `$NaNM` failure-state defect is not evidence of this brief exception.

---

## 4. New blockers introduced by this change set

### 4.1 Release path — seven independent failures

1. **Alembic fails under both tested versions.** `backend/alembic.ini:37` reads `version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.` — the inline comment is parsed as part of the value. Reproduced on both the pinned 1.13 and the installed 1.20.1:
   ```
   ValueError: 'os  # Use os.pathsep. Default configuration used for new projects.'
   is not a valid value for version_path_separator; expected 'space', 'newline', 'os', ':', ';'
   ```
2. **A second, independent config defect makes migration a silent no-op.** `alembic.ini:33` sets `version_locations = %(here)s/versions`, which resolves to `backend/versions` — a directory that does not exist (the real one is `backend/alembic/versions`). Bypassing defect 1 in memory, `alembic upgrade head --sql` emits **only `BEGIN; COMMIT;`** — success exit code, zero DDL. That is the worst possible gate failure mode: it reports success while creating nothing.
3. **`alembic/script.py.mako` is missing**, so `alembic revision` and `--autogenerate` are impossible. The migration workflow cannot be continued, only hand-edited.
4. **No migration baseline.** 001/002 create `briefs`, `audit_logs` and `client_memories` with FKs to `clients.id`, but **no migration creates `clients`, `holdings` or `interactions`**. On an empty database, `upgrade head` fails with `relation "clients" does not exist`.
5. **All three schema-creation paths are broken.** `init_db.py` and `seed_demo_data.py` both import deleted model names (`ImportError`); Alembic fails per 1–4. `init.sql` only creates extensions and explicitly defers tables to SQLAlchemy.
6. **The inspected live database is behind the repository definitions.** It contains `clients`, `holdings`, `interactions`, but not `briefs`, `audit_logs`, `client_memories` or `alembic_version`. This establishes missing schema/version tracking in this database, not that migrations were never applied anywhere. Existing live columns use `jsonb` / `timestamptz` where repository definitions use `JSON` / naive timestamps. The newly declared tables' model and migration column shapes broadly match; the evidence supports live-DB-to-repository drift, not “no two agree” or a proven creation history. Calls requiring the missing tables would fail unless the schema is provisioned.
7. **`ClientMemory` is not loaded by the schema metadata import path, and its reserved attribute fails under the pinned SQLAlchemy version.** It lives in `services/memory/memory_service.py`, while `alembic/env.py:15` imports only `app.models.models`. Without importing the memory model, metadata-based creation/autogeneration omits it; autogenerate against a database containing that table could propose its removal. This does not prevent an explicit migration from creating it. `metadata` (`memory_service.py:25`) emits a warning under the inspected SQLAlchemy 2.1.8 environment but raises `InvalidRequestError` under pinned 2.0.25.

**These are independent failures, not one sequential exit-code pattern.** The invalid ini value blocks the CLI first. Bypassing it exposed wrong revision discovery and an offline run with exit 0 but no DDL. After correcting discovery, online execution still needs a compatible sync driver and a baseline before foreign keys can reference `clients`. Missing `script.py.mako` separately blocks authoring new revisions; it does not block executing existing revisions. No evidence establishes that all later failures exit 0. Docker installs `requirements.txt` (SQLAlchemy 2.0.25), whereas `start.sh` uses the lock (2.1.8), so the reserved-name defect also differs by environment.

### 4.2 Import graph — three separate breakages

| Name imported | Still imported by | Defined in `models.py`? |
|---|---|---|
| `MarketTick` | `services/market/market_service.py:13`, `scripts/init_db.py:7` | **No** — deleted |
| `SourceKind` | `services/market/market_service.py:13`, `scripts/seed_demo_data.py:10` | **No** — deleted |
| `WorkflowStage` | `services/copilot/copilot_service.py:11` | **No** — deleted (re-declared only inside `workflow_orchestrator.py`) |

`models.py` was cut from 7 tables to 5 (`WorkflowInstance` and `AuditEvent` also removed), but the importers were not updated. `copilot_service` is a *second, independent* break: `/workflow/*` is dead even if `MarketTick` were restored.

### 4.3 Configuration and boot

- `config.py:56` sets `env_file="../.env"` — a CWD-relative path. Running from the repo root never reads `backend/.env`, producing `ValidationError: SECRET_KEY required`.
- `SECRET_KEY` is declared at `config.py:9` and **referenced nowhere else**; `python-jose` and `passlib` are declared in `pyproject.toml:17-18` and never imported. Auth is not wired into the inspected runtime. Unused configuration and dependencies do not establish developer intent.
- `docker-compose.yml` defines only `postgres` and `redis` — **there is no backend or frontend service**, yet `setup.sh:58` claims it "includes table creation and demo data seeding".
- `setup.sh:63` uses an unbounded `until curl -f http://localhost:8000/health` loop while nothing starts uvicorn → `./setup.sh` **hangs forever** on a fresh machine.
- `start.sh:54-58` never runs `init_db` or the seed, and `$!` captures the `uv run` wrapper PID rather than uvicorn's — The stale/dead `backend.pid` (14829) and unavailable port were observed, but the wrapper PID alone does not establish why the process exited.
- **Dependency manifests disagree, and the two launch paths use different ones.** There are three sources of truth: `uv.lock` matches the venv exactly, while `requirements.txt` is stale — **2 match, 17 drift, 1 missing**. Worst offenders: openai 1.10.0 → **3.46.0** (two majors), redis 5.0.1 → 8.1.0 (three majors), pytest 7.4.4 → 9.2.0, fastapi 0.109.0 → 0.162.0, SQLAlchemy 2.0.25 → 2.1.8. Root cause: `pyproject.toml:7-27` uses `>=` with no upper bounds. `start.sh` launches through `uv run` (the lock), the Dockerfile installs from the requirements file — so local and container run different majors. That is precisely why my import test only *warned* on `ClientMemory.metadata` while a container build would raise.
- **The sync database driver is missing entirely (DEP-01, High).** `psycopg2-binary` is declared at `requirements.txt:10` but is **not installed and not in `uv.lock`**: `create_engine("postgresql://…").connect()` raises `ModuleNotFoundError: No module named 'psycopg'`. Alembic's sync path in `env.py:44` therefore has **two independent blockers** — the config `ValueError` and a missing driver. Note that SQLAlchemy 2.1 maps `postgresql://` to psycopg **v3**, so installing the declared `psycopg2-binary` would not fix it either.
- **Auth would fail on its first use (DEP-02, latent).** `passlib` 1.7.4 against the installed `bcrypt` 5.0.0 raises `AttributeError: module 'bcrypt' has no attribute '__about__'` (misreported downstream as a "72 bytes" error). This remains a latent compatibility issue while auth is unwired; it is not evidence that D0 was deliberately abandoned.
- **Two Python environments disagree.** `pyproject.toml:5` requires `<3.14`; the checked-in `backend/venv/` is **3.14.7**.
- **Every documented command that targets the backend container is invalid.** Five `docker-compose exec backend …` invocations in `RUNNING.md` / `QUICKSTART.md` cannot work, because no `backend` service exists.
- **`pgvector` is present but unused** — correcting the first audit: the `timescale/timescaledb:latest-pg15` image does ship pgvector 0.8.1, so `CREATE EXTENSION` succeeds. But no vector column exists anywhere, and the floating `latest-pg15` tag does not pin image contents or PostgreSQL patch/extension versions; its name targets PostgreSQL 15, not an arbitrary major.
- **No schema step exists in any start path**: no match for `alembic`, `create_all`, `init_db` or `seed` in `start.sh`, `setup.sh` or `docker-compose.yml`.

### 4.4 Data handling and query hygiene

- **SQL logging is on unconditionally.** `core/database.py` creates the engine with `echo=True`, so every statement — including client names, AUM and holdings — is written to `backend.log`. Observed directly in the log. This is PII in logs, against NFR-04/GOV-02, and it is on by default rather than behind a debug flag.
- **Missing indexes on the hot path.** `holdings.client_id` and `interactions.client_id` are unindexed, yet every brief generation and every ranking pass filters on them. Fine at 3 rows, a sequential scan at 1,000 RMs.
- **Connection pool is hardcoded** (`pool_size=10`, `max_overflow=20`) with no recycling, no pre-ping and no statement timeout.
- **No implemented client-erasure workflow.** FKs lack `ondelete` and ORM relationships lack cascade, so direct parent deletion with dependent rows can fail. An explicit child-first transactional deletion is technically possible, but no retention/erasure flow was found; NFR-04 is therefore not delivered.

### 4.5 Persistence and false success

- **No direct `db.add`/`commit` calls were found in the API source layer.** This is not proof that routes cannot invoke service-level or external CRM writes. The new `AuditService` and `MemoryService` have no endpoint callers, and their required tables are absent; the inspected brief/approval paths do not persist their results.
- **17 of 26 routes return success without doing the work.** `GET /crm/status` still reports `"connected"` because `crm_service.py:44-46` swallows every exception.
- `clients.py:53-61` raises `HTTPException(404)` **inside** a `try/except Exception` that re-raises as 500 — a missing client returns 500, and a malformed UUID raises `DBAPIError` → 500 instead of 422.

---

## 5. Delta against the 30-gap register

| Verdict | Count | Gaps |
|---|---:|---|
| **Fixed** | **0** | — |
| **Partially fixed** | 4 | G-01 (portfolio + interactions real; market/agenda still fabricated; no persistence), G-04 (timezone fixed; silent-empty failure retained), G-11 (HubSpot fetch added; unexercisable, no idempotency), G-28 (migrations + `.gitignore`; non-executable, no baseline, tables absent) |
| **Not fixed** | 4 | G-13 (dead code, table absent), G-22 (dead code, no execution), G-23 (validator is structural only, never called; fabrication now two layers), G-25 (health fix unregistered; live endpoint still lies) |
| **Regressed** | 1 | G-26 (404 ×3, plus envelope mismatch guaranteeing fabricated render) |
| **Unchanged / not attempted** | 21 | G-02, G-03, G-05, G-06, G-07, G-08, G-09, G-10, G-12, G-14, G-15, G-16, G-17, G-18, G-19, G-20, G-21, G-24, G-27, G-29, G-30 |

`PROGRESS.md` marks G-03 and G-09 as "in progress" — both are unchanged: `approve` still has `# TODO: Store approval in database` and returns a hardcoded timestamp.

**PRD functional coverage: unchanged at 0 of 28 FRs fully implemented** (15 / 18 / 22 / 28 all zero). No FR was demonstrated to meet all acceptance criteria in this snapshot; partial code improvements are credited separately above.

---

## 6. What this audit covered that the first one did not

The first audit was feature-coverage oriented. This pass adds dimensions it never examined:

| Dimension | Finding |
|---|---|
| **Boot / importability** | App does not import; 17 of 24 `/api/v1` routes dead at import (`market` 5, `briefs` 2, `workflow` 5, `dashboard` 5) |
| **Schema ↔ migration ↔ DB drift** | Inspected live DB has `jsonb`/`timestamptz` versus repository `JSON`/naive timestamp definitions; new-table model/migration shapes broadly agree. Three new tables and `alembic_version` are absent in this DB; no baseline migration exists. |
| **Migration executability** | `alembic.ini:37` ValueError; `alembic.ini:33` points at a non-existent `backend/versions` so a corrected run emits **zero DDL with exit 0**; `script.py.mako` missing |
| **Dependency baseline** | Two manifests in conflict (`requirements.txt` SQLAlchemy 2.0.25 / openai 1.10.0 vs `uv.lock` 2.1.8 / 3.46.0); `start.sh` uses the lock, the Dockerfile uses the pins; floating `:latest` base image; compose has no application services; `setup.sh` hangs on a fresh machine |
| **Data handling** | `echo=True` SQL logging writes client names, AUM and holdings to `backend.log`; no indexes on `holdings.client_id` / `interactions.client_id`; no implemented retention/erasure flow (direct deletion lacks FK/ORM cascade) |
| **Secrets on disk** | Real credential-shaped values in `.env`, `backend/.env` and `HUBSPOT_CREDENTIALS.md:6,7,44`; `.gitignore` is correct but the directory is **not a git repo**, so it protects nothing yet |
| **Type constraints** | `Brief.version = Column(String)` but `brief_service` passes an int; `ClientMemory.confidence` is VARCHAR while provenance uses float |
| **Frontend type-check** | `tsc --noEmit` exits 1 (`FamilyGraphModal.tsx:125` string vs number); no ESLint config; 4 unused dependencies |
| **Response-shape contract** | Envelope nesting mismatch (ND-31) — a class of defect invisible to URL-only contract checks |
| **Call-site reality** | 19 of 24 `/api/v1` routes have **no call site** in the frontend; 21 of 24 have **no valid** caller — only **3 are invoked correctly** (`dashboard/my-day`, `dashboard/allocation`, `dashboard/performance-trend`). 16 of 21 frontend API methods are never imported by any component |
| **Failure-state UX** | Dashboard failure renders `$NaNM` plus five hardcoded sections — failure indistinguishable from success; no error boundary, retry or empty state |
| **Client-side state** | `BriefModal` does not reset `brief`/`editedAgenda`, creating a stale previous-client display risk on reopen; this was not an observed cross-tenant disclosure. Approval can remain enabled after failed loading. |
| **Accessibility** | Zero `role` / `aria-*` / `tabIndex` / focus trap / Escape handler / `<label>` in any component; only `lang="en"` |
| **Auth posture** | `SECRET_KEY` unused, `python-jose`/`passlib` unimported — authentication is not wired; developer intent is not established |
| **Test coverage** | 0 project tests; no pytest config, no CI, no `docker-compose.test.yml` |

---

## 7. Copilot verdict — unchanged

The change set adds no orchestrator that executes stages, no skill registry, no context assembly fed into a prompt, no per-statement provenance that resolves to a source, no enforced approval, no telemetry, no versioning and no kill switch.

- **Binary verdict: NO** — still not an "AI copilot" under PRD §3.
- **C-01…C-16: 0 YES / 16 NO.** Unchanged.
- **Maturity: 1.0 / 5.** Unchanged.
- The `provenance_service` and `workflow_orchestrator` modules are *shapes* of the missing controls, with no consumers — they do not move the checklist.

Framing to keep: **thin AI call sites exist in source, but no delivered copilot architecture was demonstrated.** The two `AsyncOpenAI` call sites remain; their presence does not establish a functioning AI service while the app fails to import. The new template-based brief path must not be described as sending client data to an LLM merely because the older service has provider calls.

---

## 8. Remediation order

The ordering matters more than the individual fixes: nothing else is testable until the app boots.

**P0 — make it run (blocking everything else)**
1. Restore or re-add `MarketTick`, `SourceKind` and `WorkflowStage` in `models.py` — or update the four importers (`market_service.py:13`, `init_db.py:7`, `seed_demo_data.py:10`, `copilot_service.py:11`). Prefer updating the importers: the market service should not persist ticks it mocks.
2. Fix both Alembic config defects (`:37` inline comment, `:33` version path), restore `script.py.mako`, **install and declare a psycopg v3 driver** (the declared `psycopg2-binary` is absent and would not satisfy SQLAlchemy 2.1 anyway), then add a baseline migration that creates `clients` before 001/002.
3. Register the real health router, or replace `main.py:44-54` with it. Return 503 when unhealthy.
4. Make `setup.sh` fail fast instead of looping; add backend/frontend services to `docker-compose.yml`.
5. Add a minimal CI gate: app and per-router imports → offline migration SQL with assertions for expected revisions/tables → **actual migration against an empty disposable PostgreSQL database**, asserting tables, foreign keys and revision head → `tsc --noEmit` → project tests, including API contracts and persistence. Offline exit 0 is insufficient: wrong `version_locations` produced only `BEGIN; COMMIT;`. Even an expected `CREATE TABLE` string does not prove successful online execution or baseline ordering. No project test/CI gate exists in the inspected snapshot.

**P0 — make the truth visible**
6. Fix the three brief failures in order: URL (frontend → path params), envelope, identity (retain the returned `brief_id`; remove `'brief-123'` and use an authenticated approver). **Recommended canonical contract: `response.brief.sections`**, matching the current endpoint and required `Brief.sections` JSON field. Update both frontend renderers to consume that contract, optionally through one explicit boundary normaliser. Consolidate/remove the unused flat `generate_brief` implementation rather than maintaining two incompatible envelopes; do not delete the whole `CopilotService` without checking its other functions, including transcript extraction. Add response-schema and generate→render→approve integration tests. This is a proposed remediation decision, not an implemented change.
7. Delete the `// Enrich with real data if missing` block and both hardcoded provenance stamps. Absent provenance is a fail-closed omission; fabricated provenance is a false-green.
8. Make market provenance conditional: stamp `LIVE_FEED` only when a real adapter returned the data, otherwise `UNAVAILABLE`. Relabel `_build_proposed_agenda` as `DERIVED` until an LLM call exists.
9. Replace `except Exception: return []` in ranking with a surfaced error state.

**P1 — make it real**
10. Persist briefs and approvals; wire `AuditService` on every write; create the three missing tables.
11. Wire `MemoryService` into brief context assembly, moving `ClientMemory` into `models.py` and renaming `metadata`.
12. Replace the `validate_provenance` stub with a check that the declared source was actually queried.
13. Fix the frontend failure states (`$NaNM`, no error boundary, stale previous-client modal state risk) and the `tsc` error.

---

## 9. Limits of this re-audit

- **No git repository exists in this directory**, so the 26 changed files could not be diffed against a baseline commit. Verdicts compare the current state against `PROGRESS.md`'s wording, not against a specific revision.
- Runtime verification is limited to what is observable with the app down: import tests, `tsc`, Alembic CLI, schema inspection, log analysis. Endpoint behaviour is asserted from source plus the pre-change runtime evidence.
- The data/release report (`REAUDIT_02_Data_Release.md`) supplies column-level and dependency evidence. The consolidated report distinguishes artifact-level progress from delivered capability for G-28 (§2); the specialist labels are not identical and should not be treated as a single shared scoring rubric.
- **Evidence boundary for HTTP/UI claims:** with the backend down, connection failure was observed. Brief 404s and workflow 422s are contract-derived expected responses after startup is repaired. The nested-envelope defect makes fallback branches execute if that payload reaches the existing renderer; it was not observed as a successful live render in this audit. Version-dependent SQLAlchemy findings are environment-specific. No fresh runtime re-test was performed during report-only corrections.
- **One correction to the first audit is recorded rather than silently dropped:** `pgvector` *is* available in the `timescaledb:latest-pg15` image, so the earlier "image may not ship it" caveat was wrong. The defect is an unused extension plus a floating base-image tag, not a missing extension.
- Absence of a capability is asserted after searching `backend/app`, `frontend/app`, `frontend/components` and `frontend/lib`. A feature hidden in an unregistered script could exist, but no such script is registered in `main.py`.

---

## Appendix — Evidence index

| Claim | Source |
|---|---|
| App does not import | `backend/.venv/bin/python -c "from app.main import app"` → `ImportError: MarketTick` |
| Server down | `backend.pid` 14829 dead; `curl localhost:8000/health` → no response, exit 000 |
| Alembic broken | `.venv/bin/alembic history` → `ValueError ... version_path_separator` |
| No direct API-layer persistence calls | Source search for `db.add` / `.commit()` in `backend/app/api` → 0; does not rule out service/external writes |
| 4 of 5 services unwired | `grep -rn <service>` → only its own `__init__.py` |
| Compose has no app | `docker-compose.yml:2,19` → only `postgres`, `redis` |
| Auth not wired | `config.py:9` `SECRET_KEY` single reference; `pyproject.toml:17-18` unused |
| Envelope mismatch | `briefs.py:29` + `brief_service.py:62-75` vs `BriefModal.tsx:32,47,63` |
| Frontend build fails | `tsc --noEmit` exit 1, `FamilyGraphModal.tsx:125` |
| Canned news rendered | `page.tsx:294-311` literal `HSBC Holdings +2.3%` |

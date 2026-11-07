# RE-AUDIT 01 — Backend Verification of PROGRESS.md Claims

**Repository:** `/Volumes/Orico/code/capco/wealth-workbench`
**Scope:** `backend/` only (read-only; no application code modified)
**Auditor:** backend-auditor
**Date:** 2026-11-07
**Subject of audit:** `PROGRESS.md` (claiming 9 of 11 P0 gaps fixed after a 26-file change set)

---

## 1. Executive Verdict

**The backend does not start. Every claim of "Fixed" in `PROGRESS.md` is either false or
materially overstated.**

Hard evidence, all reproduced during this audit:

| Fact | Evidence |
|---|---|
| `app.main` cannot be imported | `ImportError: cannot import name 'MarketTick' from 'app.models.models'` (`app/services/market/market_service.py:13`) |
| Server is down | `curl http://localhost:8000/health` → HTTP `000` / no response; `backend.pid` (14829) is dead |
| Two additional deleted symbols still imported | `WorkflowStage`, `SourceKind` (`app/services/copilot/copilot_service.py:11`), `SourceKind` (`app/scripts/seed_demo_data.py:10`), `MarketTick`/`WorkflowInstance`/`AuditEvent` (`app/scripts/init_db.py:6-9`) |
| Alembic is non-executable | `alembic history` and `alembic current` both raise `ValueError: 'os  # Use os.pathsep...' is not a valid value for version_path_separator` (`alembic.ini:37`) |
| Migrations were never applied | Live DB tables = `clients, holdings, interactions` only. `briefs`, `audit_logs`, `client_memories` **do not exist** |
| Zero write paths in the API layer | `grep -rn "db.add\|session.add" backend/app` → **no matches in `app/api/`** |
| Four of five new services are dead code | `audit_service`, `memory_service`, `provenance_service`, `workflow_orchestrator` appear only in their own `__init__.py` |
| `/health` "fix" never wired | `app/api/health.py:14` defines the router; no `include_router` anywhere references it; `app/main.py:44-54` still serves hardcoded `"database": "connected"` |
| Alembic would still do nothing if the ini were fixed | `version_locations` → nonexistent `backend/versions` (`alembic.ini:33`), so `upgrade head --sql` emits `BEGIN; COMMIT;` and exits 0 — zero DDL, no error (ND-33). `alembic/script.py.mako` is missing, so no revision can be created either (ND-34) |

Verdict on the change set: **regression, not remediation.** The previous state was "28 requirements
unimplemented but the server could arguably boot." The current state is "the server cannot boot at
all," and the four newly added services are unreachable from any HTTP surface.

### 1.1 Blast radius of the single root cause

Three model classes were deleted from `app/models/models.py` (`MarketTick`, `WorkflowInstance`,
`AuditEvent`) and the `SourceKind` / `WorkflowStage` enums were removed with them. Five files still
import them. Because FastAPI's router aggregation is eager (`app/main.py:5` → `app/api/v1/__init__.py:5`),
**one broken leaf import kills the entire process**, not just the affected feature:

```
app.main
 └── app.api.v1.api_router                (app/api/v1/__init__.py:5)
      ├── clients     → app.services.shariah            OK
      ├── market      → app.services.market   ✗ MarketTick      ← kills boot
      ├── briefs      → app.services.brief    ✗ MarketTick (transitively via market)
      ├── workflow    → app.services.copilot  ✗ WorkflowStage
      ├── dashboard   → app.services.market   ✗ MarketTick
      └── crm         → app.services.crm      OK
```

Import matrix, executed against the project venv:

```
OK    app.models.models
OK    app.services.memory.memory_service        (SAWarning only)
OK    app.services.provenance.provenance_service
OK    app.services.workflow.workflow_orchestrator
OK    app.services.audit.audit_service
FAIL  app.services.brief.brief_service      -> ImportError cannot import name 'MarketTick'
FAIL  app.services.market.market_service    -> ImportError cannot import name 'MarketTick'
FAIL  app.services.copilot.copilot_service  -> ImportError cannot import name 'WorkflowStage'
FAIL  app.api.v1.endpoints.workflow         -> ImportError cannot import name 'MarketTick'
FAIL  app.scripts.init_db                   -> ImportError cannot import name 'MarketTick'
FAIL  app.scripts.seed_demo_data            -> ImportError cannot import name 'SourceKind'
OK    app.scripts.sync_from_hubspot
FAIL  app.main                              -> ImportError cannot import name 'MarketTick'
```

Consequence: `GET /api/v1/dashboard/*`, `/market/*`, `/briefs/*`, `/workflow/*` — **16 of 26 routes**
— cannot be exercised even after the import is patched, because `dashboard.py:10` and `briefs.py:11`
both depend on the same broken market module.

---

## 2. Claim-by-Claim Verification

`PROGRESS.md` asserts nine completed P0 items. Each is checked against code and runtime evidence.

### 2.1 Summary Table

| ID | Claimed | Actual | Verdict |
|---|---|---|---|
| G-04 | Ranking timezone errors fixed | `timezone.utc` applied in 4 places; but `datetime.now()` naive still emitted, and `except Exception: return []` still swallows everything | **Partially fixed** |
| G-25 | Accurate `/health` with real DB check | New accurate endpoint written but **never registered**; old fake endpoint still live | **Not fixed** (dead code added) |
| G-01 | Brief from real data, provenance, versioning | Portfolio + interactions are genuinely DB-backed; changes/news are hash mocks stamped `LIVE_FEED`; agenda claims "AI Generated" with **no LLM call**; brief never persisted so "versioning" does not exist | **Partially fixed + new integrity regression** |
| G-22 | Real workflow state machine | Orchestrator is in-memory, unused (0 callers), executes no stages; live endpoint uses a different service returning `stages: []` | **Not fixed** |
| G-28 | Alembic migrations, .gitignore, AuditService | `.gitignore` entry is real; `alembic.ini` is corrupt so **no migration command runs**; migrations never applied; AuditService never called | **Partially fixed** (hygiene only) |
| G-13 | Client memory model + CRUD | Declared inside a service module, uses reserved `metadata` attribute, `confidence` is `String` while provenance uses `float`, table absent from DB and from both `create_all` and Alembic autogenerate, zero callers | **Not fixed** |
| G-26 | Frontend↔backend contract fixed | Frontend still calls `/briefs/generate` (no path param) while backend now requires `/briefs/generate/{client_id}`; `GET /briefs/{id}` has no backend route at all | **Regressed** |
| G-11 | HubSpot CRM sync | `fetch_contacts_from_hubspot` exists but silently returns `[]` on any error; no pagination, no rate-limit handling, no retry; idempotency keyed on email only | **Partially fixed** |
| G-23 | Provenance tracking prevents fabrication | Validator only checks 4 key names + enum membership; it never sees the underlying data, so it **cannot** detect fabrication; and it is never called | **Not fixed** |

Count as fully delivered: **0 of 9.** The prior audit graded 0/28; this change set does not move that
number, and it moves system availability from "degraded" to "down."

---

### 2.2 G-04 — "Fixed ranking service timezone errors"

**CLAIMED:** "Added timezone.utc to all datetime operations... Ranking now works without TypeError,
returns real client priorities." (`PROGRESS.md:5-9`)

**ACTUAL:** The timezone normalisation is genuinely present and correct in four places:

- `ranking_service.py:117-121` — `datetime.fromisoformat(...)` then `.replace(tzinfo=timezone.utc)`
  if naive, compared against `datetime.now(timezone.utc)`.
- `ranking_service.py:143-148` — same pattern for `suitability_expiry`.
- `ranking_service.py:196-201` — same for `interaction_date`.
- `ranking_service.py:212-215` — inline re-attach for the six-month window.

That part is a real, correct fix. But three qualifications:

1. **Naive datetimes are still emitted.** `ranking_service.py:273` returns
   `"timestamp": datetime.now()` (no `tzinfo`) inside the evidence chip that the UI renders next to
   every ranked client. So the response is internally inconsistent: aware timestamps in the
   provenance of a comparison, naive timestamp in the evidence payload.
2. **The exception swallow is untouched.** `ranking_service.py:81-83` is still
   `except Exception as e: logger.error(...); return []`. Any failure — including the import failure
   this very change set introduced — degrades silently to an empty ranked list. `dashboard.py:41-45`
   then returns HTTP 200 with `ranked_clients: []` and `priority_actions: []`. This is a false
   success: the RM sees a working dashboard with zero clients rather than an error.
3. **Unverified runtime.** The claim "ranking now works" cannot be tested because `dashboard.py`
   imports the broken `market_service` (`dashboard.py:10`). The unit that was fixed has no reachable
   entry point today.

**EVIDENCE:** `ranking_service.py:117-121`, `143-148`, `196-201`, `212-215`, `273`, `81-83`;
`dashboard.py:41-45`, `10`.

**VERDICT: Partially fixed.** Timezone logic yes; swallow-no-more claimed implicitly ("now works")
is not addressed; reachability is zero.

---

### 2.3 G-25 — "Fixed false-success health endpoint"

**CLAIMED:** "Created accurate /health endpoint with real checks. Tests actual database
connectivity. Returns accurate service status. No more false 'healthy' when database is down."
(`PROGRESS.md:11-15`)

**ACTUAL:** A correct implementation exists at `app/api/health.py:14-63`. It does
`await db.execute(text("SELECT 1"))` (`health.py:28`), sets `status: "unhealthy"` on failure
(`health.py:32`), and downgrades to `"degraded"` per service (`health.py:43, 52, 61`). Good work.

**It is not registered.** The router is instantiated at `health.py:12` but:

- `app/api/v1/__init__.py:5` imports only `clients, market, briefs, workflow, dashboard, crm`.
- `app/main.py` contains no `from app.api.health import router` and no
  `app.include_router(health.router)`.

`grep -rn "health" backend/app/main.py backend/app/api/v1/__init__.py` returns nothing.

Therefore the only `/health` FastAPI serves is the **original fake one**, unchanged:

```python
# app/main.py:44-54
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "services": {"market_data": "active", "copilot": "active", "crm": "active"}
    }
```

The `# TODO` the claim says was fixed is still in the live code path, and it still hardcodes
`"database": "connected"`.

Second-order defect: even if registered, `health.py:47` does
`from app.services.market.market_service import market_data_service` inside the handler, which today
raises `ImportError` → the endpoint would permanently report `status: "degraded"`.

**EVIDENCE:** `health.py:12,14,28,32,43`; `api/v1/__init__.py:5`; `main.py:5,44-54`.

**VERDICT: Not fixed.** Correct code was written and then orphaned. Net effect on operators is
identical to before; net effect on the repository is an additional unreferenced module.

---

### 2.4 G-01 — "Brief generation from real data"

**CLAIMED:** "Created BriefService with 5 sections from real sources... Portfolio: from holdings
table; Changes: from live TigerBroker market data; Interactions: from database; News: from
TigerBroker API; Agenda: AI-generated from context; All sections track provenance; Briefs no longer
hardcoded to 'Kenneth Wong'." (`PROGRESS.md:17-25`)

**What is genuinely fixed (credit where due):**

- **Portfolio is a real DB read.** `brief_service.py:86-89` executes
  `select(Holding).where(Holding.client_id == client.id)`. Verified against the live DB: 2 rows for
  `RM001-C001`.
- **Interactions are a real DB read.** `brief_service.py:153-158` executes a `select(Interaction)`
  ordered by `interaction_date desc` with `limit(5)`. Verified: 2 rows.
- **Client lookup is a real DB read** and raises `ValueError` → mapped to HTTP 404 at
  `briefs.py:30-31`.
- **"Kenneth Wong" hardcoding is gone** from the brief path. (It survives elsewhere —
  see §4 defect ND-22 and `workflow.py:117`.)

**What is false:**

**(a) "Changes: from live TigerBroker market data" is a hash-based mock stamped as a live feed.**
`brief_service.py:127-129` calls `market_data_service.detect_market_signal(...)`. That method
(`market_service.py:115-140`) calls `get_real_time_quote`, whose docstring states
*"Returns mock data for now since Tiger SDK has dependency issues"* (`market_service.py:41`) and
which computes:

```python
# market_service.py:51-53
"price": 50.0 + hash(symbol) % 100,
"change": (hash(symbol) % 5) - 2.5,
"change_percent": ((hash(symbol) % 5) - 2.5) / 50.0 * 100,
"source_id": "TigerBroker",
"source_kind": SourceKind.LIVE_FEED if self.mode == "LIVE" else SourceKind.REPLAY,
```

There is **no network call anywhere in the file** (`requests` is imported at
`market_service.py:7` and never used; `hmac`, `hashlib`, `base64`, `time` likewise unused).
The resulting percentage takes exactly one of five values `{-5.0, -3.0, -1.0, +1.0, +3.0}`. With the
default threshold of `2.0` (`brief_service.py:128`), `abs(pct) >= 2` for three of those five values —
so roughly **60% of symbols produce a fabricated "material change"** on every generate call.

Worse, Python's `hash()` for `str` is salted per process (`PYTHONHASHSEED`). Prices and change
percentages therefore **change after every restart and differ between uvicorn workers**. A "live
feed" that is different on every boot is not a feed.

Nevertheless `brief_service.py:142-147` stamps:

```python
"source": "TigerBroker Market Data · LIVE",
"confidence": 1.0,
"source_kind": "LIVE_FEED"
```

`confidence: 1.0` is a statement of certainty about a number derived from `hash()`. This is the exact
failure mode G-23 was supposed to eliminate — a false-green provenance stamp — reintroduced in the
file that claims to implement it.

**(b) "News: from TigerBroker API" is a hardcoded 3-item list.**
`market_service.py:82-107` returns three literal dictionaries (`news-1..news-3`, HSBC Q3 earnings,
HK tech rally, SGX volumes) with `"source": "TigerBroker News"` and `url: "https://example.com/news/1"`.
`get_market_news` slices `news_items[:limit]`. `brief_service.py:196-199` then stamps
`"source": "TigerBroker News · LIVE"`, `confidence: 1.0`, `source_kind: "LIVE_FEED"`.
The content is identical for every client on every run.

**(c) "Agenda: AI-generated from context" makes no LLM call.**
`brief_service.py:203-237`. `_build_proposed_agenda` is pure `if`/`append` logic; there is no import
of `openai`, no `AsyncOpenAI`, no `copilot_service`. It nonetheless returns
`"source": "AI Generated"`, `"confidence": 0.85`, `"source_kind": "ai_generated"`
(`brief_service.py:231-236`). The document literally attributes authorship to an AI that was never
invoked. This is a misrepresentation of method, and it is the most serious integrity defect in the
change set after the boot failure.

**(d) The agenda branch condition is always true.**
`brief_service.py:214`:

```python
if "movement" in changes["content"].lower():
    agenda_items.append("1. Review recent market movements and portfolio impact")
```

When no signal fires, `_build_material_changes` returns the fallback string
`"No material market movements detected in portfolio holdings."` (`brief_service.py:138`), which
contains the substring `"movement"`. So the "review market movements" agenda item is emitted
**unconditionally**, including in the branch that says there were none. The agenda therefore
contradicts its own section 2.

**(e) "Versioning" does not exist.**
`generate_brief` accepts `version: Optional[int]` (`brief_service.py:22`) and writes
`"version": version or 1` into the returned dict (`brief_service.py:66`). That is all. There is no
`Brief(...)` instantiation anywhere in the repository:

```
$ grep -rn "Brief(" backend/app --include=*.py
backend/app/models/models.py:75:class Brief(Base):
```

The only hit is the model declaration. The `briefs` table does not exist in the live database (§3.4).
A version integer that is always `1` and is never stored is not versioning; it is a constant.

**(f) None-safety crash.**
`brief_service.py:104`:

```python
f"  • {holding.symbol}: {holding.quantity} units @ {client.currency} {holding.current_value:,.0f}"
```

`Holding.current_value` is `Column(Float)` with **no** `nullable=False`
(`models.py:44`), so `None` is legal. Formatting `None` with `:,.0f` raises
`TypeError: unsupported format string passed to NoneType.__format__`. Same pattern at
`brief_service.py:96` for `client.aum` (`models.py:19`, nullable). One incomplete holding row
takes the whole brief to HTTP 500.

**(g) Interaction recency is miscomputed for aware datetimes.**
`brief_service.py:163`:

```python
days_ago = (datetime.now(timezone.utc) - interaction.interaction_date.replace(tzinfo=timezone.utc)).days
```

`.replace(tzinfo=...)` is called unconditionally. If `interaction_date` is already timezone-aware
(e.g. stored as `timestamptz`, or set from `datetime.now(timezone.utc)` by a writer), the replace
**overwrites** the real offset rather than converting, shifting `days_ago` by the offset difference.
The safe idiom — the one ranking_service actually uses (`ranking_service.py:198-199`) — is
`if dt.tzinfo is None: dt = dt.replace(...)`. The fix was applied in one file and not the other.

**EVIDENCE:** `brief_service.py:22, 66, 86-89, 96, 104, 127-129, 138, 142-147, 153-158,
163, 196-199, 203-237`; `market_service.py:7, 41, 51-53, 82-107, 115-140`; `briefs.py:14-34`;
`models.py:19, 44, 75-86`; `grep "Brief(" → models.py only`.

**VERDICT: Partially fixed**, and the partial fix introduced a **provenance-integrity regression**:
two of five sections are mock data labelled `LIVE_FEED` at `confidence 1.0`, and one section claims
AI authorship it never had.

---

### 2.5 G-22 — "Workflow state machine"

**CLAIMED:** "Created WorkflowOrchestrator with proper state management. 4-stage workflow:
rank → brief → meeting → review. State transitions with validation. Stage status tracking. **Real
state machine, not static dict with empty stages[]**." (`PROGRESS.md:27-32`)

**ACTUAL:** `workflow_orchestrator.py` (88 lines) defines `WorkflowStage`
(`:12-17`), `WorkflowState` (`:19-24`), a transition map (`:28-33`), `create_workflow` (`:35-50`) and
`transition_stage` (`:52-85`). No persistence, no execution.

**It is never called.** Exhaustive reference search:

```
$ grep -rn "workflow_orchestrator" backend/app --include=*.py
backend/app/services/workflow/workflow_orchestrator.py:87:workflow_orchestrator = WorkflowOrchestrator()
backend/app/services/workflow/__init__.py:2:from app.services.workflow.workflow_orchestrator import workflow_orchestrator
backend/app/services/workflow/__init__.py:4:__all__ = ['workflow_orchestrator']
```

Zero hits in `app/api/`. The live workflow endpoints use a **different** service:
`workflow.py:7` imports `copilot_service`, and `workflow.py:34` calls
`copilot_service.orchestrate_workflow(...)`, which returns:

```python
# copilot_service.py:187-196
workflow_instance = {
    "correlation_id": str(correlation_id),
    ...
    "stages": [],                      # ← the exact "empty stages[]" the claim says was removed
    "current_stage": WorkflowStage.RANK_CLIENTS.value,
    "status": "in_progress",
}
```

So the response the frontend actually receives from `POST /api/v1/workflow/start` still contains
`"stages": []`. The object the claim disparages is still on the wire, produced by a different module.

Assessing "real state machine":

- `transition_stage(workflow, current_stage, result)` (`:52-57`) takes the workflow dict as a
  **parameter and mutates it in place**. There is no registry, no lookup by `workflow_id`, no
  concurrency control. Two concurrent requests for the same workflow are not serialised because
  there is nothing shared to serialise.
- There is **no stage execution**. `result` is stored as opaque data (`:64`): the orchestrator never
  ranks clients, never generates a brief, never captures a meeting. "4-stage workflow" is a
  four-key dictionary.
- `transition_stage` has no guard for illegal transitions: it calls
  `stage_enum = WorkflowStage(current_stage)` (`:60`) and looks up
  `self.stage_transitions.get(...)` (`:68`). Any valid stage string that appears out of order (e.g.
  jumping `meeting.capture` → `review.approve`) is accepted. The claim "state transitions with
  validation" has no supporting code.
- `create_workflow` builds IDs from `int(datetime.now(...).timestamp())` (`:38`). Two workflows
  created for the same `(rm_id, client_id)` within the same second receive **identical IDs**.
- Because the object is a plain `dict` created per call and discarded, and the constructor holds
  no state beyond the transition map, the module is a pure function library. Calling it a
  "state machine" is generous; calling it "real" is not defensible when nothing instantiates it.

**EVIDENCE:** `workflow_orchestrator.py:12-17, 19-24, 28-33, 35-50, 38, 52-57, 60, 64, 68, 87`;
`workflow/__init__.py:2,4`; `workflow.py:7, 34`; `copilot_service.py:187-196`;
`grep workflow_orchestrator → 3 hits, all in the module's own package`.

**VERDICT: Not fixed.** A dead, in-memory dictionary helper was added next to a live endpoint that
still returns `stages: []`.

---

### 2.6 G-28 — "Release hygiene"

**CLAIMED:** "Created Alembic migrations (briefs, audit_logs, client_memories). Added .gitignore
with HUBSPOT_CREDENTIALS.md. Created AuditService for action tracking. Migration README with
instructions. **Impact: Database version controlled, credentials protected.**" (`PROGRESS.md:34-39`)

Four sub-claims; two true, two false.

**(a) `.gitignore` — TRUE.** `.gitignore:32-36`:

```
# Credentials (G-28 fix)
HUBSPOT_CREDENTIALS.md
*_credentials.json
*.pem
*.key
```

`.env` is also ignored (`.gitignore:12-14`). This is real and correct. Caveat: the repository is not
a git repo (`git status` unavailable; env reports "Is directory a git repo: No"), so "protected" is
currently theoretical — the files sit in the working tree either way (§4, ND-19).

**(b) "Alembic migrations created" — FILES EXIST, TOOLING BROKEN.**
`alembic/versions/001_add_briefs_audit.py` and `002_add_client_memories.py` are syntactically
plausible. But `alembic.ini:37` is corrupt:

```
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.
```

Alembic does not strip inline comments in this key. Every command fails at config parse:

```
$ ./.venv/bin/alembic history
ValueError: 'os  # Use os.pathsep. Default configuration used for new projects.'
is not a valid value for version_path_separator; expected 'space', 'newline', 'os', ':', ';'

$ ./.venv/bin/alembic current
ValueError: (same)
```

"Migration README with instructions" instructs the operator to run a command that cannot run.

**(c) "Database version controlled" — FALSE.** There is no `alembic_version` table in the live
database (full table list below). The migrations have never been applied. Worse, they **could not**
be applied to a fresh database either: `001_add_briefs_audit.py:20-32` creates `briefs` with
`sa.ForeignKeyConstraint(['client_id'], ['clients.id'])`, but neither `001` nor `002` creates the
`clients`, `holdings` or `interactions` tables. Those only ever exist because someone ran
`Base.metadata.create_all` directly. `alembic upgrade head` against an empty database fails on a
missing referenced table. The migration chain has no baseline.

**(d) AuditService exists but is never invoked.** `audit_service.py:14-45` is a correct
`INSERT`-and-commit. Its only references are `audit/__init__.py:2,4`. No endpoint, no service, and
critically **not `briefs.py:36-58`**, whose docstring promises "Records the approval in audit log"
while the body is `# TODO: Store approval in database with audit trail` returning a hardcoded
timestamp (`briefs.py:48-54`).

**EVIDENCE:** `.gitignore:12-14,32-36`; `alembic.ini:37`; `alembic/versions/001_add_briefs_audit.py:20-32`;
`alembic/versions/002_add_client_memories.py:20-33`; `audit_service.py:14-45`;
`audit/__init__.py:2,4`; `briefs.py:44-54`; runtime: `alembic history` / `alembic current` ValueError.

**VERDICT: Partially fixed** — release hygiene (`.gitignore`) improved; "database version controlled"
is false in the strongest possible sense: the tool cannot start and the schema was never migrated.

---

### 2.7 G-13 — "Client memory / relationship graph"

**CLAIMED:** "Created ClientMemory model for persistent context. Implemented MemoryService for CRUD
operations. Support for preference, relationship, context memory types. Confidence and source
tracking. **Impact: Persistent D5 memory, not just flat Interaction rows.**" (`PROGRESS.md:41-46`)

**ACTUAL:** Six independent problems, any one of which defeats the claim.

**(a) The model lives in a service module, not `models.py`.**
`memory_service.py:16-29` declares `class ClientMemory(Base)` inside the service file. Consequences:

- `app/models/models.py` — the single place Alembic and every reader looks — does not know about it.
- `alembic/env.py:15` does `from app.models.models import *` and nothing else.
  `Base.metadata` at autogenerate time therefore lacks `client_memories`, so autogenerate would
  emit a **DROP TABLE** for it if the table ever existed.
- `app/scripts/init_db.py:6-9` imports only model classes from `app.models.models`, then calls
  `Base.metadata.create_all` (`init_db.py:19`). Importing a model is what registers it. Since
  `memory_service` is never imported by `init_db`, `create_all` will **not** create
  `client_memories`.

This is not theoretical — the live database confirms it (§2.7f).

**(b) `metadata` is a reserved SQLAlchemy attribute name — and its behaviour is
environment-dependent.**
`memory_service.py:25`: `metadata = Column(JSON, default=dict)`. The declarative API reserves
`metadata` for the `MetaData` instance. On the **installed** SQLAlchemy 2.1.8 importing the module
emits only:

```
SAWarning: Attribute name 'metadata' should be left reserved for the MetaData instance
when using a Declarative class.
  class ClientMemory(Base):
```

and the class is created; `ClientMemory.metadata` resolves to the *column descriptor*, shadowing the
intended `MetaData` accessor. But `requirements.txt:8` pins `sqlalchemy==2.0.25`, and **on that
version it is a hard failure**. Verified independently in an isolated environment
(`uv run --python 3.11 --with "sqlalchemy==2.0.25"`):

```
sqlalchemy 2.0.25
RESULT: InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

That distinction matters because the two supported start paths install different majors:
`start.sh:49` (`uv sync`) → 2.1.8 (warn); `Dockerfile:13` (`pip install -r requirements.txt`) →
2.0.25 (**raise**). So "the module imports fine" is true only on the venv path; under the Docker image
`import app.services.memory.memory_service` raises `InvalidRequestError` before any request is served.
Either way the attribute is unsafe; the severity depends on the interpreter.

Nothing in the current code path reads `ClientMemory.metadata`, so on 2.1.8 it does not crash today —
but it silently breaks any generic SQLAlchemy tooling (`inspect()`, `__table__`-derived helpers) that
walks `cls.metadata`. This is documented-unsafe usage, not a stylistic nit.

**(c) `confidence` is a `String`, contradicting the provenance contract.**
`memory_service.py:26`: `confidence = Column(String)  # low, medium, high`.
Verified: `ClientMemory.__table__.c.confidence.type` → `VARCHAR`.
But `provenance_service.create_provenance` types confidence as `float = 1.0`
(`provenance_service.py:24`), and `brief_service` emits `1.0`, `0.92`, `0.85`
(`brief_service.py:112, 175, 234`). The system now has **two incompatible confidence scales** —
`"medium"` vs `0.85` — with no conversion anywhere. Any UI that sorts or thresholds on confidence
will silently misbehave across the two.

**(d) The table was never created.** Live schema:

```
TABLES: ['clients', 'holdings', 'interactions']
  clients: 3 rows
  holdings: 2 rows
  interactions: 2 rows
  briefs: MISSING (UndefinedTableError)
  audit_logs: MISSING (UndefinedTableError)
  client_memories: MISSING (UndefinedTableError)
```

`002_add_client_memories.py` was never applied, and `memory_service` is never imported at boot, so
neither migration nor `create_all` produced it.

**(e) Zero callers.** `memory_service` appears only in `memory/__init__.py:2,4`. No endpoint reads or
writes memories. `brief_service._build_recent_interactions` is annotated
`"""Build recent interactions from database + HubSpot"""` (`brief_service.py:151`) but only queries
`Interaction` — it never touches `ClientMemory`. So the brief, the one consumer that should read
memory, does not.

**(f) If it were called, it would 500.** `memory_service.py:57` does `await db.commit()` inside the
service while `get_db` also commits after `yield` (`database.py:41`) — double commit, and the
service's own `rollback` (`memory_service.py:63`) would then roll back nothing. `memory_service.py:46`
does `uuid.UUID(client_id)` with no guard: a non-UUID path parameter raises
`ValueError` before the DB is touched, surfacing as a 500 rather than 422.

**EVIDENCE:** `memory_service.py:16-29, 25, 26, 46, 57, 63, 102`; `models/__init__.py:1`;
`alembic/env.py:15`; `init_db.py:6-9,19`; `provenance_service.py:24`; `brief_service.py:112,151,175,234`;
runtime: `SAWarning` on import; `client_memories` absent from `pg_tables`.

**VERDICT: Not fixed.** A class was written; a table was not created, not registered, not migrated,
not read, and not written. "Persistent D5 memory" is exactly as absent as before, plus one more
conflicting confidence schema.

---

### 2.8 G-26 — "Frontend↔backend contract fixes"

**CLAIMED:** "Fixed briefApi.generate() to use correct URL format. Fixed approval endpoint payload
structure. Updated workflow/start endpoint. **Impact: Frontend can now call APIs without 422
errors.**" (`PROGRESS.md:48-52`)

**ACTUAL:** The two sides were changed in opposite directions and now disagree more than before.

Backend (`briefs.py`):

```python
@router.post("/generate/{client_id}")          # briefs.py:14   ← path parameter
@router.post("/approve/{brief_id}")            # briefs.py:36   ← path parameter
async def approve_brief(brief_id: str, approver: str, edited_agenda: str = None, ...)
                                                # :39            ← approver is a required QUERY param
```

Frontend (`frontend/lib/api.ts`):

```ts
generate: (clientId, forceRegenerate = false) =>
  apiClient.post('/briefs/generate', { client_id: clientId, force_regenerate: forceRegenerate }),   // :62-63
approve: (briefId, approvedBy, editedAgenda) =>
  apiClient.post('/briefs/approve', { brief_id: briefId, approved_by: approvedBy, edited_agenda: editedAgenda }),  // :65-66
getBrief: (briefId) => apiClient.get(`/briefs/${briefId}`),                                          // :68-69
```

Resulting failures:

| Frontend call | Backend route | Result |
|---|---|---|
| `POST /api/v1/briefs/generate` (body) | `POST /api/v1/briefs/generate/{client_id}` | **404 Not Found** — no such route |
| `POST /api/v1/briefs/approve` (body) | `POST /api/v1/briefs/approve/{brief_id}` | **404 Not Found** |
| `GET /api/v1/briefs/{brief_id}` | *(none)* | **404** — `getBrief` has no backend counterpart at all |
| `POST /api/v1/workflow/start` `{workflow_type, client_id, trigger}` (`api.ts:74-75`) | `start_workflow(workflow_type: str, client_id: str, trigger: Dict)` (`workflow.py:25-31`) | **422** — `workflow_type` and `client_id` are scalar function params ⇒ FastAPI binds them as **query** params, not body fields |
| `POST /api/v1/workflow/extract-insights` body | `extract_meeting_insights(transcript: str, client_id: str, ...)` (`workflow.py:108-113`) | **422** — both are query params |
| *(response shape)* frontend reads `brief.portfolio_overview` (`BriefModal.tsx:122,126,135,148,156`; `page.tsx:75,78,86,99,107`) | backend wraps sections one level deeper: `{"brief": {"sections": {…}}}` (`brief_service.py:62-75` + `briefs.py:29`) | **Silent empty render** — every section resolves `undefined`; all five UI panels fall back to placeholder text |

So the claimed outcome — "can now call APIs without 422 errors" — is the opposite of reality: the
frontend receives **404 on all three brief calls** and **422 on two of five workflow calls**. The
422s are new, produced by the change, because the payload shape was never reconciled.

**The envelope mismatch is the most damaging item**, because it is silent and it makes the
fabrication path unconditional. `briefs.py:29` returns `{"brief": brief}`, and
`brief_service.py:62-75` nests all five sections under `"sections"`:

```python
brief = {
    "brief_id": ..., "client_id": ..., "client_name": ..., "version": ...,
    "sections": {
        "portfolio_overview": portfolio_section,
        "material_changes": changes_section,
        ...
    }
}
```

The frontend destructures only to `response.data.brief` (`BriefModal.tsx:29`) and then reads
`briefData.recent_interactions`, `briefData.market_news`, `briefData.proposed_agenda` — i.e. one level
too shallow. All are `undefined`, always. Consequences:

- `BriefModal.tsx:32` `if (!briefData.recent_interactions?.content)` → **always true** → the hardcoded
  "CRM & D5 Memory / confidence 0.92" fabrication always executes (§9.6).
- `BriefModal.tsx:47` `if (!briefData.market_news?.content)` → **always true** → the hardcoded
  "TigerBroker News · LIVE / confidence 1.0" fabrication always executes.
- `BriefModal.tsx:63` `briefData.proposed_agenda?.content || <hardcoded 5-item agenda>` → always the
  literal agenda.
- `BriefModal.tsx:122,135,148,156` and `page.tsx:75,86,99,107` render
  `'Portfolio data temporarily unavailable.'` / `'No significant changes detected.'` /
  `'Interaction history available in client record.'` / `'Market news feed temporarily unavailable.'`
  — **three of these four are byte-identical** to the fallbacks in `copilot_service.py:157-175`
  `_generate_fallback_brief` (`:167`↔`BriefModal.tsx:135`, `:169`↔`:148`, `:172`↔`:156`); the fourth
  is a **prefix** of the backend string (`'Portfolio data temporarily unavailable.'` vs
  `'Portfolio data temporarily unavailable. Please review manually.'` at `:162-164`). The visual
  effect is that the UI looks like a legitimate fallback rather than a wiring bug.

Net user-visible behaviour even if every URL were corrected: the RM sees four placeholder panels and
two blocks of fabricated content stamped `LIVE` / `confidence 1.0`.

**Root cause of the envelope split — two brief generators exist and the client was written against
the dead one.** This is not "the frontend forgot to update"; it is a wiring regression.

| Generator | Shape returned | Callers |
|---|---|---|
| `CopilotService.generate_brief` (`copilot_service.py:27-91`) | **flat**: `{portfolio_overview, material_changes, recent_interactions, market_news, proposed_agenda}` | **ZERO.** Only definitions of `generate_brief` in the repo are `briefs.py:15` (the endpoint fn), `copilot_service.py:27`, `brief_service.py:18`; the only call site is `briefs.py:28` → `brief_service` |
| `BriefService.generate_brief` (`brief_service.py:18-82`) | **nested**: `{"sections": {…}}` | one: `briefs.py:7,28` |

The frontend's accessor path (`BriefModal.tsx:32,47,63,122`) matches `CopilotService`'s **flat**
shape exactly — i.e. it matches a service that was subsequently bypassed. So the endpoint wiring
changed underneath a client that was correct against the previous implementation. Vertex: the flat
shape is the one the frontend and `_generate_fallback_brief` both assume, and it is the one no longer
served. Fixing this requires choosing a shape, not just editing whichever side is wrong.

Additional pre-existing frontend defect worth flagging to the frontend auditor (not attributable to
this change set): `api.ts:36`

```ts
apiClient.get(`/market/news${symbols ? `?symbols=${symbols.join(',')}` : ''}?limit=${limit}`)
```

emits `?symbols=A,B?limit=20` — two `?`. `limit` is absorbed into the `symbols` value.

**EVIDENCE:** `briefs.py:14,29,36,39`; `brief_service.py:32,62-75`; `frontend/lib/api.ts:62-69, 74-75,
86-87`; `frontend/components/BriefModal.tsx:29,32,42,47,55,57,63,77,122,135,148,156`;
`frontend/app/brief/[clientId]/page.tsx:23,33,75,86,99,107`; `copilot_service.py:157-175`;
`workflow.py:25-31, 108-113`.

**VERDICT: Regressed.** The backend changed its URL shape and its response envelope while the
frontend kept both old shapes; the "fix" introduced the mismatches it claims to remove, and the
envelope change additionally converts the client-side fabrication branches into always-on paths.

---

### 2.9 G-11 — "HubSpot CRM sync"

**CLAIMED:** "Implemented fetch_contacts_from_hubspot() method. Created sync_from_hubspot.py script
with create/update logic. Syncs contacts from HubSpot to local database. Maps HubSpot custom
properties to client fields. **Impact: Real HubSpot integration, not broken/mock.**"
(`PROGRESS.md:54-59`)

**ACTUAL:** Partially real, with silent-failure and correctness gaps.

**What is real:** `crm_service.py:102-135` genuinely calls the HubSpot SDK —
`self.client.crm.contacts.search_api.do_search(public_object_search_request=...)` (`:119-121`) — and
returns `[{hubspot_id, properties}]`. `sync_from_hubspot.py:17-84` performs real
`select(Client)` / `session.add` / `session.commit` with create-vs-update branching keyed on email
(`:46-49`). The import succeeds (unlike every other script): `OK app.scripts.sync_from_hubspot`.
This is the only genuinely working new capability in the change set.

**What is wrong:**

1. **Every error is swallowed into an empty list.** `crm_service.py:133-135`:
   `except Exception as e: logger.error(...); return []`. `sync_from_hubspot.py:29-31` then sees
   `if not contacts: logger.warning("No contacts fetched from HubSpot"); return` — exit code **0**.
   A wrong token, an expired PAT, a 429, or a network outage are indistinguishable from an empty
   CRM, and the operator is told "sync complete" success-by-silence. This is the same false-success
   pattern as G-25 and G-04.
2. **No pagination.** `crm_service.py:109-117` issues a single search request with `"limit": limit`
   (default 100). HubSpot's search API pages via `after`; no cursor is ever followed, no
   `response.paging` inspection, no loop. Sub-claim "Syncs contacts from HubSpot" is true only for
   the first ≤100 contacts and is silently incomplete beyond that.
3. **No rate-limit handling.** HubSpot enforces per-10-second limits and returns 429 with a
   `Retry-After` header. There is no retry, no backoff, no `Retry-After` parse anywhere in
   `crm_service.py`. On burst, the first 429 aborts the whole sync and is absorbed by (1).
4. **Idempotency is email-only and breaks on missing email.** `sync_from_hubspot.py:40-43` silently
   `continue`s any contact without `email`. `client.email` is nullable (`models.py:17`) and
   `external_id` is the actual unique key (`models.py:15`), but the sync matches on the *non-unique,
   nullable* email column. Two HubSpot contacts sharing an email will collapse to one local client;
   a contact whose email changed in HubSpot creates a duplicate local client.
5. **Unsafe numeric coercion.** `sync_from_hubspot.py:55, 69`:
   `float(props.get("rm_aum", 0)) if props.get("rm_aum") else None`. HubSpot properties are always
   strings; `rm_aum = "1,200,000"` or `"N/A"` raises `ValueError`, which propagates to the outer
   handler (`:81-84`) and **rolls back the entire batch** — one bad contact discards every other
   contact's changes.
6. **Duplicate, conflicting CRM implementations.** `crm_service.py:11` and
   `hubspot_service.py:11` both declare `class CRMService`, both export a `crm_service` singleton.
   `hubspot_service.CRMService.sync_client` (`:28-30`) calls
   `basic_api.get_by_id(contact_id=email, ...)` — passing an email where a HubSpot record ID is
   required, which is guaranteed-wrong. Nothing imports `hubspot_service`, so it is dead — but it is
   dead code that looks authoritative and will be picked up by the next developer.
7. **Credentials mismatch.** Root `.env:16-18` holds live-looking credentials
   (`HUBSPOT_ACCESS_TOKEN=pat-na2-...`, `HUBSPOT_PERSONAL_ACCESS_KEY=CiRuYTIt...`) while
   `backend/.env:16-17` holds `HUBSPOT_ACCESS_TOKEN=demo_hub...`. `config.py:56` sets
   `env_file = "../.env"`, i.e. **relative to CWD**. Run uvicorn from `backend/` → root `.env`
   (real token). Run from repo root → `.env` at CWD/../.env → not found → `SECRET_KEY` missing →
   `ValidationError` at import. The effective credential set depends on the shell's working
   directory.

**EVIDENCE:** `crm_service.py:102-135, 109-117, 133-135`; `sync_from_hubspot.py:29-31, 40-43, 46-49, 55, 69, 81-84`;
`hubspot_service.py:11, 28-30`; `models.py:15,17`; `config.py:56`; `.env:16-18`; `backend/.env:16-17`;
runtime: `OK app.scripts.sync_from_hubspot`.

**VERDICT: Partially fixed.** The outbound call is real. Error handling, pagination, rate limits and
idempotency are all absent, and failure is reported as success.

---

### 2.10 G-23 — "Provenance tracking"

**CLAIMED:** "Created ProvenanceService with validation. Defined ProvenanceSourceKind enum.
Per-statement provenance in all brief sections. **Validation prevents fabricated provenance.**
**Impact: No more false-green provenance stamps.**" (`PROGRESS.md:61-66`)

**ACTUAL:** Two components exist; neither does what is claimed.

**(a) `validate_provenance` cannot detect fabrication — by construction.**
The entire function is `provenance_service.py:39-58`:

```python
required_fields = ["source", "source_kind", "timestamp", "confidence"]
for field in required_fields:
    if field not in provenance:
        return False
try:
    ProvenanceSourceKind(provenance["source_kind"])
except ValueError:
    return False
return True
```

It receives a **dict the caller constructed**. It checks (i) four keys are present and (ii)
`source_kind` is a member of the enum. It has no access to the data the provenance describes, no
notion of the producing code path, and no signature/attestation. Therefore:

```python
provenance_service.validate_provenance({
    "source": "TigerBroker Market Data · LIVE",
    "source_kind": "LIVE_FEED",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "confidence": 1.0,
})
# → True
```

That is a *verbatim* description of the fabricated mock in `brief_service.py:142-147`, and the
validator returns `True`. The same holds for `"source": "AI Generated"` with `source_kind`
`"ai_generated"` and `confidence 0.85` (`brief_service.py:231-236`) — validator approves. So the
claim "no more false-green provenance stamps" is falsified by the validator itself: it is a
schema-shape checker, and both false stamps are schema-shaped.

What it *would* catch: a missing key, or a typo like `"LIVE"` / `"live_feed"` instead of `"LIVE_FEED"`.
That is a lint, not an integrity control.

**(b) It is never called.** Reference search:

```
$ grep -rn "provenance_service" backend/app --include=*.py
backend/app/services/provenance/provenance_service.py:60:provenance_service = ProvenanceService()
backend/app/services/provenance/__init__.py:2:from ... import provenance_service
backend/app/services/provenance/__init__.py:4:__all__ = ['provenance_service']
```

Zero callers. `brief_service` builds provenance dicts **by hand** (`brief_service.py:109-114,
142-147, 172-177, 195-200, 231-236`) and never validates them — and could not, because validation
is not wired into the response path.

**(c) The enum and the hand-written values have drifted.** `ProvenanceSourceKind`
(`provenance_service.py:12-17`) defines `DATABASE="database"`, `LIVE_FEED="LIVE_FEED"`,
`CRM="crm"`, `AI_GENERATED="ai_generated"`, `DERIVED="DERIVED"`. `brief_service` writes raw string
literals `"database"`, `"LIVE_FEED"`, `"ai_generated"` — coincidentally matching, and only because
nobody used the enum. The module that owns the vocabulary is not the module that speaks it.

**(d) `CRM` members are never used by the CRM-backed section.** `_build_recent_interactions`
stamps `"source": "CRM & D5 Memory"` with `source_kind: "database"` (`brief_service.py:173-176`)
even though section (e) of G-13 established that D5 memory (`ClientMemory`) is never read. The
label names a source that is not in the data path.

**EVIDENCE:** `provenance_service.py:12-17, 39-58, 60`; `provenance/__init__.py:2,4`;
`brief_service.py:109-114, 142-147, 172-177, 195-200, 231-236`; `grep provenance_service → only own package`.

**VERDICT: Not fixed.** A four-key presence check was written, never called, and cannot detect the
exact fabrications it was created to prevent — two of which exist in the same change set.

---

## 3. Full Route Table

All routes were enumerated with:

```
grep -rnE '@router\.(get|post|put|patch|delete)' backend/app/api
grep -nE '@app\.(get|post|put|patch|delete)'   backend/app/main.py
```

**Legend for "Persists?":** `No` = endpoint never issues `db.add` / `INSERT` / `UPDATE` / `DELETE`.
Verified globally: `grep -rn "db.add\|session.add" backend/app` returns **zero hits under `app/api/`**
and the only `INSERT`-capable code is `memory_service.py:56` and `audit_service.py:37`, neither of
which is reachable from HTTP.
**"Boot?"** = reachable today. Every route behind a broken import is marked ✗.

### 3.1 Root / unversioned (served by `app/main.py`)

| # | Method + Path | Handler | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 1 | `GET /` | `main.py:35-42` | Returns static banner: message, version, status `"active"`, tagline | No | Mild — `"status": "active"` while app is dead | Hardcoded literals | ✓ (if app imported) |
| 2 | `GET /health` | `main.py:44-54` | Returns `status:"healthy"`, `database:"connected"`, 3 services `"active"` | No | **YES — severe.** Hardcodes `"database": "connected"` with live `# TODO` on the same line (`:48`); never probes anything | Hardcoded literals | ✓ |
| — | `GET /health` | `api/health.py:14-63` | Accurate: real `SELECT 1` (`:28`), `unhealthy` on failure (`:32`), `degraded` per service (`:43,52,61`) | No | No | Real DB + import probes | **✗ NOT REGISTERED** |

Route 2 and the unregistered route collide on the same path. Because `health.py`'s router is never
included (`api/v1/__init__.py:5` lists six routers, not seven), the accurate implementation is
unreachable and the fake one wins. This is the single clearest illustration of the change set's
pattern: correct code written, never wired.

### 3.2 `/api/v1/clients` (`clients.py`)

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 3 | `GET /api/v1/clients/` | 27-42 | `select(Client).offset(skip).limit(limit)`; returns `{"clients":[c.__dict__...],"count":n}` | No | No | **Real DB** | ✓ |
| 4 | `GET /api/v1/clients/{client_id}` | 44-62 | `select(Client).where(id==client_id)`; 404 if absent | No | No | **Real DB** | ✓ |
| 5 | `GET /api/v1/clients/{client_id}/portfolio` | 64-83 | `select(Holding)` for client; `total_value = sum(current_value or 0)` | No | No | **Real DB** | ✓ |
| 6 | `GET /api/v1/clients/{client_id}/shariah-report` | 85-134 | Screens each holding, computes zakat, returns report | No | **YES** — `screen_instrument` returns `"compliant": True  # Placeholder` (`shariah_service.py:35-37`); `business_description` is passed as `""` (`clients.py:103`) so the prohibited-keyword check can never fire; zakat uses hardcoded `"2025-01-01"` hawl date (`:120`) | Real DB holdings + **stub compliance logic** | ✓ |

Note on route 3: `c.__dict__` (`clients.py:39`) returns the ORM instance dict including
`_sa_instance_state`. Verified key list at runtime:
`['_sa_instance_state','aum','client_type','created_at',...,'updated_at']`.
`jsonable_encoder` drops it, so the response works, but the endpoint bypasses Pydantic response
models entirely — no field filtering, no schema stability, and `preferences`/`family_entities` JSON
columns are echoed verbatim to the caller.

### 3.3 `/api/v1/market` (`market.py`) — **all five routes dead at import**

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 7 | `GET /api/v1/market/quotes` | 12-23 | Splits symbols, calls `get_real_time_quote` | No | **YES** — `source_id:"TigerBroker"`, `source_kind: LIVE_FEED`, but values are `50.0 + hash(symbol) % 100` (`market_service.py:51-56`) | **Mock (hash)** | ✗ |
| 8 | `GET /api/v1/market/news` | 25-37 | Returns 3 hardcoded articles sliced to `limit` | No | **YES** — `"source":"TigerBroker News"`, `url: example.com` (`market_service.py:82-107`) | **Hardcoded** | ✗ |
| 9 | `GET /api/v1/market/signals` | 39-55 | Loops symbols, keeps those with \|Δ\| ≥ threshold | No | **YES** — signal derived from mock hash; ~60% fire at default 2.0 | **Mock (hash)** | ✗ |
| 10 | `GET /api/v1/market/historical/{symbol}` | 57-69 | Generates `min(limit,30)` synthetic OHLC points | No | **YES** — synthetic but unlabelled as such | **Synthetic** | ✗ |
| 11 | `POST /api/v1/market/mode` | 71-78 | `market_data_service.set_mode(mode)` mutates a **process-global singleton** (`market_service.py:171-177`) | No — in-memory, lost on restart, not per-user, no auth | No | N/A (control) | ✗ |

`market_service.py` imports `requests`, `base64`, `hmac`, `hashlib`, `time`
(`market_service.py:7-11`) and uses **none** of them. `_sign_request` (`:29-36`) returns a bearer
token or `""` and is never called. There is no HTTP client invocation in the file.

### 3.4 `/api/v1/briefs` (`briefs.py`) — **dead at import (`briefs.py:11` → market_service)**

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 12 | `POST /api/v1/briefs/generate/{client_id}` | 14-34 | Calls `brief_service.generate_brief`, wraps as `{"brief": ...}` | **No** — `Brief` model never instantiated (grep: only `models.py:75`) | **YES** — `material_changes` + `market_news` are mock data stamped `LIVE_FEED`/`confidence 1.0`; `proposed_agenda` claims `"AI Generated"`/`0.85` with no LLM call; `"version": 1` implied versioning that does not exist | Portfolio/interactions **real DB**; changes/news **mock**; agenda **template** | ✗ |
| 13 | `POST /api/v1/briefs/approve/{brief_id}` | 36-58 | Returns a dict claiming approval | **No** — body is `# TODO: Store approval in database with audit trail` (`:48`) | **YES — severe.** Returns `"status":"approved"` and `"approved_at":"2024-11-07T12:00:00Z"` (`:49-54`) — a hardcoded date, in the past relative to audit date, for a brief that was never stored and whose ID is not validated | **Hardcoded** | ✗ |
| — | `GET /api/v1/briefs/{brief_id}` | — | **No such route** — frontend `api.ts:68-69` calls it | — | — | — | n/a |

Route 13 is the most consequential false success in the system: it is approval Gate 1, and it
returns "approved" without touching the database. Combined with the fact that no brief can be
persisted, the approval gate is decorative.

### 3.5 `/api/v1/workflow` (`workflow.py`) — **dead at import (`workflow.py:7` → copilot_service)**

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 14 | `POST /api/v1/workflow/start` | 25-40 | `copilot_service.orchestrate_workflow` returns a literal dict with `"stages": []` (`copilot_service.py:187-196`) | No | **YES** — returns `"status":"in_progress"` for a workflow that was never created | Hardcoded | ✗ |
| 15 | `POST /api/v1/workflow/consent` | 42-60 | Echoes the request back with `"status":"consent_recorded"` | **No** — `# TODO: Store consent in database with C-4 audit log` (`:49`) | **YES** — Gate 2 consent is never recorded; `recording_consent` DB column (`models.py:65`) is untouched | **Echo** | ✗ |
| 16 | `POST /api/v1/workflow/review/approve` | 62-89 | Returns `"actions_executed":["crm_sync","d5_memory_update","email_draft_saved"]`, `"workflow_complete": True` | **No** — `# TODO: Execute all approved actions` (`:69-73`) | **YES — severe.** Claims three side effects executed; **none** is implemented. D5 memory does not exist (G-13), CRM sync is a separate manual endpoint, no email code exists anywhere in the repo | **Hardcoded** | ✗ |
| 17 | `GET /api/v1/workflow/{workflow_id}` | 91-106 | Returns `"status":"in_progress"`, `"current_stage":"brief.generate"` | No — `# TODO: Fetch from database` (`:98`) | **YES** — any string `workflow_id` (even `"x"`) returns 200 `in_progress`; a nonexistent workflow is indistinguishable from a live one | **Hardcoded** | ✗ |
| 18 | `POST /api/v1/workflow/extract-insights` | 108-126 | Calls `copilot_service.extract_meeting_insights` (real LLM call, `copilot_service.py:222-232`) | No | Partly — real LLM, but `client_context = {"name": "Kenneth Wong"}` (`:117`, live `# TODO` on `:116`) → **the "no hardcoded Kenneth Wong" claim is false in this file** | LLM + **hardcoded client context** | ✗ |

Route 16 deserves emphasis: it is Gate 3, the final human approval, and it fabricates the execution
report. This is the same class of defect as the approval endpoint (route 13) but larger, because
three distinct downstream systems are falsely reported as having been written to.

### 3.6 `/api/v1/dashboard` (`dashboard.py`) — **dead at import (`dashboard.py:10`)**

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 19 | `GET /api/v1/dashboard/my-day` | 18-88 | Detects signals on 3 hardcoded watch symbols, ranks clients, fetches news, computes `count`/`sum(aum)` KPI | No | **Partial** — `total_aum`/`total_clients` real (`:54-57`), but `meetings_today: 3`, `open_actions: 7`, `ytd_performance: 5.8` hardcoded with live TODOs (`:63-65`); `workflow.correlation_id: "8f21a4b2"` is a literal (`:80`) | **Mixed: real DB + hardcoded** | ✗ |
| 20 | `GET /api/v1/dashboard/kpis` | 90-112 | Returns a fixed KPI block | No | **YES — severe.** `# TODO: Calculate from database` (`:99`). Returns `total_aum: 428.5e6`, `client_count: 45` while route 19 on the same book returns real values (3 clients, ~198.3M). Two endpoints, same dashboard, contradictory numbers | **Hardcoded** | ✗ |
| 21 | `GET /api/v1/dashboard/book-stats` | 114-132 | Returns `total_clients:45`, `family_offices:8`, `avg_aum:9.5e6`, `meetings_mtd:18`, `net_new_assets_ytd:38e6` | No | **YES** — wholly hardcoded, no DB access at all; `db` dependency is declared (`:117`) and unused | **Hardcoded** | ✗ |
| 22 | `GET /api/v1/dashboard/allocation` | 134-154 | Returns `equities 62 / fixed_income 28 / cash 10` | No | **YES** — hardcoded; no `db` dependency even declared | **Hardcoded** | ✗ |
| 23 | `GET /api/v1/dashboard/performance-trend` | 156-186 | Returns 9 hardcoded month labels and two series | No | **YES** — comment `# Mock YTD performance data` (`:165`) | **Hardcoded** | ✗ |

Routes 20-23 mean the dashboard is ~80% fabricated while route 19 is partly real — a self-inconsistent
UI with no indication which numbers are live.

### 3.7 `/api/v1/crm` (`crm.py`) — **boots, but depends on a live third-party token**

| # | Method + Path | Line | Behaviour | Persists? | False success? | Data source | Boot |
|---|---|---|---|---|---|---|---|
| 24 | `POST /api/v1/crm/sync` | 16-87 | `select(Client)` → per-client `sync_client_to_hubspot`; aggregates created/updated/error | **No local DB write**; outbound HTTP to HubSpot | **Partial** — `"status":"success"` is returned even when `errors > 0` (`:77-83`); and `find_contact_by_email` swallows exceptions to `None` (`crm_service.py:44-46`), so an auth failure is reported as `action:"created"` while `create_contact` raises `ApiException` (`crm_service.py:62-64`) → caught per-client at `crm.py:69-75` → `action:"error"`; net: a dead token yields `status:"success", synced:0, errors:3` | HubSpot API (real SDK) | ✓ |
| 25 | `POST /api/v1/crm/sync/{client_id}` | 90-140 | Single-client variant | No local write | Partial — same pattern | HubSpot API | ✓ |
| 26 | `GET /api/v1/crm/status` | 143-162 | Probes `find_contact_by_email("test@example.com")`; returns `"connected"` if no exception | No | **YES — severe.** `find_contact_by_email` catches **all** exceptions and returns `None` (`crm_service.py:44-46`). Therefore the `except` at `crm.py:157` almost never runs and status is **always** `"connected"`. The variable `result` on `:150` is assigned and discarded. This is structurally identical to the `/health` false success that G-25 was supposed to fix — reproduced in a new endpoint | Claimed HubSpot, actually constant | ✓ |

Route 26 is worth calling out to the team: it is a *new* false-success endpoint added in the same
change set that claims to eliminate false success.

### 3.8 Route totals

**Denominator note.** This report counts **26 endpoints** = **24 under `/api/v1`** (clients 4,
market 5, briefs 2, workflow 5, dashboard 5, crm 3) **+ 2 app-level** (`GET /` and `GET /health` in
`main.py:35,44`). The 24/26 distinction matters: `frontend-auditor` uses 24 because only `/api/v1`
routes are frontend targets; both figures are correct against different denominators. Additionally
`api/health.py:14` defines a **25th `@router`** that is never registered, so it appears below as a
dead definition rather than a route.

| Category | Count |
|---|---|
| Registered endpoints | **26** (24 under `/api/v1` + 2 app-level) |
| Unregistered (dead) route definitions | 1 (`api/health.py:14`) |
| Reachable **today** | **0** — the process cannot be imported at all (ND-01), so no endpoint responds. Counterfactually, if only the import chain were repaired: 9 (2 app-level + 4 `/clients` + 3 `/crm`), or 6 excluding the three `/crm` routes that need a live HubSpot token |
| Dead at import | **17 of 24** `/api/v1` routes — all of `/market` (5), `/briefs` (2), `/workflow` (5), `/dashboard` (5). They would still fail after the app-level import is repaired, because `market.py:6`, `briefs.py:11`, `dashboard.py:10` and `workflow.py:7` each pull in a broken module |
| Routes that persist anything | **0** |
| Routes returning success without performing the work | **17 of 26** — #2, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 26 (see per-route notes; #6 is partial: real holdings data with stubbed compliance logic) |

---

## 4. New Defects Introduced by This Change Set

Each is a regression attributable to the 26-file modification, with severity and location.

### Blocker

**ND-01 — Backend cannot import; server is down.**
`market_service.py:13` imports `MarketTick`, deleted from `models.py`. Eager router aggregation at
`main.py:5` → `api/v1/__init__.py:5` → `market.py:6` propagates the `ImportError` to process start.
Runtime: `curl :8000/health` → `000`; `ps -p 14829` → not running; `backend.log` ends with the
`ImportError` traceback.
*Severity: Blocker.*

**ND-02 — Second independent import break via `copilot_service`.**
`copilot_service.py:11`: `from app.models.models import WorkflowStage, SourceKind` — both deleted.
So even if ND-01 is fixed, `/api/v1/workflow/*` remains dead. `workflow.py:7` imports this module at
module import time.
*Severity: Blocker.*

**ND-03 — Seeding script cannot run.**
`seed_demo_data.py:10` imports `SourceKind` (deleted); used at `:121` (`SourceKind.SEEDED`) and
`:172` (`SourceKind.RM_MANUAL`). Runtime: `FAIL app.scripts.seed_demo_data -> ImportError cannot
import name 'SourceKind'`. No demo data can ever be re-seeded. Corroborating evidence of a partial
seed in the live DB: `holdings.source_kind` is `None` for both rows, though the seeder sets
`SourceKind.SEEDED` — the rows were written before the enum was removed.
*Severity: Blocker.*

**ND-04 — Table-creation script cannot run.**
`init_db.py:6-9` imports `MarketTick`, `WorkflowInstance`, `AuditEvent`. Runtime: `FAIL
app.scripts.init_db -> ImportError cannot import name 'MarketTick'`. There is now **no working way to
create the schema**, because `init_db` is broken and Alembic is broken (ND-05).
*Severity: Blocker.*

**ND-05 — `alembic.ini:37` is syntactically invalid for Alembic.**
`version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.`
Runtime: both `alembic history` and `alembic current` raise
`ValueError: 'os  # Use os.pathsep...' is not a valid value for version_path_separator`.
Every migration command fails before touching the DB.
*Severity: Blocker for release path.*

### High

**ND-06 — Migrations were never applied; three tables do not exist.**
Live `pg_tables` = `['clients','holdings','interactions']`. `briefs`, `audit_logs`,
`client_memories` all raise `UndefinedTableError`. No `alembic_version` table exists. Consequence:
`AuditService.log_action` (`audit_service.py:27-38`) and `MemoryService.store_memory`
(`memory_service.py:45-57`) would raise `UndefinedTableError` on first use — they are latent 500s.
*Severity: High.*

**ND-07 — Migration chain has no baseline.**
`001_add_briefs_audit.py:30` declares `ForeignKeyConstraint(['client_id'], ['clients.id'])` and
`002_add_client_memories.py:31` likewise, but no migration creates `clients`, `holdings`, or
`interactions`. `alembic upgrade head` on a clean database fails on the missing referenced table.
The migrations only ever work on a DB that was created out-of-band by the now-broken `init_db.py`.
*Severity: High.*

**ND-08 — `ClientMemory` is invisible to both schema-creation paths.**
Declared in `memory_service.py:16-29`, not `models.py`. `alembic/env.py:15` imports only
`app.models.models`, so `target_metadata` lacks the table → autogenerate would emit a DROP.
`init_db.py:6-9` imports only model classes → `create_all` (`init_db.py:19`) skips it. Runtime
confirms: after `import app.services.memory.memory_service`, `Base.metadata.tables` **does** contain
`client_memories` (the declarative registry is global), but no code path imports this module at
boot, and the table is absent from the DB.
*Severity: High (silent schema drift).*

**ND-09 — False `LIVE_FEED` provenance stamps on mock data (integrity regression).**
`brief_service.py:142-147` and `:196-199` label hash-derived and hardcoded content as
`"TigerBroker ... · LIVE"` with `confidence: 1.0`. Source data is `market_service.py:51-53`
(`50.0 + hash(symbol) % 100`) and `:82-107` (three literals). Python `hash()` is per-process
salted, so the "live" values change on every restart and differ across workers.
*Severity: High (misrepresents data provenance to an RM making fiduciary decisions).*

**ND-10 — False AI authorship on a template.**
`brief_service.py:231-236` returns `"source": "AI Generated"`, `"confidence": 0.85`,
`"source_kind": "ai_generated"` from `_build_proposed_agenda` (`:203-237`), which contains no LLM
call, no `openai` import, and no service dependency. The system attributes text to a model that was
never invoked.
*Severity: High (misattribution of method in a regulated advice context).*

**ND-11 — Frontend/backend contract regressed on all brief operations.**
Backend moved to path parameters (`briefs.py:14,36`); frontend still posts to collection URLs
(`frontend/lib/api.ts:62-66`) and calls a route that does not exist (`:68-69`). Result: 404 × 3.
Claimed outcome was "no 422 errors."
*Severity: High.*

### Medium

**ND-12 — Two duplicate `CRMService` classes with conflicting semantics.**
`crm_service.py:11` and `hubspot_service.py:11` both define `class CRMService` and export a
module-level `crm_service` singleton (`crm_service.py:204`, `hubspot_service.py:103`). The second
implementations's `sync_client` passes an email as `contact_id` (`hubspot_service.py:28-30`), which
cannot work. Nothing imports it, so it is dead — but it is an authoritative-looking trap.
*Severity: Medium.*

**ND-13 — `None`-unsafe numeric formatting in brief generation.**
`brief_service.py:104` (`holding.current_value:,.0f`) and `:96` (`client.aum:,.0f`) format nullable
columns (`models.py:44`, `models.py:19`) with `:,.0f`. A single row with `NULL` yields
`TypeError` → HTTP 500 for the whole brief.
*Severity: Medium.*

**ND-14 — Agenda branch condition is tautological.**
`brief_service.py:214` tests `"movement" in changes["content"].lower()`, but the negative branch
text is `"No material market movements detected in portfolio holdings."` (`:138`), which contains
`"movement"`. The "review market movements" item is therefore always emitted, contradicting
section 2 of the same brief.
*Severity: Medium (correctness), Low (impact).*

**ND-15 — `/health` fix is dead code; fake endpoint still serves.**
`api/health.py:14` router never included (`api/v1/__init__.py:5`; `main.py` has no reference).
`main.py:44-54` still returns hardcoded `"database": "connected"` with the original `# TODO`.
*Severity: Medium (operational blindness).*

**ND-16 — New false-success endpoint `GET /crm/status`.**
`crm.py:143-162` returns `"connected"` whenever `find_contact_by_email` does not raise — but that
function swallows all exceptions and returns `None` (`crm_service.py:44-46`). Status is effectively
constant `"connected"`. Introduced in the same change set that claims to fix false success.
*Severity: Medium.*

**ND-17 — Workflow endpoints bind body fields as query parameters.**
`workflow.py:25-31` declares `workflow_type: str, client_id: str` as bare scalars → FastAPI treats
them as query params; `trigger: Dict` becomes the body. Frontend sends all three in the body
(`api.ts:74-75`) → 422. Same at `workflow.py:108-113` for `extract-insights`.
*Severity: Medium.*

**ND-18 — `get_db` commits on every request, including reads.**
`database.py:37-46`: after `yield`, `await session.commit()` unconditionally, then `rollback` on
exception. Every `GET` opens a write transaction and commits it. Combined with service-level
`db.commit()` (`memory_service.py:57`, `audit_service.py:38`) this produces double-commit and
makes transaction boundaries unauditable.
*Severity: Medium.*

**ND-19 — Live-looking production secrets in the working tree.**
Root `.env:8-13` contains a Tiger private key (`MIICdwIB...`), `:16-18` a HubSpot PAT
(`pat-na2-...`), `:21` an LLM key (`sk-7dbd3...`); `HUBSPOT_CREDENTIALS.md` is present at the repo
root (3,635 bytes) and is gitignored but not removed. `.gitignore:12-14,33` covers both, but the
repository is not under git, so nothing is actually prevented from being committed later.
*Severity: Medium (High if the repo is ever initialised and pushed).*

**ND-20 — Non-deterministic mock prices produce non-reproducible briefs.**
`market_service.py:51-53` uses `hash(symbol)`, which is salted per interpreter. Two runs, two
workers, or one restart all yield different "market data" for the same symbol. Any downstream
computation (ranking opportunity score at `ranking_service.py:111`, brief material changes) is
therefore non-reproducible.
*Severity: Medium.*

**ND-21 — `except Exception: return []` still hides ranking failure.**
`ranking_service.py:81-83` unchanged. Now that the import chain is broken, this swallow guarantees
the dashboard would render an empty, successful-looking client list if it could boot.
*Severity: Medium.*

**ND-22 — Hardcoded "Kenneth Wong" survives in workflow context.**
`workflow.py:117`: `client_context = {"name": "Kenneth Wong"}` with `# TODO: Fetch client context
from DB` on `:116`. G-01 claims hardcoded clients were eliminated; they were removed from
`brief_service` and left in `workflow`.
*Severity: Medium.*

**ND-23 — Invalid UUID path parameters return 500, not 4xx.**
Verified at runtime: `select(Client).where(Client.id == "not-a-uuid")` raises `DBAPIError: invalid
input for query argument $1: 'not-a-uuid' (invalid UUID ...)`. Affected handlers catch bare
`Exception` and re-raise as HTTP 500: `clients.py:52,72,94`, `crm.py:101`, and `briefs.py` via
`brief_service.py:38`. `memory_service.py:46` raises a bare `ValueError` from `uuid.UUID()`.
*Severity: Medium.*

**ND-24 — Interpolation of `briefs` `version` column cannot happen.**
`models.py:81` declares `version = Column(String, nullable=False)`, but `brief_service.py:66` writes
an `int` into the response dict. When persistence is eventually added, a type mismatch
(`int` → `String` column) will surface. Currently masked by the absence of persistence.
*Severity: Low.*

### Low

**ND-25 — Naive timestamp in ranking evidence.**
`ranking_service.py:273`: `"timestamp": datetime.now()`. Mixes naive and aware timestamps in one
payload, undoing part of the G-04 fix it sits inside.

**ND-26 — `POST /market/mode` mutates a global singleton.**
`market_service.py:171-177` + `market.py:71-78`. No auth, no persistence, no per-user scope; one
caller flips the feed mode for every user of the process.

**ND-27 — `c.__dict__` response serialisation.**
`clients.py:39`, `:78`. Bypasses Pydantic response models; exposes `_sa_instance_state` to the
encoder and echoes raw JSON columns.

**ND-28 — No application tests exist.**
`find` for `test_*.py` under the repo returns only vendored packages
(`backend/.venv/lib/python3.13/site-packages/...`). Zero tests in `backend/app`. Nothing in this
change set could have been caught by CI, because there is none.

**ND-29 — `alembic.ini:43` retains the placeholder URL.**
`sqlalchemy.url = driver://user:pass@localhost/dbname`. `alembic/env.py:21` overrides it from
settings, so this is latent rather than fatal — but combined with ND-05 it is a second reason the
migration path is untrustworthy.

**ND-30 — Migration `001` indexes disagree with the model.**
`001_add_briefs_audit.py:48` creates `ix_audit_logs_entity` on `(entity_type, entity_id)`; the model
`AuditLog` (`models.py:89-99`) declares no indexes and no `index=True` on `entity_id`. Autogenerate
will churn.

**ND-31 — Brief response envelope nesting mismatch makes fabrication unconditional.**
Backend returns `{"brief": {…, "sections": {...}}}` (`briefs.py:29` wrapping `brief_service.py:62-75`).
The frontend reads `response.data.brief` and then `briefData.recent_interactions` /
`briefData.market_news` / `briefData.proposed_agenda` / `brief.portfolio_overview`
(`BriefModal.tsx:29,32,47,63,122,135,148,156`; `app/brief/[clientId]/page.tsx:23,75,86,99,107`) —
one level too shallow. Every lookup is `undefined`, so:
- the two client-side fabrication branches (`BriefModal.tsx:32-60`) **always** execute, injecting
  hardcoded content stamped `"CRM & D5 Memory" / 0.92` and `"TigerBroker News · LIVE" / 1.0`;
- the agenda always falls back to a literal 5-item string (`BriefModal.tsx:63`);
- the four real sections always render placeholder text (`BriefModal.tsx:122,135,148,156`).

Combined with ND-11 (404 on the brief routes), the brief view can never show real data, and when the
URLs are fixed it will show fabricated data instead. This is the highest user-visible impact defect
in the change set after the boot failure.
*Severity: High.*

**ND-32 — Generated brief identity is discarded, so approval can never address the generated brief.**
Backend mints a fresh `brief_id = str(uuid.uuid4())` per call (`brief_service.py:32`) and returns it
in the payload. The frontend reads only `response.data.brief` (`BriefModal.tsx:29`) and never stores
`brief.brief_id`; `approve` is then called with a literal:

```tsx
// BriefModal.tsx:77
await briefApi.approve('brief-123', 'Sarah Chen', editing ? editedAgenda : undefined);
```
```tsx
// app/brief/[clientId]/page.tsx:33
await briefApi.approve('brief-123', 'Sarah Chen', editing ? editedAgenda : undefined);
```

So even with both URLs repaired, the approval would target a non-existent ID with a hardcoded
approver name. This is the frontend half of the same defect as `briefs.py:49-54` accepting any
`brief_id` and any `approver` string without validation (§3.4 #13, §5.1).
*Severity: Medium.*

**ND-33 — Alembic discovers zero revisions: `upgrade head` is a silent no-op.**
`alembic.ini:33` sets `version_locations = %(here)s/versions`, and `%(here)s` is `backend/`, so this
resolves to `backend/versions` — a directory that **does not exist** (revisions live in
`backend/alembic/versions`). Verified by running the real config shape offline, with only
`alembic.ini:37` repaired, against the shipped `version_locations`:

```
$ alembic -c /tmp/probe_a.ini upgrade head --sql     # version_locations = backend/versions
BEGIN;

COMMIT;
exit=0        ← zero DDL, no error, no warning
```

Correcting `version_locations` to `backend/alembic/versions` and running the same command emits the
expected DDL (`CREATE TABLE client_memories …`, `CREATE INDEX ix_client_memories_client_id …`,
`UPDATE alembic_version SET version_num='002_add_client_memories' …`). So after ND-05 is fixed, the
migration command would appear to succeed while creating **nothing** — a third layer of false success
in the release path. *Severity: High (silent schema drift).*

**ND-34 — `alembic/script.py.mako` is absent, so `alembic revision` can never run.**
`find alembic` returns only `env.py`, `versions/001_*.py`, `versions/002_*.py`, `versions/README.md`.
The Mako template Alembic uses to render a new revision file is missing, so both
`alembic revision -m "…"` and `alembic revision --autogenerate` fail. Combined with ND-33, the
migration system cannot read existing revisions and cannot create new ones. (For completeness:
autogenerate would also propose `DROP TABLE client_memories`, because `alembic/env.py:15` imports only
`app.models.models` and `ClientMemory` is declared in `memory_service.py:16` — §2.7a/ND-08.)
*Severity: Medium.*

**ND-35 — The live schema was produced by neither the models nor the migrations.**
`information_schema.columns` on the running database:

```
clients      preferences        jsonb
clients      family_entities    jsonb
clients      created_at         timestamp with time zone
clients      updated_at         timestamp with time zone
holdings     as_of              timestamp with time zone
interactions interaction_date   timestamp with time zone
```

The models declare `JSON` (`models.py:24,26,98`) and naive `DateTime` (`models.py:28,29,47,48,60,69`),
which `create_all` renders as `json` and `timestamp without time zone`. The live columns are `jsonb`
and `timestamptz` — neither what the models emit nor what `001`/`002` emit
(`postgresql.JSON()`, `sa.DateTime()` at `002_add_client_memories.py:26,29,30`). Therefore the live
tables **predate the current model definitions** and were created by some earlier revision of the
code. Consequence for the clean-start analysis (§10.4): the only working database in existence cannot
be reproduced from any artifact in the repository. *Severity: Medium (evidence integrity).*

---

## 5. Areas This Change Set Did NOT Touch (Required Coverage for a Serious Audit)

These are not regressions; they are untouched risk surfaces that a "9/11 P0 fixed" report implies
were considered but were not.

### 5.1 Authentication & Authorization — absent entirely
There is no auth dependency on any of the 26 routes. `main.py:12-33` configures CORS
(`allow_origins` from settings, `allow_credentials=True`) but no authentication middleware.
Every route that mutates state — `POST /briefs/approve/{brief_id}` (`briefs.py:36`),
`POST /workflow/review/approve` (`workflow.py:62`), `POST /crm/sync` (`crm.py:16`),
`POST /market/mode` (`market.py:71`) — is unauthenticated.
The `approver` parameter on `briefs.py:39` is a free-text query string: **any caller can assert any
approver identity**. This defeats the entire Gate 1 / Gate 3 approval concept.
`rm_id` is a caller-supplied string with a default (`dashboard.py:20`), so any caller can request any
RM's book. There is no tenant boundary.

### 5.2 Input validation — partial and inconsistent
- Only three Pydantic models exist in the whole API: `ClientCreate` (`clients.py:17-25`, **unused —
  there is no create-client endpoint**), `ConsentRequest` (`workflow.py:15-18`),
  `ReviewApprovalRequest` (`workflow.py:20-23`).
- 20+ routes take bare `str` / `Dict` parameters with no validation: `briefs.py:16,39-40`;
  `workflow.py:27-29,110-111`; `crm.py:92`.
- Unvalidated UUIDs → 500 (ND-23).
- `market.py:18,32,46`: `symbols.split(",")` is passed straight to the mock; no allow-list, no
  length cap, no dedupe. `market.py:61` caps `limit` at 500 but `market.py:28` at 100 — inconsistent.
- `market.py:72`: `mode: str` is a bare scalar → query param, validated only inside
  `set_mode` (`market_service.py:171-177`).
- `clients.py:29-30`: `skip`/`limit` are bounded (`le=100`) — the one place pagination is done right.

### 5.3 Transaction boundaries — inverted
`database.py:37-46` commits after every request, including reads. Services that write
(`memory_service.py:57`, `audit_service.py:38`) also commit internally, then `get_db` commits again.
The `except` in `get_db` rolls back a transaction that may already have been committed by the
service. `sync_from_hubspot.py:78` commits once for the whole batch, so a single bad row discards
everything (ND-11.5).
There is no `SAVEPOINT` usage, no unit-of-work, and no explicit isolation level.

### 5.4 N+1 queries and unbounded reads
`ranking_service.py:41-45` loops over every client returned by
`select(Client).where(Client.external_id.like(f"{rm_id}%"))` (`:34-36`, **no limit**) and issues:
- `_calculate_opportunity` → `select(Holding)` per client (`:102-105`), once per market signal
  matched;
- `_calculate_risk` → `select(Holding)` per client (`:160-163`);
- `_calculate_retention` → `select(Interaction)` per client (`:186-191`).

That is ~3 queries per client, unbounded by client count. `dashboard.py:41-45` calls this on every
`/my-day` load. `dashboard.py:54-56` and `clients.py:35-37` also run unfiltered aggregates.
`crm.py:26-27` loads **all** clients into memory before looping outbound HTTP calls
(`crm.py:38-75`) with no concurrency limit.

### 5.5 Error taxonomy — a single `except Exception` pattern
Every route follows:
```python
except Exception as e:
    logger.error(f"...: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```
(`clients.py:40-42,60-62,81-83,132-134`; `briefs.py:32-34,56-58`; `market.py:21-23,35-37,53-55,
67-69`; `dashboard.py:86-88,110-112,130-132,152-154,184-186`; `workflow.py:38-40,58-60,87-89,
104-106,124-126`; `crm.py:85-87,138-140`).

Consequences:
- `str(e)` leaks internal detail (SQL, table names, driver messages) to the client — verified above:
  a bad UUID would return `"invalid input for query argument $1: 'not-a-uuid' (invalid UUID ...)"`.
- 404/409/422 conditions collapse into 500. `clients.py:56-57` raises 404 inside the `try`, and the
  bare `except Exception` at `:60` would re-wrap it — saved only because `HTTPException` is not
  caught by `except Exception` in the same way FastAPI expects (it is still an `Exception`, so
  `clients.py:60` **does** catch its own 404 and convert it to 500 — an actual bug at
  `clients.py:56-62`). `crm.py:136-137` gets this right (`except HTTPException: raise`); the
  clients endpoints do not.

### 5.6 Logging and PII
- `clients.py:39,78` echo full client records including `email`, `phone`, `aum`,
  `preferences`, `family_entities` — all PII — with no field filtering.
- `crm_service.py:45,63,82,99,134,186` log exception strings that can contain HubSpot request
  payloads (client name, email, AUM).
- `brief_service.py:81` logs `client_id`; `:77` logs brief IDs. Acceptable.
- `copilot_service.py:150,232` parse `response.choices[0].message.content` with `json.loads` and no
  length cap, and never log the prompt — good — but `:154,243` log the exception which may contain
  the full prompt on API error.
- No structured logging, no correlation ID propagation (the `correlation_id` at
  `copilot_service.py:38` is generated and returned but never threaded through logs).

### 5.7 Concurrency
- `market_service.set_mode` (`:171-177`) mutates `self.mode` on a process-global singleton with no
  lock; `get_real_time_quote` reads it at `:56`. Under `--reload`/multi-worker, mode differs per
  worker.
- `memory_service` and `audit_service` commit on a shared request-scoped session without
  concurrency guards.
- `workflow_orchestrator.transition_stage` mutates a caller-owned dict with no locking
  (`workflow_orchestrator.py:52-85`); two concurrent transitions can both read `current_stage` and
  both write.

### 5.8 SQL injection
No raw SQL in the app except `await db.execute(text("SELECT 1"))` at `health.py:28` — parameterless
and safe. All other queries use SQLAlchemy expression language. **This area is clean**, and worth
stating explicitly so it is not re-audited.

### 5.9 Unbounded queries / DoS surface
- `ranking_service.py:34-36`: `select(Client)` with a `LIKE` prefix and no `limit`.
- `crm.py:26-27`: `select(Client)` with no `limit`, then N outbound HTTPS calls serially.
- `dashboard.py:54-56`: `count(*)` + `sum(aum)` on the full table per request.
- `market.py:14`: `symbols` has no upper bound; each symbol triggers
  `detect_market_signal` → `get_real_time_quote` (`market_service.py:121`).
- `market.py:61`: `limit` capped at 500 but `get_historical_data` internally caps at 30
  (`market_service.py:154`) — the cap is decorative.

### 5.10 Duplicate implementations
- **CRM**: `crm_service.py` (used) vs `hubspot_service.py` (dead, wrong) — ND-12.
- **Brief generation**: `copilot_service.generate_brief` (`copilot_service.py:27-91`, real LLM,
  unused) vs `brief_service.generate_brief` (`brief_service.py:18-82`, template, used). Two
  implementations of the same requirement, the better one dead.
- **Workflow**: `copilot_service.orchestrate_workflow` (`:177-199`, returns `stages: []`) vs
  `workflow_orchestrator.create_workflow` (`:35-50`, stages populated, never called).
- **Shariah**: `shariah_service.py` stub returns `compliant: True` (`:35-37`) — no second
  implementation, but the "AAOIFI Standard" label at `:40` is attached to placeholder logic.

### 5.11 Config / environment
`config.py:56` `env_file = "../.env"` is CWD-relative. `config.py:9` makes `SECRET_KEY` **required**
with no default, so the app cannot import if the `.env` resolution fails. `backend/.env` exists but
is never read (the path resolves to the repo root `.env` when run from `backend/`). Two env files
with divergent credentials (real PAT at root, `demo_hub...` in `backend/`) create a
"works on my machine" hazard.
There is no config validation for `LLM_MODEL` (`config.py:40` defaults to `gpt-4-turbo-preview` while
`.env:23` sets a different model), `TIGER_*`, or `HUBSPOT_*`. `SECRET_KEY` is declared
(`config.py:9`) and **never used anywhere** — grep for `SECRET_KEY` returns only `config.py:9`.

### 5.12 Observability
Only `logging.basicConfig(level=INFO)` at `main.py:9`. No request logging middleware, no latency
metrics, no trace IDs, no health dashboards beyond the two `/health` endpoints (one fake, one dead),
and no alerting. `backend.log` is a raw uvicorn stream redirected by `start.sh:56`.

---

## 6. Appendix — Quoted Code

### A1. The boot failure
```python
# backend/app/services/market/market_service.py:13
from app.models.models import MarketTick, SourceKind
```
```python
# backend/app/main.py:5
from app.api.v1 import api_router
```
```python
# backend/app/api/v1/__init__.py:5
from app.api.v1.endpoints import clients, market, briefs, workflow, dashboard, crm
```
```python
# backend/app/api/v1/endpoints/market.py:6
from app.services.market.market_service import market_data_service
```
Runtime:
```
File "backend/app/services/market/market_service.py", line 13, in <module>
    from app.models.models import MarketTick, SourceKind
ImportError: cannot import name 'MarketTick' from 'app.models.models'
```
`app/models/models.py` now declares exactly five classes: `Client` (`:11`), `Holding` (`:36`),
`Interaction` (`:55`), `Brief` (`:75`), `AuditLog` (`:89`).

### A2. Fake health, accurate health, and the missing `include_router`
```python
# backend/app/main.py:44-54   ← LIVE
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "services": {"market_data": "active", "copilot": "active", "crm": "active"}
    }
```
```python
# backend/app/api/health.py:14-34   ← NEVER REGISTERED
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    health_status = {"status": "healthy", "database": "unknown", "services": {}}
    try:
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
        return health_status
```
```python
# backend/app/api/v1/__init__.py:9-15   ← six routers, health is not among them
api_router.include_router(clients.router,   prefix="/clients",   tags=["clients"])
api_router.include_router(market.router,    prefix="/market",    tags=["market"])
api_router.include_router(briefs.router,    prefix="/briefs",    tags=["briefs"])
api_router.include_router(workflow.router,  prefix="/workflow",  tags=["workflow"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(crm.router,       prefix="/crm",       tags=["crm"])
```

### A3. Mock market data stamped as a live feed
```python
# backend/app/services/market/market_service.py:38-56
async def get_real_time_quote(self, symbols: List[str]) -> List[Dict]:
    """
    Get real-time quotes for given symbols
    Returns mock data for now since Tiger SDK has dependency issues
    """
    ...
    for symbol in symbols:
        tick_data = {
            "symbol": symbol,
            "price": 50.0 + hash(symbol) % 100,
            "change": (hash(symbol) % 5) - 2.5,
            "change_percent": ((hash(symbol) % 5) - 2.5) / 50.0 * 100,
            "volume": 1000000 + hash(symbol) % 5000000,
            "source_id": "TigerBroker",
            "source_kind": SourceKind.LIVE_FEED if self.mode == "LIVE" else SourceKind.REPLAY,
```
```python
# backend/app/services/brief/brief_service.py:140-148
return {
    "content": content,
    "provenance": {
        "source": "TigerBroker Market Data · LIVE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": 1.0,
        "source_kind": "LIVE_FEED"
    }
}
```

### A4. "AI Generated" agenda with no AI
```python
# backend/app/services/brief/brief_service.py:203-237
async def _build_proposed_agenda(self, client, portfolio, changes, interactions) -> Dict:
    """Build proposed agenda based on context"""
    agenda_items = []
    if "movement" in changes["content"].lower():
        agenda_items.append("1. Review recent market movements and portfolio impact")
    if client.preferences and "last_rebalancing" in client.preferences:
        agenda_items.append("2. Discuss rebalancing approach")
    agenda_items.extend([
        f"{len(agenda_items) + 1}. Review overall portfolio performance",
        f"{len(agenda_items) + 2}. Q&A and next steps"
    ])
    return {
        "content": "\n".join(agenda_items),
        "provenance": {
            "source": "AI Generated",
            "confidence": 0.85,
            "source_kind": "ai_generated"
        }
    }
```
(No `openai`, no `AsyncOpenAI`, no `copilot_service` reference in this method or its imports at
`brief_service.py:1-13`.)

### A5. Provenance validator that cannot detect fabrication
```python
# backend/app/services/provenance/provenance_service.py:39-58
def validate_provenance(self, provenance: Dict) -> bool:
    """
    Validate that provenance is complete and accurate
    Returns False if provenance is fabricated or incomplete
    """
    required_fields = ["source", "source_kind", "timestamp", "confidence"]
    for field in required_fields:
        if field not in provenance:
            logger.warning(f"Missing required field in provenance: {field}")
            return False
    try:
        ProvenanceSourceKind(provenance["source_kind"])
    except ValueError:
        logger.warning(f"Invalid source_kind: {provenance['source_kind']}")
        return False
    return True
```

### A6. Approval gate that approves nothing
```python
# backend/app/api/v1/endpoints/briefs.py:36-58
@router.post("/approve/{brief_id}")
async def approve_brief(brief_id: str, approver: str, edited_agenda: str = None, db=Depends(get_db)) -> Dict:
    """
    Approve a brief (Gate 1)
    Records the approval in audit log
    """
    try:
        # TODO: Store approval in database with audit trail
        return {
            "status": "approved",
            "brief_id": brief_id,
            "approver": approver,
            "approved_at": "2024-11-07T12:00:00Z",
            "edited_agenda": edited_agenda
        }
```

### A7. Gate 3 that fabricates its audit trail
```python
# backend/app/api/v1/endpoints/workflow.py:62-89
@router.post("/review/approve")
async def approve_review(request: ReviewApprovalRequest, db=Depends(get_db)):
    """Approve all meeting outcomes (Gate 3)"""
    try:
        # TODO: Execute all approved actions:
        # - CRM sync
        # - D5 memory update
        # - Email draft
        # - Update workflow status
        return {
            "workflow_id": request.workflow_id,
            "gate": "gate3",
            "status": "approved",
            "approved_by": request.approved_by,
            "actions_executed": ["crm_sync", "d5_memory_update", "email_draft_saved"],
            "workflow_complete": True
        }
```

### A8. Reserved SQLAlchemy attribute
```python
# backend/app/services/memory/memory_service.py:16-29
class ClientMemory(Base):
    __tablename__ = "client_memories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    memory_type = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text)
    metadata = Column(JSON, default=dict)          # ← reserved name
    confidence = Column(String)                    # ← provenance uses float
    source = Column(String)
```
Runtime behaviour is version-dependent:

```
# SQLAlchemy 2.1.8  (backend/.venv, installed via uv sync — requirements.txt is NOT used)
memory_service.py:16: SAWarning: Attribute name 'metadata' should be left reserved
for the MetaData instance when using a Declarative class.
  class ClientMemory(Base):

# SQLAlchemy 2.0.25  (requirements.txt:8, installed by Dockerfile:13)
InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

So the Docker path cannot even import this module.
```

### A9. Corrupt Alembic config
```ini
# backend/alembic.ini:35-37
# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses os.pathsep.
version_path_separator = os  # Use os.pathsep. Default configuration used for new projects.
```
```
$ alembic history
ValueError: 'os  # Use os.pathsep. Default configuration used for new projects.'
is not a valid value for version_path_separator; expected 'space', 'newline', 'os', ':', ';'
```

### A10. Live schema (ground truth)
```
TABLES: ['clients', 'holdings', 'interactions']
  clients: 3 rows
  holdings: 2 rows
  interactions: 2 rows
  briefs: MISSING (UndefinedTableError)
  audit_logs: MISSING (UndefinedTableError)
  client_memories: MISSING (UndefinedTableError)
```
`holdings.source_kind` is `None` for both rows, although `seed_demo_data.py:121` sets
`source_kind=SourceKind.SEEDED` — evidence that the enum was removed after the last successful seed.

### A11. Transaction inversion
```python
# backend/app/core/database.py:37-46
async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()      # ← commits every request, including GETs
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### A12. The self-catching 404
```python
# backend/app/api/v1/endpoints/clients.py:50-62
try:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
except Exception as e:                      # ← catches the 404 above
    logger.error(f"Error fetching client: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

---

## 7. Reproduction Commands

All findings above are reproducible:

```bash
cd /Volumes/Orico/code/capco/wealth-workbench/backend

# Boot failure
./.venv/bin/python -c "import sys; sys.path.insert(0,'.'); import app.main"

# Per-module import matrix
./.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0,'.')
for m in ["app.models.models","app.services.memory.memory_service",
          "app.services.provenance.provenance_service",
          "app.services.workflow.workflow_orchestrator",
          "app.services.audit.audit_service","app.services.brief.brief_service",
          "app.services.market.market_service","app.services.copilot.copilot_service",
          "app.api.v1.endpoints.workflow","app.scripts.init_db",
          "app.scripts.seed_demo_data","app.scripts.sync_from_hubspot","app.main"]:
    try: __import__(m); print("OK  ", m)
    except Exception as e: print("FAIL", m, "->", type(e).__name__, e)
EOF

# Server state
curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://localhost:8000/health   # → 000
ps -p "$(cat ../backend.pid)" -o pid,stat,command                              # → no such process

# Alembic
./.venv/bin/alembic history                                                    # → ValueError
./.venv/bin/alembic current                                                    # → ValueError

# Live schema
./.venv/bin/python -c "
import asyncio, asyncpg
async def m():
    c = await asyncpg.connect('postgresql://rm_user:demo_password_123@localhost:5432/rm_workbench')
    print([r[0] for r in await c.fetch(\"select tablename from pg_tables where schemaname='public' order by 1\")])
asyncio.run(m())"

# Zero write paths in the API
grep -rn "db.add\|session.add" app/api          # → no matches
# Dead services
grep -rn "audit_service\|memory_service\|provenance_service\|workflow_orchestrator" app --include=*.py
# Never instantiated Brief model
grep -rn "Brief(" app --include=*.py            # → models.py:75 only
```

---

## 8. Bottom Line

`PROGRESS.md` reports **9 of 11 P0 gaps addressed (82%)**. Measured against the running system:

- **Fully delivered: 0 of 9.**
- **Partially delivered: 4** (G-04 timezone logic; G-01 portfolio + interactions reads; G-11 outbound
  HubSpot call; G-28 `.gitignore` only).
- **Not delivered: 4** (G-25 `/health` unregistered; G-22 orchestrator unused; G-13 memory table
  absent; G-23 validator cannot detect fabrication).
- **Regressed: 1** (G-26), with two new integrity regressions (G-01's false `LIVE_FEED` /
  `AI Generated` stamps), one response-envelope regression that makes the client-side fabrication
  unconditional (ND-31), and three new false-success endpoints (`/briefs/approve`,
  `/workflow/review/approve`, `/crm/status`).
- **System availability: down.** 0 of 26 endpoints respond because the process cannot be imported;
  17 of the 24 `/api/v1` routes would remain dead even after the app-level import is repaired.

The change set's characteristic failure mode is consistent and diagnosable: **correct-looking code
written into modules that nothing calls, next to live code paths left untouched.** The accurate
`/health`, the `WorkflowOrchestrator`, the `AuditService`, the `ProvenanceService`, the
`MemoryService`, and the real `copilot_service.generate_brief` are all functionally orphaned, while
`main.py`'s fake health, `workflow.py`'s fake approvals, and `dashboard.py`'s hardcoded KPIs remain
in production position. Remediation should start with the four import breaks (ND-01…ND-04), then
wire-or-delete the five orphan services, then re-run this audit.

---

## 9. Call-Site Coverage and Orphan Inventory (Addendum)

Method: enumerate every backend route (§3) and every frontend API wrapper invocation, then compute
the intersection.

### 9.1 Every frontend call site (exhaustive)

```
$ grep -rnoE "(dashboardApi|marketApi|clientApi|briefApi|workflowApi)\.[a-zA-Z]+" frontend/app frontend/components
components/BriefModal.tsx:28:briefApi.generate
components/BriefModal.tsx:77:briefApi.approve
app/page.tsx:33:dashboardApi.getMyDay
app/page.tsx:34:dashboardApi.getAllocation
app/page.tsx:35:dashboardApi.getPerformanceTrend
app/brief/[clientId]/page.tsx:21:briefApi.generate
app/brief/[clientId]/page.tsx:33:briefApi.approve
```

Seven invocations, five distinct backend operations.

### 9.2 Backend routes with a frontend caller

| Backend route | Frontend caller | Reachable today? | Works if reached? |
|---|---|---|---|
| `GET /api/v1/dashboard/my-day` | `app/page.tsx:33` | ✗ (`dashboard.py:10` ImportError) | Partly — real AUM/count, hardcoded meetings/actions (§3.6 #19) |
| `GET /api/v1/dashboard/allocation` | `app/page.tsx:34` | ✗ | No — fully hardcoded (§3.6 #22) |
| `GET /api/v1/dashboard/performance-trend` | `app/page.tsx:35` | ✗ | No — `# Mock YTD performance data` (`dashboard.py:165`) |
| `POST /api/v1/briefs/generate/{client_id}` | `BriefModal.tsx:28`, `brief/[clientId]/page.tsx:21` | ✗ | **No — frontend calls `/briefs/generate` with no path param → 404** (§2.8) |
| `POST /api/v1/briefs/approve/{brief_id}` | `BriefModal.tsx:77`, `brief/[clientId]/page.tsx:33` | ✗ | **No — 404, and the approved ID is the literal `'brief-123'`** |

So **0 of the 5 routes the UI actually depends on is reachable**, and 0 of them would return correct
data even if the import chain were repaired.

### 9.3 Orphan backend routes — no frontend caller (19 / 17 / 21 of 24 under `/api/v1`)

Two conventions are in play and it is worth stating both to reconcile with the frontend audit — plus
a third that is the strictest:

- **19 of 24** `/api/v1` routes have **no caller at all** (5 are invoked: `/dashboard/my-day`,
  `/dashboard/allocation`, `/dashboard/performance-trend`, `/briefs/generate/{client_id}`,
  `/briefs/approve/{brief_id}`).
- **17 of 24** have **no imported/invoked caller** — `workflowApi.start` and
  `workflowApi.extractInsights` exist as wrappers in `lib/api.ts:74-87` but the entire `workflowApi`
  object is **never imported by any component**, so `/workflow/start` and `/workflow/extract-insights`
  are not actually called by anything.
- **21 of 24** have **no *valid* caller** — the strongest and most useful figure. The two brief routes
  are "called" only at a URL that does not exist (§2.8), so no route is ever successfully addressed.

Which number to quote depends on the question: 19 for "is there a wrapper that targets it", 17 for
"does any shipped component invoke it", 21 for "is any route ever successfully reached".

`GET /` · `GET /health` · all four `GET /api/v1/clients/*` · all five `/api/v1/market/*` ·
`/api/v1/workflow/start` · `/workflow/consent` · `/workflow/review/approve` ·
`GET /workflow/{id}` · `/workflow/extract-insights` · `GET /dashboard/kpis` ·
`GET /dashboard/book-stats` · all three `/api/v1/crm/*`.

Notable implications:
- `GET /api/v1/dashboard/kpis` and `GET /dashboard/book-stats` are implemented, hardcoded, and
  **never called** — dead fake data.
- The entire CRM surface (`crm.py:16-162`, 147 lines) has no UI consumer.
- The entire workflow surface has no UI consumer, so the fabricated Gate 2 / Gate 3 responses
  (§3.5 #15, #16) are currently unreachable from the browser — but they are live unauthenticated
  HTTP endpoints on `:8000` and would report success to any direct caller.
- All four `clients` endpoints are orphaned; the UI reads client data only through
  `/dashboard/my-day`.

### 9.4 Orphan frontend wrappers (dead client code)

`frontend/lib/api.ts` exposes 21 methods (dashboard 5, market 4, client 4, brief 3, workflow 5).
Used: 5. **Unused: 16.**

| Wrapper | Line | Status |
|---|---|---|
| `dashboardApi.getKPIs` | 17-18 | never called |
| `dashboardApi.getBookStats` | 20-21 | never called |
| `marketApi.getQuotes` / `getNews` / `getSignals` / `getHistorical` | 32-42 | **all four never called**; `marketApi` is imported at `app/page.tsx:4` and never used → unused import |
| `clientApi.getClients` / `getClient` / `getPortfolio` / `getShariahReport` | 47-57 | **`clientApi` is never imported anywhere** — the entire object is dead |
| `workflowApi.start` / `recordConsent` / `approveReview` / `getWorkflow` / `extractInsights` | 74-87 | **`workflowApi` is never imported anywhere** — the entire object is dead |
| `briefApi.getBrief` | 68-69 | never called, and no backend route exists |

### 9.5 Orphan backend service methods (never reached from any endpoint)

| Module | Public methods | Reached from HTTP? |
|---|---|---|
| `brief_service` | `generate_brief` | **Yes** — `briefs.py:28` (only genuinely wired new service) |
| `audit_service` | `log_action` | No — 0 callers |
| `memory_service` | `store_memory`, `get_memories` | No — 0 callers |
| `provenance_service` | `create_provenance`, `validate_provenance` | No — 0 callers |
| `workflow_orchestrator` | `create_workflow`, `transition_stage` | No — 0 callers |
| `copilot_service` | `generate_brief` | No — dead duplicate of `brief_service` |
| `copilot_service` | `extract_meeting_insights` | Yes (via `workflow.py:119`) — but the route is dead at import |
| `copilot_service` | `orchestrate_workflow` | Yes (via `workflow.py:34`) — but the route is dead at import |
| `crm_service` | `fetch_contacts_from_hubspot` | No — only `sync_from_hubspot.py:27` (CLI, runs) |
| `crm_service` | `create_contact`, `update_contact`, `get_contact`, `sync_client_to_hubspot` | Yes via `crm.py` (which boots) |
| `hubspot_service.CRMService` | `sync_client`, `execute_sync` | No — whole module unused (ND-12) |
| `shariah_service` | `screen_instrument`, `calculate_zakat`, `generate_shariah_report` | Yes via `clients.py:101-128` |

Orphan rate among the five new service modules: **4 of 5 modules, 6 of 10 methods.**

### 9.6 Cross-cutting defect found while tracing call sites (credit to frontend-auditor's remit)

`frontend/components/BriefModal.tsx:32-60` **fabricates provenance in the browser.** If the backend
brief lacks `recent_interactions.content`, the component injects a hardcoded narrative and stamps it:

```tsx
// BriefModal.tsx:32-45
if (!briefData.recent_interactions?.content) {
  briefData.recent_interactions = {
    content: `Last meeting (15 days ago): Client expressed preference for gradual rebalancing...`,
    provenance: {
      source: 'CRM & D5 Memory',        // :40
      timestamp: new Date().toISOString(),
      confidence: 0.92                  // :42
    }
  };
}
// BriefModal.tsx:47-60
if (!briefData.market_news?.content) {
  briefData.market_news = {
    content: `HSBC Holdings (0005.HK) +2.3%: Strong Q3 earnings announced today...`,
    provenance: {
      source: 'TigerBroker News · LIVE', // :55
      timestamp: new Date().toISOString(),
      confidence: 1.0                    // :57
    }
  };
}
```

The `confidence: 1.0` / `"TigerBroker News · LIVE"` stamp is authored by client-side TypeScript, not
by any data source. Combined with `brief_service.py:142-147,196-199` (§2.4), provenance is
fabricated at **two independent layers**.

**These branches are not hypothetical — they fire on every render.** Because the backend nests
sections under `sections` (`brief_service.py:62-75`) while the client reads them flat
(`BriefModal.tsx:29` → `response.data.brief.recent_interactions`), both conditions are always true
(ND-31). The fabricated `LIVE` / `1.0` content is therefore the *only* content the brief modal can
display, regardless of what the backend returns.

Also `BriefModal.tsx:77` hardcodes both the approved brief ID and the approver:
`briefApi.approve('brief-123', 'Sarah Chen', ...)`.

---

## 10. Clean-Start Path (Addendum)

Question: can a fresh clone be brought up? **No.** There are four independent points of failure, and
the documented entry point hangs rather than fails.

### 10.1 `docker-compose.yml` does not define the backend

`docker-compose.yml:2` and `:19` declare only `postgres` and `redis`. There is no `backend` or
`frontend` service. Yet `setup.sh:43` runs `docker-compose up -d` and `setup.sh:58` claims
*"this includes table creation and demo data seeding"* — nothing in the compose file creates tables
or seeds data.

### 10.2 `setup.sh` hangs forever on a fresh machine

```bash
# setup.sh:58-66
echo "⏳ Waiting for backend to initialize (this includes table creation and demo data seeding)..."
sleep 15
echo "🔍 Checking backend health..."
until curl -f http://localhost:8000/health &> /dev/null; do
    echo "   Waiting for backend API..."
    sleep 3
done
```

Compose starts only Postgres and Redis; nothing starts uvicorn; the loop at `:63` is unbounded.
`setup.sh` never terminates. (It also `set -e`s, so any earlier `docker-compose` failure aborts
silently after the password check.)

### 10.3 `start.sh` starts a backend that cannot import

```bash
# start.sh:54-58
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
```

`uvicorn` exits immediately on the `MarketTick` `ImportError` (§A1). `$!` captures the `uv run`
wrapper PID, not uvicorn's, so `stop.sh` / `backend.pid` management is unreliable — corroborated by
the dead PID 14829 in the current workspace. `start.sh` never runs `init_db.py` or
`seed_demo_data.py`, so even with imports fixed there is no schema and no data.

### 10.4 Neither schema path works

| Path | Invocation | Status |
|---|---|---|
| `init_db.py` | `python -m app.scripts.init_db` | `ImportError: MarketTick` (ND-04) |
| `seed_demo_data.py` | `python -m app.scripts.seed_demo_data` | `ImportError: SourceKind` (ND-03) |
| Alembic | `alembic upgrade head` | Three layered failures: `ValueError` from `alembic.ini:37` (ND-05); if fixed, `version_locations` points at a nonexistent `backend/versions` so `upgrade head --sql` emits `BEGIN; COMMIT;` with zero DDL (ND-33); and the chain has no baseline for `clients` (ND-07) |
| `alembic revision` | any revision command | `alembic/script.py.mako` is missing → cannot render a new revision (ND-34) |
| `docker-entrypoint-initdb.d` | `backend/init.sql` | Only `CREATE EXTENSION`; explicitly *"Table creation happens via SQLAlchemy in the backend"* (`init.sql:8-9`) — which is the broken path |
| Existing database | the running `rm_workbench` | Reproducible from **no** artifact: its columns are `jsonb`/`timestamptz` while every definition in the repo emits `json`/`timestamp` (ND-35) |

### 10.5 Environment and configuration defects on the clean path

- `setup.sh:11-19` copies `.env.example` → `.env` and then **exits 1**; the operator must hand-edit.
  `.env.example:42` sets `SHARIAH_TOOLS_PATH=/Volumes/Orico/code/capco/islamic-ai/shariah` — an
  absolute path on the original author's machine, committed into the template.
- `.env.example:10` documents `TIGER_PRIVATE_KEY` as `your_tiger_private_key_path` (a path), but
  `config.py:26` types it as `str` and `market_service.py:22` assigns it as a secret. No code ever
  reads a key file.
- `config.py:56` `env_file = "../.env"` is CWD-relative; `backend/.env` is never loaded. Running
  uvicorn from the repo root produces `ValidationError: SECRET_KEY Field required` because
  `config.py:9` has no default.
- `config.py:9` declares `SECRET_KEY` and nothing in the codebase reads it (`grep -rn SECRET_KEY`
  → `config.py:9` only). JWT/bcrypt are in `pyproject.toml:17-18` and never imported — auth was
  planned and abandoned, but the settings imply otherwise.
- `.env` / `HUBSPOT_CREDENTIALS.md` are gitignored (`.gitignore:12-14,33`) but present; the
  directory is not a git repo, so nothing has been committed and nothing is protected (ND-19).

### 10.6 Verdict on clean start

| Step | Outcome |
|---|---|
| `./setup.sh` | **Hangs indefinitely** at `setup.sh:63` |
| `docker-compose up -d` | Starts DB + cache only |
| `./start.sh` | Backend dies on import; `backend.pid` records the wrong process |
| Schema creation | All three paths broken |
| Demo data | Broken import; current DB shows a partial, pre-change seed (2 holdings, `source_kind NULL`) |
| `curl /health` | `000` |

A new contributor following the README cannot reach a working system.

---

## 11. Dependencies (Addendum)

Scope: declared vs installed, real incompatibilities only. No installs were run.

### 11.1 Three conflicting sources of truth

| Source | Role | State |
|---|---|---|
| `backend/uv.lock` (251,927 bytes) | what `start.sh:49` (`uv sync`) actually installs | matches the venv exactly (spot-checked fastapi 0.162.0, openai 3.46.0, sqlalchemy 2.1.8, pydantic 2.14.3, pytest 9.2.0) |
| `backend/pyproject.toml:6-27` | resolver input | every pin is `>=` with **no upper bound** → the cause of §11.2 drift |
| `backend/requirements.txt` | vestigial | **stale by 17 packages and declares one package that is not in the lock at all** |

`requirements.txt` is the file a new contributor is most likely to `pip install -r`, and it would
produce an environment that has never been tested.

### 11.2 `requirements.txt` vs installed (measured with `importlib.metadata`)

Command used (not `pip list`, which returns empty for this uv-managed venv):

```
backend/.venv/bin/python - <<'EOF'
from importlib.metadata import version
...  # table below
EOF
```

| Package | `requirements.txt` | Installed | Status |
|---|---|---|---|
| fastapi | 0.109.0 | **0.162.0** | DRIFT |
| uvicorn | 0.27.0 | **0.54.0** | DRIFT |
| python-dotenv | 1.0.0 | 1.2.4 | DRIFT |
| pydantic | 2.5.3 | **2.14.3** | DRIFT |
| pydantic-settings | 2.1.0 | 2.16.2 | DRIFT |
| sqlalchemy | 2.0.25 | **2.1.8** | DRIFT (minor bump) |
| alembic | 1.13.1 | 1.20.1 | DRIFT |
| **psycopg2-binary** | 2.9.9 | **not installed** | **MISSING** |
| asyncpg | 0.29.0 | 0.32.0 | DRIFT |
| pgvector | 0.2.4 | 0.5.1 | DRIFT |
| hubspot-api-client | 13.0.0 | 13.0.0 | match |
| openai | 1.10.0 | **3.46.0** | DRIFT (**two major versions**) |
| httpx | 0.26.0 | 0.28.1 | DRIFT |
| python-multipart | 0.0.6 | 0.0.33 | DRIFT |
| python-jose | 3.3.0 | 3.5.0 | DRIFT |
| passlib | 1.7.4 | 1.7.4 | match |
| redis | 5.0.1 | **8.1.0** | DRIFT (**three majors**) |
| requests | 2.31.0 | 2.34.2 | DRIFT |
| pytest | 7.4.4 | **9.2.0** | DRIFT (two majors) |
| pytest-asyncio | 0.23.3 | 1.4.1.post1 | DRIFT |

**Totals: 2 match, 17 drift, 1 missing.** `psycopg2-binary` is absent from `uv.lock` as well
(verified: both `psycopg2-binary` and `psycopg` return `ABSENT from uv.lock`), so it was never intended
to be installed — `requirements.txt:10` is simply wrong.

### 11.3 Real incompatibilities (not stylistic)

**DEP-01 (High, `uv` path only) — no synchronous PostgreSQL driver, so `alembic/env.py` cannot connect.**
`alembic/env.py:44-48` uses `engine_from_config(...)` with `settings.DATABASE_URL` =
`postgresql://rm_user:…` (`alembic/env.py:21`), i.e. the **sync** dialect. Verified on the venv that
`start.sh:49` produces:

```
>>> create_engine('postgresql://rm_user:x@localhost:5432/rm_workbench').connect()
ModuleNotFoundError: No module named 'psycopg'
```

SQLAlchemy 2.1.8 maps `postgresql://` to **psycopg (v3)**, not psycopg2 — so installing
`requirements.txt:10` (`psycopg2-binary`) would **not** satisfy this dialect. Alembic online mode
therefore has two independent blockers on this path: the `alembic.ini:37` `ValueError` (ND-05) and a
missing driver. The app itself is unaffected because `database.py:10-12` rewrites the URL to
`postgresql+asyncpg://` for the async engine.

**The two supported start paths fail for different reasons — this is the key result of §11.** Neither
works, and fixing one does not fix the other:

| | `start.sh:49` → `uv sync` (uv.lock) | `Dockerfile:13` → `pip install -r requirements.txt` |
|---|---|---|
| Python | 3.13.13 (`backend/.venv`) | 3.11 (`Dockerfile:1`) |
| SQLAlchemy | **2.1.8** | **2.0.25** (pinned, `requirements.txt:8`) |
| `ClientMemory.metadata` | warning only, class created | **`InvalidRequestError` on import** (§2.7b) |
| Sync PG driver | **absent** (`psycopg` missing) → alembic cannot connect | `psycopg2-binary` installed, and 2.0.25 still accepts psycopg2 → driver OK |
| `passlib`+`bcrypt` | broken (bcrypt 5.0.0) | `passlib[bcrypt]` resolves bcrypt unpinned → same class of break |
| Net | app cannot import (ND-01), alembic cannot connect (DEP-01) | app cannot import (ND-01), and even with that fixed `memory_service` cannot import |

So `requirements.txt` is not merely stale — it describes a genuinely different runtime with a
different failure mode. `Dockerfile:13` consumes it, `uv.lock` does not, and nothing reconciles them.

**DEP-02 (Medium, latent) — `passlib` 1.7.4 is incompatible with the installed `bcrypt` 5.0.0.**
`requirements.txt:26` / `pyproject.toml:18` declare `passlib[bcrypt]`; the resolver installed
`bcrypt==5.0.0`. Verified:

```
>>> CryptContext(schemes=['bcrypt']).hash('x')
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes, ...
```

`passlib/handlers/bcrypt.py:620` reads `_bcrypt.__about__.__version__`, removed in bcrypt ≥4.1. The
failure surfaces as a *misleading* "72 bytes" error. Nothing imports passlib today (§11.5), so this is
latent — but the moment authentication is wired up (the stated intent of `SECRET_KEY` at
`config.py:9` and `python-jose`/`passlib` in `pyproject.toml:17-18`), hashing fails 100% of the time.

**DEP-03 (Low) — `pytest-asyncio` 1.4.1 defaults to strict mode with no config.**
Verified warning on every invocation:
`PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset`.
There is no `[tool.pytest.ini_options]` and no `pytest.ini` (§12.1), so async tests would silently
skip or error rather than run. Any test suite added must ship config alongside it.

### 11.4 Compatibility checks that PASS (recorded so they are not re-investigated)

| Check | Result |
|---|---|
| Legacy ORM API (`session.query(...)`) | **Clean.** `grep -rn "session.query(\|\.query(" app` → no matches. All access is `select()` (SQLAlchemy 2.0 style), which is correct for 2.1.8 |
| `declarative_base()` under SQLAlchemy 2.1.8 | Works (`database.py:2,34` imports and instantiates successfully) |
| pydantic-settings legacy `class Config` + `env_file` (`config.py:55-56`) under pydantic 2.14.3 / pydantic-settings 2.16.2 | **Works.** Verified: `from app.core.config import settings` succeeds and resolves `DATABASE_URL` to `localhost:5432/rm_workbench` |
| `openai` 3.46.0 vs `AsyncOpenAI` + `chat.completions.create` (`copilot_service.py:20-23,140-148,222-230`) | **Works.** Verified `openai.AsyncOpenAI` exists and the instance exposes `chat.completions.create`. No API-shape break, despite the 1.x→3.x jump |
| `hubspot-api-client` 13.0.0 | Matches declaration; `search_api.do_search` / `basic_api.create` / `update` / `get_by_id` resolve |
| `CREATE EXTENSION vector` (`init.sql:5`) vs `pgvector` 0.5.1 | Package installed; the extension itself is only created if `init.sql` runs at container init |

### 11.5 Declared but never imported under `app/`

Complete third-party import surface (`grep -rhoE "^(from|import) …" app`):
`fastapi`, `hubspot`, `openai`, `pydantic`, `pydantic_settings`, `requests`, `sqlalchemy`
(+ stdlib: `asyncio, base64, datetime, enum, hashlib, hmac, json, logging, os, random, sys, time,
typing, uuid`).

| Declared | Imported anywhere in `app/`? | Note |
|---|---|---|
| `redis` (`pyproject.toml:19`) | **No** | `REDIS_URL` at `config.py:50` is also unused. Redis container runs for nothing |
| `pgvector` (`pyproject.toml:20`) | **No** | only used via SQL `CREATE EXTENSION` (`init.sql:5`) |
| `python-jose[cryptography]` (`pyproject.toml:17`) | **No** | auth planned, abandoned (§5.11) |
| `passlib[bcrypt]` (`pyproject.toml:18`) | **No** | same; also broken (DEP-02) |
| `httpx` (`pyproject.toml:15`) | **No** | `market_service.py:7` imports `requests` instead, and uses neither |
| `python-multipart` (`pyproject.toml:16`) | **No** | only needed for `Form()`/`File()`, which no route uses |
| `psycopg2-binary` (`requirements.txt:10`) | No | not installed, not in lock (DEP-01) |
| `greenlet` (`pyproject.toml:26`) | indirectly | required by SQLAlchemy async; correct to keep |
| `python-dotenv` (`pyproject.toml:9`) | indirectly | consumed by pydantic-settings |

**Imported but not declared: none.** A clean install of `pyproject.toml` provides every import the app
needs.

### 11.6 Floating pins

`pyproject.toml:7-27` uses `>=` exclusively, with **no upper bounds** — including on packages that
have had breaking majors since the declared floor: `openai>=1.10.0` (installed 3.46.0),
`redis>=5.0.1` (installed 8.1.0), `pytest>=7.4.4` (installed 9.2.0). This is precisely how the
17-package drift in §11.2 occurred. `uv.lock` is the only thing preventing a rebuild from resolving a
different set, and `requirements.txt` bypasses it entirely.

Additionally: `backend/venv/` is a **second virtualenv on Python 3.14.7**, while
`pyproject.toml:5` declares `requires-python = ">=3.11,<3.14"` — so that environment violates the
project's own interpreter constraint. It contains the same package versions as `backend/.venv/`
(3.13.13), which is the one `start.sh:56` actually uses via `uv run`. Two venvs in one backend
directory is a "which interpreter am I on" hazard; both are gitignored (`.gitignore:7,9`) yet both
persist locally.

---

## 12. Tests and CI (Addendum)

### 12.1 Current state: zero tests, zero CI

Evidence commands and output:

```
# test files, excluding installed packages
$ cd /Volumes/Orico/code/capco/wealth-workbench
$ find . \( -name "test_*.py" -o -name "*_test.py" \) \
       -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/node_modules/*"
(no output)

# pytest's own view
$ cd backend && ./.venv/bin/python -m pytest --collect-only -q
no tests collected in 0.01s
```

Config/CI artifacts searched for **one by one at the repository root** and **all absent**:
`.github/`, `.gitlab-ci.yml`, `.circleci/`, `Jenkinsfile`, `azure-pipelines.yml`, `.travis.yml`,
`bitbucket-pipelines.yml`, `.drone.yml`, `Makefile`, `tox.ini`, `noxfile.py`, `pytest.ini`,
`conftest.py` (also `docker-compose.test.yml`). `backend/pyproject.toml` has `[project]`,
`[build-system]`, `[tool.hatch.build.targets.wheel]` and `[tool.uv]` only — **no
`[tool.pytest.ini_options]`**.

This is independently corroborated by `frontend-auditor`, who checked the same list from the frontend
side and reached the same result. The consequence for the recommendations in §12.3 is that every gate
proposed there is a **new** control, not the restoration of a broken one — "CI would have caught this"
is only true after CI exists.

Frontend (`frontend/package.json:5-10`) has scripts `dev`, `build`, `start`, `lint` — **no `test`**.
No `jest`, `vitest`, `playwright` or `cypress` in `node_modules/.bin`.

So: **there is no automated gate of any kind.** This is why a change set that cannot import was
committed with a document claiming 9/11 P0 items fixed.

Relevant pre-existing evidence for the "no CI" claim: `PROGRESS.md:34-39` declares G-28 "release
hygiene" complete while shipping a corrupt `alembic.ini:37` — a single `alembic history` smoke step in
CI would have caught it on the first run.

### 12.2 Minimum test set that would have caught this change set

Five tests, one assertion each. Paths are suggestions; the assertion is the requirement.

**T1 — the app boots.** `backend/tests/test_boot.py`
```python
def test_app_imports_and_routes_exist():
    from app.main import app
    paths = {r.path for r in app.routes}
    assert {"/", "/health", "/api/v1/briefs/generate/{client_id}"} <= paths
```
Catches: ND-01 (any deleted-model import at router aggregation). Would have failed on commit.
Note: do not assert an exact route count — FastAPI adds `/openapi.json`, `/docs`,
`/docs/oauth2-redirect`, `/redoc`, so the number is framework-version dependent.

**T2 — every router imports cleanly.** `backend/tests/test_router_imports.py`
```python
@pytest.mark.parametrize("mod", [
    "app.api.v1.endpoints.briefs",  "app.api.v1.endpoints.clients",
    "app.api.v1.endpoints.crm",     "app.api.v1.endpoints.dashboard",
    "app.api.v1.endpoints.market",  "app.api.v1.endpoints.workflow",
])
def test_router_module_imports(mod):
    importlib.import_module(mod)          # no assertion needed; import IS the assertion
```
Catches: ND-01, ND-02 (`copilot_service.py:11` → `WorkflowStage`/`SourceKind`) as *separate*
failures, so a fix for one does not mask the other. Also catches ND-03/ND-04 if the scripts are
added to the parametrisation.

**T3 — ranking does not swallow failure.** `backend/tests/test_ranking.py`
```python
async def test_rank_returns_clients_for_naive_interaction(db):
    seed_client(db, external_id="RM001-C001")
    seed_interaction(db, when=datetime(2024, 1, 1))       # naive, deliberately
    assert len(await ranking_service.rank_clients(db, "RM001")) == 1
```
Catches: G-04's residual `except Exception: return []` (`ranking_service.py:81-83`) in the *opposite*
direction — if the timezone handling regresses to a `TypeError`, the swallow returns `[]` and this
assertion fails with a clear message instead of the dashboard silently showing no clients. This is the
test that converts the silent-swallow into a visible failure.

**T4 — the brief envelope matches the client's accessor path.** `backend/tests/test_brief_contract.py`
```python
async def test_brief_sections_are_nested_under_sections(db, client_id):
    brief = (await brief_service.generate_brief(client_id, db))
    assert set(brief) >= {"brief_id", "sections"}
    assert set(brief["sections"]) == {
        "portfolio_overview", "material_changes", "recent_interactions",
        "market_news", "proposed_agenda"}
    assert "portfolio_overview" not in brief     # pins the non-flat contract
```
Catches: ND-31 (envelope mismatch) — and, critically, it fails if someone "fixes" the backend by
flattening the payload without also updating `frontend/lib/api.ts` and `BriefModal.tsx:32,47,63,122`.
Best paired with a frontend assertion on the same path; the backend half is the cheaper gate.

**T5 — provenance guard: no LIVE_FEED stamp while the market source is mock.** `backend/tests/test_provenance_guard.py`
```python
async def test_no_live_feed_stamp_when_market_is_mock(db, client_id, monkeypatch):
    monkeypatch.setattr(market_data_service, "is_mock", True)
    brief = await brief_service.generate_brief(client_id, db)
    assert not any(s["provenance"]["source_kind"] == "LIVE_FEED"
                   for s in brief["sections"].values())
```
Catches: the whole class of fabricated-provenance defects — `brief_service.py:142-147` (mock market),
`:196-199` (hardcoded news), and it would also catch `:231-236` if extended to `"ai_generated"`.
**Prerequisite:** `market_data_service` currently has no `is_mock` flag; `get_real_time_quote`'s own
docstring says *"Returns mock data for now"* (`market_service.py:40-42`), so the flag is a one-line
addition on the singleton. Without the flag this test cannot be written, which is itself the point:
the codebase has no way to state "this data is fake".

**Recommended extras (target specific NDs, cheap to add):**
- **T6** — dashboard self-consistency: `assert (await get_my_day(db))["kpis"]["total_aum"] == (await get_kpis(db))["total_aum"]`. Catches ND-21/§3.6 #20 (real 198.3M vs hardcoded 428.5e6 for the same book).
- **T7** — `GET /crm/status` is not constant: monkeypatch `crm_service.find_contact_by_email` to raise, then `assert resp["status"] == "error"`. Catches ND-16 (the new false-success endpoint).
- **T8** — approval rejects unknown IDs: `POST /api/v1/briefs/approve/does-not-exist` → `assert response.status_code == 404`. Catches `briefs.py:48-54` returning `"approved"` for any ID.

### 12.3 What a minimal CI gate should be

There is no CI today. The smallest gate that would have blocked this change set, in cost order:

| # | Gate | Command | Catches | Cost |
|---|---|---|---|---|
| 1 | Boot import | `cd backend && python -c "import app.main"` | ND-01, ND-02 | <1 s |
| 2 | Router imports | `python -m pytest tests/test_router_imports.py -q` | ND-01…ND-04 | <1 s |
| 3 | Alembic parses + generates offline SQL | `cd backend && alembic upgrade head --sql` | ND-05, ND-07 | ~1 s, no DB needed |
| 4 | Python tests | `python -m pytest -q` | T1…T5 | needs a Postgres service |
| 5 | TypeScript | `cd frontend && npx tsc --noEmit` | ND-31/ND-32 class of contract drift | ~10 s |
| 6 | Lint | `cd frontend && npm run lint` | unused imports (e.g. `marketApi` at `app/page.tsx:4`) | ~15 s |

Gates 1-3 and 5 need no database and no secrets; they run in a few seconds and each one fails on the
current tree. Gate 5 currently fails with exactly one real error:

```
$ cd frontend && ./node_modules/.bin/tsc --noEmit
components/FamilyGraphModal.tsx(125,9): error TS2322: Type '{ … value: string; … }[]'
  is not assignable to type 'SeriesOption$1 | SeriesOption$1[] | undefined'
  ...
  Types of property 'value' are incompatible. Type 'string' is not assignable to type 'number'.
exit=1   (1 error, 1 file)
```

That is a genuine type error in the ECharts graph series (`value: string` where `number` is required),
not a config artefact — so `tsc --noEmit` is a viable gate, but only after the defect is fixed. **It is
not a one-line fix, and correcting the type alone would silently break the UI.** The strings are
entitlement *labels*, not weights, and they are consumed in two places:

- `FamilyGraphModal.tsx:161` `edgeLabel.formatter: (params) => params.data.value` — renders the label on the edge
- `FamilyGraphModal.tsx:113` edge tooltip `` `Entitlement: ${params.data.value}` `` — renders it in the tooltip

while the link data supplies them as strings (`FamilyGraphModal.tsx:81-88`:
`value: 'full'`, `'education-only'`, `'restricted'`). Node entries use `value` numerically for AUM
(`:110`), which is why the two uses collide in the type system. Casting the link `value` to `number`
(or `as any`) satisfies `tsc` and blanks both labels. The correct minimal fix is to add a distinct
`entitlement` field to each link and repoint both consumers at `params.data.entitlement`, then either
make `value` numeric or omit it. Acceptance for this gate item must therefore be "`tsc` green **and**
entitlement labels still render", not "`tsc` green" alone.

Note also that this gate would be an **addition, not a restoration**: there is no CI in this repository
on either side (§12.1), so `tsc --noEmit` has never run here. Recording that distinction matters,
because "CI will catch it" is only true once CI exists. This is a frontend file and the finding is the
frontend auditor's (F2 / Blocker in `REAUDIT_03_Frontend.md`); it is cited here only because it
determines whether the proposed backend gate set can go green.

`alembic upgrade head --sql` is offline (`literal_binds`, no connection, `env.py:29-40`) and therefore
avoids DEP-01's missing psycopg driver. **But it is not sufficient as written.** With the shipped
`version_locations` (`alembic.ini:33` → nonexistent `backend/versions`) it emits `BEGIN; COMMIT;` and
exits **0** (ND-33), so it would pass a naive gate while creating nothing and would not exercise ND-07
either. Gate 3 must therefore assert on the output, not just the exit code:

```bash
cd backend
sql="$(alembic upgrade head --sql)"            # after alembic.ini:37 is fixed
grep -q "CREATE TABLE briefs" <<<"$sql" \
  && grep -q "CREATE TABLE audit_logs" <<<"$sql" \
  && grep -q "CREATE TABLE client_memories" <<<"$sql"
```

That assertion forces `version_locations` to be correct (ND-33) and keeps ND-07 visible: the emitted
DDL contains `FOREIGN KEY(client_id) REFERENCES clients (id)` while no revision creates `clients`, so a
real `upgrade head` against an empty database will fail — which is what gate 3 should eventually
become, once DEP-01's driver is present.

---

## 13. Appendix — Addendum Reproduction Commands

```bash
# Installed set (pip list returns empty for this uv-managed venv)
cd backend && ./.venv/bin/python -c "
from importlib.metadata import distributions
print('\n'.join(sorted(f\"{d.metadata['Name']}=={d.version}\" for d in distributions())))"

# Declared vs installed
./.venv/bin/python -c "from importlib.metadata import version; print(version('openai'))"   # 3.46.0

# Missing sync driver
./.venv/bin/python -c "
from sqlalchemy import create_engine
create_engine('postgresql://rm_user:x@localhost:5432/rm_workbench').connect()"            # ModuleNotFoundError: psycopg

# passlib / bcrypt incompatibility
./.venv/bin/python -c "
from passlib.context import CryptContext; CryptContext(schemes=['bcrypt']).hash('x')"     # AttributeError: __about__

# uv.lock is the real source of truth
grep -A1 'name = "openai"' uv.lock                                                         # version = "3.46.0"

# No tests, no CI
cd .. && find . \( -name "test_*.py" -o -name "*_test.py" \) \
        -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/node_modules/*"
cd backend && ./.venv/bin/python -m pytest --collect-only -q                               # no tests collected

# Frontend gate status
cd ../frontend && ./node_modules/.bin/tsc --noEmit                                         # exit=1, 1 error
```


```bash
# ND-33: alembic discovers zero revisions (probe config, repo untouched)
cd backend && B="$PWD" && sed -e "s|^version_path_separator.*|version_path_separator = os|" \
  -e "s|^version_locations.*|version_locations = $B/versions|" alembic.ini > /tmp/probe.ini
./.venv/bin/alembic -c /tmp/probe.ini upgrade head --sql          # → BEGIN; COMMIT;  (exit 0)
# with version_locations = $B/alembic/versions → real CREATE TABLE output

# ND-34: no revision template
ls alembic/script.py.mako                                          # → No such file

# ND-35: live schema predates the models
./.venv/bin/python -c "
import asyncio, asyncpg
async def m():
    c = await asyncpg.connect('postgresql://rm_user:demo_password_123@localhost:5432/rm_workbench')
    for r in await c.fetch(\"select column_name, data_type from information_schema.columns where table_name='clients' and column_name in ('preferences','created_at')\"):
        print(dict(r))
asyncio.run(m())"                                                  # → jsonb / timestamp with time zone

# ClientMemory.metadata is a hard error on the pinned SQLAlchemy 2.0.25
uv run --python 3.11 --with "sqlalchemy==2.0.25" python -c "
from sqlalchemy import Column, JSON, String
from sqlalchemy.orm import declarative_base
B = declarative_base()
class M(B):
    __tablename__='x'; id=Column(String, primary_key=True); metadata=Column(JSON)"
# → InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

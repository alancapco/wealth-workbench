# 02 · Implementation Feature Completeness Audit
## RM Workbench / Wealth Workbench — Implementation-Side Evidence Review

| Field | Value |
|---|---|
| Auditor | 交得齐 (Jiao Deqi), Release & Integration Engineer (`release-integrator`) |
| Team | `rm-workbench-gap-audit` |
| Codebase | `/Volumes/Orico/code/capco/wealth-workbench` |
| Requirement baseline | `PRODUCT REQUIREMENTS DOCUMENT · V1.1` (`/tmp/prd_full.txt`, 308 lines); authoritative 111-item inventory in `deliverables/01_PRD_Requirement_Inventory.md` |
| Sibling deliverables | `deliverables/01_PRD_Requirement_Inventory.md` (requirements side), `deliverables/03_Copilot_Capability_Review.md` (AI copilot code review), `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` (team-lead consolidated gap analysis) |
| Method | Read-only static review of **every** application source file + **live end-to-end probes** against the running server on `localhost:8000` (OpenAPI introspection + 20+ real HTTP calls) + log/config/doc inspection. **No application code was written or modified.** |
| Date | 2026-11-07 |

> **File-history note:** this report was first written at 13:50 (756 lines) and was overwritten at 13:51 by a 186-line team-lead compilation whose header incorrectly stated that no file had been produced by this role. I preserved that compilation verbatim under a separate name and then restored this full implementation-side audit with the integration sign-off; the team lead subsequently removed the standalone copy after folding its findings into `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md`. Both documents agree on the evidence; denominators differ (see §7.2 reconciliation). No team-lead content was lost.
>
> **Addendum (post-sign-off, 2026-11-07):** after `code-reviewer` independently verified the §4.4 422 contract defects, one additive cross-cutting finding — **N9 transcript-in-URL privacy exposure** — was appended to §4.1 (no verdict, coverage percentage, status distribution, or frozen ID changed; no rubric re-scoring). Citation-stability convention: all additions are anchored to section numbers, not line numbers, so downstream references (`03` §8.2 cites `02` §3.6; `GAP_ANALYSIS_RM_WORKBENCH.md`) remain valid.

---

## 0. Verdict Up Front

> ### 🔴 NOT a production system. NOT a functional implementation of the PRD.
> **Classification: a UI mockup backed by a thin, largely read-only API — with one live LLM call.**
> Of the three candidate labels, this is closest to **"UI mockup with a thin read-only API"**. It is a *demo prototype shell*: the stack does boot, a real PostgreSQL database is queried, and a real external LLM is called, but almost every PRD capability is either absent, a hardcoded stub, or a static fixture/design document that was never wired to code.

**Headline numbers**

| Metric | Result |
|---|---|
| Overall PRD coverage (111 discrete requirements, weighted) | **6.6%** |
| Overall PRD coverage (75 capability-item grouping, weighted) | **8.4%** |
| P0 coverage (Epic 1 + Epic 2, 15 FRs) — PRD release gate | **11.7%** (gate requires 100%) |
| All 28 functional requirements | **9.5%** |
| Requirements fully `Implemented` (meeting acceptance criteria) | **0 / 111** |
| Status distribution | `Implemented 0` · `Partial 2` · `Stub 24` · `Mock-data-only 2` · `Absent 83` |
| API routes registered | **27** total (`/` + `/health` + **25** under `/api/v1`) |
| API routes returning genuinely real DB data | **3 / 25 (12%)** |
| API routes returning hardcoded / mock / echo data | **16 / 25 (64%)** pure; **17 / 25 (68%)** incl. the stub Shariah report |
| API routes reachable from the running frontend | **5 / 25 (20%)** — 20 are orphaned |
| Test suite | **None** (0 test files; `npm run test` and `docker-compose.test.yml` do not exist) |
| Authentication / RBAC / tenant isolation / audit logging | **None** |
| "Three approval gates" persisted server-side | **No — cosmetic in every layer** |

**The single most damning runtime fact:** the P0 "Daily Top 10" ranking throws
`can't subtract offset-naive and offset-aware datetimes` on **every** invocation, is swallowed by
`except: return []`, and `GET /api/v1/dashboard/my-day` returns **HTTP 200 with `ranked_clients: []`**.
The flagship P0 feature is silently empty while the UI reports "System Ready".

---

## 1. Method, Scope and Evidence Base

1. **Static read of all application code**: 25 Python files under `backend/app/` (2,631 lines), 9 TS/TSX files under `frontend/` (1,325 lines), `docker-compose.yml`, `start.sh`, `stop.sh`, `setup.sh`, `.env`, `.env.example`, `backend/init.sql`, `backend/requirements.txt`, `backend/pyproject.toml`, `frontend/package.json`.
2. **Live runtime verification**: the app was running (`backend.pid` 22620, `frontend.pid` 22621). I introspected `GET /openapi.json`, then exercised the actual endpoints (dashboard, clients, market, brief generation, all three gates, workflow start, CRM status, Shariah report, contract-mismatch probes). Actual JSON responses are quoted in §4.3.
3. **Log evidence**: `backend.log` (63 KB), `frontend.log`.
4. **Requirements baseline**: full PRD V1.1 (`/tmp/prd_full.txt`) plus the reduced "Leadership Demo" MVP spec `designs/01_Requirements_Specification.md` (34 `MVP-FR-xx`).
5. **Four-layer inventory**: `demo_data/` (43 CSV + 12 JSON), `mockup/` (9 HTML + `app.js`), `designs/` (**12** markdown files, numbered 00–16 with gaps, ~798 KB) + root docs, and real code.

**Scoring rubric (stated so the percentages are auditable):**

| Status | Score | Definition |
|---|---|---|
| `Implemented` | 1.00 | Runs end-to-end in real code and meets the requirement's acceptance criteria |
| `Partial` | 0.50 | Real code exists for a meaningful subset, but key AC unmet |
| `Stub` | 0.25 | Route/service/function exists but returns static/hardcoded/echo data, or is present but broken at runtime |
| `Mock-data-only` | 0.15 | Exists only as fabricated demo content rendered by the UI, with no backend logic |
| `Absent` | 0.00 | No implementation in running code |

> **Note on "0 Implemented":** this does **not** mean zero working code. Real DB reads, a real LLM call, real ECharts rendering and real HubSpot SDK calls exist. It means **no PRD requirement is satisfied end-to-end with its acceptance criteria** — chiefly because D0 (identity/tenant/RBAC/audit), provenance, persisted approval state, policy checks and telemetry are all missing, so no capability can be compliantly "complete".

---

## 2. What Actually Exists — Complete Capability Inventory

### 2.1 Backend API routes (all 25 `/api/v1` operations)

Verified against the live server's `/openapi.json` and every `@router.*` decorator. Prefix `/api/v1` from `main.py:33`, routers assembled in `api/v1/__init__.py:10-15`.

| # | Method | Path | File:line | What it **ACTUALLY** does | Data source | Class |
|---|---|---|---|---|---|---|
| 1 | POST | `/briefs/generate` | `briefs.py:24-55` | Ignores `client_id`; builds a **hardcoded** `client_data = {"name": "Kenneth Wong", "aum": 45.2e6, ...}` (line 32-37) and passes **three empty lists** `portfolio_data=[]`, `market_signals=[]`, `interaction_history=[]` (39-41) to a live LLM. Returns 5 sections + `status:"draft"`, `requires_approval:True`. TODO line 31: *"Fetch client, portfolio, market data, interactions from DB"*. | Live LLM **over empty context** | Partial / stub |
| 2 | POST | `/briefs/approve` | `briefs.py:57-74` | Returns a static dict echoing `brief_id`/`approved_by`; **no DB write, no existence check**. TODO line 64: *"Update brief status in database"*. `edited_agenda` accepted in the request model (line 22) but **never read**. | None (echo) | Stub |
| 3 | GET | `/briefs/{brief_id}` | `briefs.py:76-92` | Returns hardcoded `{"client_id":"client-123","version":1,"status":"draft"}` for **any** ID; never 404. TODO line 83. | None (hardcoded) | Stub |
| 4 | GET | `/clients/` | `clients.py:27-42` | `select(Client).offset(skip).limit(limit)` — **real DB read**. Returns `c.__dict__` incl. SQLAlchemy internals. | PostgreSQL | **Real** |
| 5 | GET | `/clients/{client_id}` | `clients.py:44-62` | `select(Client).where(Client.id == client_id)` — **real DB read**, 404 on miss. | PostgreSQL | **Real** |
| 6 | GET | `/clients/{client_id}/portfolio` | `clients.py:64-83` | `select(Holding)` + `sum(current_value)` — **real DB read**. | PostgreSQL | **Real** |
| 7 | GET | `/clients/{client_id}/shariah-report` | `clients.py:85-134` | Real holdings query, then calls `screen_instrument(symbol, {"business_description": ""})` (line 103 — **always empty**) and `calculate_zakat(..., "2025-01-01")` (line 120 — **hardcoded hawl date**). Produces a report that always says 100% compliant. | DB + stub service | Stub over DB |
| 8 | GET | `/crm/status` | `crm.py:143-162` | Calls `find_contact_by_email("test@example.com")`. Because `crm_service.py:44-46` swallows **all** exceptions and returns `None`, this endpoint **always** reports `"status":"connected","message":"Successfully connected to HubSpot API"` — even when DNS fails. | None (false health) | Stub / false |
| 9 | POST | `/crm/sync` | `crm.py:16-87` | Reads all DB clients, builds HubSpot properties, calls real SDK create/update with old/new `diff`. **Unguarded external write, no approval gate, no idempotency, no audit.** Returns `"status":"success"` even when every client fails. | DB + HubSpot SDK (broken) | Partial / broken |
| 10 | POST | `/crm/sync/{client_id}` | `crm.py:90-140` | Same as #9 for one client. | DB + HubSpot SDK (broken) | Partial / broken |
| 11 | GET | `/dashboard/my-day` | `dashboard.py:18-88` | Mixed: real `select(count(Client.id), sum(Client.aum))` (54-57); **3 fabricated KPIs** `meetings_today:3, open_actions:7, ytd_performance:5.8` (63-65); `ranked_clients` from ranking service (**always `[]` at runtime**); mock news; `priority_actions` derived from `ranked_clients[0]`; hardcoded `workflow.correlation_id = "8f21a4b2"` (80). | DB + mock + broken | Mixed / broken |
| 12 | GET | `/dashboard/kpis` | `dashboard.py:90-112` | **100% hardcoded**: `total_aum: 428.5e6, client_count: 45, meetings_today: 3, ...`. TODO line 99: *"Calculate from database"*. | None (hardcoded) | Stub |
| 13 | GET | `/dashboard/book-stats` | `dashboard.py:114-132` | **100% hardcoded** (45 clients, 8 family offices, 9.5M avg, 18 meetings, 38M net new). Not in README. | None (hardcoded) | Stub |
| 14 | GET | `/dashboard/allocation` | `dashboard.py:134-154` | **100% hardcoded** 62/28/10 split. | None (hardcoded) | Stub |
| 15 | GET | `/dashboard/performance-trend` | `dashboard.py:156-186` | **Hardcoded** mock arrays `portfolio=[0,1.2,...,5.8]`, `benchmark=[...]`. Comment line 165: `# Mock YTD performance data`. | None (hardcoded) | Stub |
| 16 | GET | `/market/quotes` | `market.py:12-23` → `market_service.py:38-71` | **No network call.** Prices from `50.0 + hash(symbol) % 100` (line 51). Docstring (line 41): *"Returns mock data for now since Tiger SDK has dependency issues"*. Labelled `source_id:"TigerBroker"`, `source_kind:"live_feed"`. | `hash()` mock | Mock |
| 17 | GET | `/market/news` | `market.py:25-37` → `market_service.py:73-113` | **3 hardcoded news items** with fake URLs `https://example.com/news/1..3` (line 89). `symbols` argument accepted but **ignored**. | Hardcoded | Mock |
| 18 | GET | `/market/signals` | `market.py:39-55` → `market_service.py:115-140` | Derived from the `hash()`-based mock quotes. | `hash()` mock | Mock |
| 19 | GET | `/market/historical/{symbol}` | `market.py:57-69` → `market_service.py:142-169` | Generated loop `base_price + i*0.5`; comment `# Mock historical data`. | Generated mock | Mock |
| 20 | POST | `/market/mode` | `market.py:71-78` → `market_service.py:171-177` | Sets `self.mode` string only. **Both LIVE and REPLAY return the same fabricated data** — only the `source_kind` label differs. No recorded stream exists. | In-memory flag | Stub |
| 21 | POST | `/workflow/start` | `workflow.py:25-40` → `copilot_service.py:177-199` | Returns an **in-memory dict** with `stages: []`, `current_stage:"rank.clients"`. Nothing persisted, no orchestration, no skill invoked. | None (echo) | Stub |
| 22 | POST | `/workflow/consent` | `workflow.py:42-60` | Returns static dict `status:"consent_recorded"` / `"consent_declined"`. TODO line 49: *"Store consent in database with C-4 audit log"*. **No persistence, no audio, no recording state.** | None (echo) | Stub |
| 23 | POST | `/workflow/review/approve` | `workflow.py:62-89` | Returns `"actions_executed": ["crm_sync","d5_memory_update","email_draft_saved"], "workflow_complete": True` while the TODO at lines 69-73 says these actions are **not implemented**. This is a **false success**. | None (echo) | Stub / false |
| 24 | GET | `/workflow/{workflow_id}` | `workflow.py:91-106` | Hardcoded `{"status":"in_progress","current_stage":"brief.generate"}` for any ID; never 404. | None (hardcoded) | Stub |
| 25 | POST | `/workflow/extract-insights` | `workflow.py:108-126` → `copilot_service.py:201-244` | Live LLM call on a raw transcript **string** (no speaker labels/timestamps), hardcoded `confidence: 0.85` (line 236), hardcoded `client_context = {"name":"Kenneth Wong"}` (line 117), no evidence links. **Frontend contract is broken (422)** — see §4.4. | Live LLM, thin | Stub |

Plus `GET /` (`main.py:35-42`, static tagline) and `GET /health` (`main.py:44-54`) which hardcodes
`"database": "connected"` with `# TODO: Add actual DB health check` and `"crm":"active"` — a **false health claim**.

**Route classification summary (25 `/api/v1` routes):**

| Class | Count | Routes |
|---|---|---|
| Real DB-backed reads | 3 | #4, #5, #6 |
| Live external LLM (thin/broken context) | 2 | #1, #25 |
| Real DB + real HubSpot SDK (broken externally) | 2 | #9, #10 |
| Mixed real + mock + broken | 1 | #11 |
| Stub computed over real DB | 1 | #7 |
| Pure hardcoded / mocked data | 8 | #12, #13, #14, #15, #16, #17, #18, #19 |
| Echo / label-only stubs | 8 | #2, #3, #8, #20, #21, #22, #23, #24 |

### 2.2 Services (5 active modules + 1 dead duplicate)

| Service | File | Reality |
|---|---|---|
| `CopilotService` | `copilot/copilot_service.py` (247 lines) | **Real `AsyncOpenAI` client** (`api_key=settings.LLM_API_KEY`, `base_url=settings.LLM_BASE_URL`, lines 20-24). Two real call sites: `_generate_with_ai()` (140-148) and `extract_meeting_insights()` (222-230). `generate_brief()` attaches **hardcoded provenance labels** (49-84): `"TigerBroker + Copilot"`, `"TigerBroker News"`, `"D5 Client Memory"` — none of which were actually queried. `_generate_fallback_brief()` (157-175) returns 5 hardcoded "temporarily unavailable" strings. `orchestrate_workflow()` (177-199) returns an unpersisted dict with `stages: []`. |
| `RankingService` | `ranking/ranking_service.py` (258 lines) | Real DB queries for `Client`, `Holding`, `Interaction` and heuristic Opportunity/Risk/Retention scoring with fixed weights 0.4/0.35/0.25 (16-20). Reason code = `max()` of 3 scores + 3 static descriptions (203-231). Evidence chips include a hardcoded `"rank.clients v1.2"` string (248-253). **Runtime-broken**: `_calculate_retention` (178-179) subtracts a timezone-aware `interaction_date` from naive `datetime.now()` → exception → `rank_clients` catches (81-83) and returns `[]`. No DNC exclusion, no snooze/pin/dismiss, no outcome capture, no telemetry. |
| `MarketDataService` | `market/market_service.py` (180 lines) | **Fully mocked.** Imports `requests`, `base64`, `hmac`, `hashlib` and defines `base_url` and `_sign_request()` (29-36) but **never makes an HTTP request**. `get_real_time_quote` uses `hash(symbol)` (51-54). Docstrings say *"Returns mock data for now since Tiger SDK has dependency issues"* (41) and *"Mock news data"* (81). `set_mode()` only flips a label. |
| `ShariahService` | `shariah/shariah_service.py` (196 lines) | Checks `os.path.exists(settings.SHARIAH_TOOLS_PATH)` (`/tmp` in `.env:36`) and does `sys.path.insert`, but **never imports or calls any Shariah tool**. `screen_instrument` sets `"compliant": True, # Placeholder` (line 37) and only checks 5 prohibited keywords against a `business_description` that callers always pass as `""` → **always compliant**. `calculate_zakat` = 2.5% × (Equity + Cash) (97-99), "Simplified Hawl Method", no nisab/hawl/lunar convention. `get_shariah_compliant_alternatives` (124-148) returns a fake `ALT-{symbol}-1` — **never called by any endpoint** (orphan). |
| `CRMService` (live) | `crm/crm_service.py` (169 lines) | Real `hubspot` SDK: `search_api.do_search`, `basic_api.create/update/get_by_id`, old→new `_calculate_diff` (154-166). **Broken at runtime**: `create_contact` calls `basic_api.create(simple_public_object_input=...)` but SDK v13 expects `simple_public_object_input_for_create` (see `backend.log:395`). No idempotency keys, no queue/retry, no audit. |
| `CRMService` (dead duplicate) | `crm/hubspot_service.py` (103 lines) | A **second `CRMService` class** with `sync_client()` (returns `status:"pending_approval"` diff) and `execute_sync()`. **Never imported anywhere** (`grep` confirms). `crm/__init__.py:2` re-exports only `crm_service.py`. The two-phase approval-aware implementation is orphaned while the unguarded one is wired — violates Iron Law #1 (no duplicate implementations). |

All five active services are instantiated as module-level singletons at import time.

### 2.3 Data model (`models.py`, 209 lines)

7 tables + 3 enums declared; only **3 tables are ever read** by endpoints, and **zero tables are written** by any endpoint.

| Table | Declared | Read by code | Written by code |
|---|---|---|---|
| `clients` | `models.py:33-66` | ✅ (`clients.py`, `dashboard.py`, `crm.py`, `ranking_service.py`) | ❌ (only `seed_demo_data.py` offline script) |
| `holdings` | `models.py:69-90` | ✅ | ❌ |
| `interactions` ("D5 Client Memory") | `models.py:115-139` | ✅ (`ranking_service.py:169`) | ❌ — only 2 rows seeded offline |
| `market_ticks` (comment "TimescaleDB hypertable") | `models.py:93-112` | ❌ | ❌ — **never converted to a hypertable**; no `create_hypertable`, no `time_bucket` anywhere |
| `briefs` | `models.py:142-172` | ❌ | ❌ — 5 sections, `state`, `approved_by`, `correlation_id` columns exist but no endpoint touches them |
| `workflow_instances` | `models.py:175-189` | ❌ | ❌ |
| `audit_events` | `models.py:192-209` | ❌ | ❌ — **no audit event is ever emitted** |

Enums `SourceKind`, `WorkflowStage`, `ArtefactState` (`models.py:9-30`) exist; `ArtefactState` (draft → pending_review → approved/edited/rejected/blocked/stale/superseded) is **never used** — the "state machine" is design-only.

**No model exists for**: users/roles/tenants, consent state, approval tokens, outreach drafts/messages, products/instruments, suitability assessments/overrides, Shariah screening results/evidence packs, family graph nodes/edges/entitlements, telemetry events, config versions, or trade tickets.

### 2.4 Frontend — what the user can actually do

2 routes, 4 components, 1 API client (`frontend/lib/api.ts`).

| File | What the user can actually do | Reality |
|---|---|---|
| `app/page.tsx` (409 lines) — `/` | Loads **only 3** endpoints via `Promise.all`: `getMyDay`, `getAllocation`, `getPerformanceTrend` (32-36). Renders 4 KPI cards, 2 ECharts, a hardcoded 3-meeting schedule, a hardcoded market-news panel, 4 hardcoded "Priority Actions" cards, 5 hardcoded book stats. Three "Open Brief" buttons (237-242, 254-259, 271-276), one "View Family Graph" button (277-282). | **Mostly static JSX.** Header: hardcoded `● LIVE MARKET DATA` (93) and `Workflow ID: 8f21a4b2` (115); hardcoded RM `Sarah Chen` (120), hardcoded date `Tuesday, 16 March 2026` (131). KPI deltas `↑ $12.3M this month (+2.9%)`, `↑ Benchmark +1.2%`, `Next at 10:00 AM` hardcoded (146, 156, 177). Schedule text hardcoded (233-236 etc.). News panel **ignores `marketNews` content** and prints hardcoded `HSBC Holdings +2.3%` / `● LIVE · Reuters` (298-306) — note the backend says `TigerBroker News`, so the displayed provenance is a *different fabrication*. Priority Actions are 4 hardcoded `<div>`s with `cursor-pointer` but **no `onClick`** (323-349). Book stats hardcoded 45/8/9.5M/18/+38M (354-375) — not even fetched from `/dashboard/book-stats`. Footer admits `SYNTHETIC DEMO DATA` / `Not for production use` (384-389) while the header claims `LIVE MARKET DATA`. |
| `components/BriefModal.tsx` (213 lines) | Calls `briefApi.generate(clientId)` (28); renders 5 sections; "Edit Agenda" textarea (164-182); "Approve & Continue to Meeting" button (200-206). | **Client-side fabrication path** (31-60): if a section lacks content it injects hardcoded invented interactions (`Last meeting (15 days ago)...`) and market news (`HSBC +2.3% ... 51% of equity allocation... 6% drift`) with **fabricated provenance** `source:'CRM & D5 Memory', confidence:0.92` and `source:'TigerBroker News · LIVE', confidence:1.0`. A hardcoded `● LIVE · TigerBroker` chip is shown **unconditionally** (138-140). `handleApprove` calls `briefApi.approve('brief-123', 'Sarah Chen', ...)` — a **hardcoded brief ID** (77); the backend discards `edited_agenda`, so **RM edits are lost**. No regenerate, no feedback, no per-section status, no clickable source links. |
| `app/brief/[clientId]/page.tsx` (155 lines) | Duplicate full-page brief UI with the same edit/approve controls. | **Orphan route** — nothing links to it (dashboard uses `BriefModal` instead). Header hardcodes `Kenneth Wong` (59) regardless of `clientId`. Same hardcoded `'brief-123'` approve (33). **Duplicate implementation** (Iron Law #1). |
| `components/FamilyGraphModal.tsx` (259 lines) | Renders an ECharts force graph of 7 family entities with entitlement-labelled edges; zoom/roam; "Close". | **100% hardcoded in the component** (22-95): node values `120.5, 35.2, 28.8, 31.5, 8.5, 7.2, 9.3` sum to **241.0M** while the title claims `Total AUM: SGD 120.5M` (100) — the graph does not reconcile. **No API call, no backend, no entitlement enforcement, no document intelligence.** Tooltip says `Click for details` (111) but there is **no click handler**. |
| `components/AllocationChart.tsx` / `PerformanceChart.tsx` | Render the two hardcoded dashboard datasets. | Presentation only. |
| `lib/api.ts` (88 lines) | Declares 5 API groups (dashboard 5, market 4, clients 4, briefs 3, workflow 5 = 21 methods). | Only **5 methods are ever called** by the UI (`getMyDay`, `getAllocation`, `getPerformanceTrend`, `generate`, `approve`). `marketApi`, `clientApi`, `workflowApi` are **entirely dead**. 3 contract bugs — see §4.4. |

**Unused declared dependencies**: `swr` (README says "State: SWR for data fetching" — **never imported**), `lightweight-charts` (README says "TradingView Lightweight Charts" — **never imported**), `date-fns`, `clsx`. Backend `requirements.txt` declares `pgvector`, `redis`, `python-jose`, `passlib`, `pytest` — **none used** in `backend/app/`.

### 2.5 Orphan inventory (integration view)

| Orphan | Location | Why it matters |
|---|---|---|
| 20 of 25 API endpoints | `api/v1/endpoints/*` | Unreachable from the UI; no consumer, no test |
| `crm/hubspot_service.py` | 103 lines, entire file | Dead duplicate `CRMService`; the approval-aware `pending_approval` diff / `execute_sync()` flow is never wired to a gate |
| `app/brief/[clientId]/page.tsx` | 155 lines | Duplicate brief UI, no inbound link |
| `ClientCreate` Pydantic model | `clients.py:17-25` | Defined, no POST endpoint uses it |
| `ShariahService.get_shariah_compliant_alternatives` | `shariah_service.py:124-148` | Never called |
| `marketApi` / `clientApi` / `workflowApi` | `lib/api.ts` | Never imported by any component |
| `Brief`, `WorkflowInstance`, `AuditEvent`, `MarketTick`, `ArtefactState` | `models.py` | Declared, never read or written by any endpoint |
| `demo_data/` (55 data files) | root | **Zero references** from `backend/app` or `frontend/` — see §6 |
| `docker-compose.test.yml`, `npm run test`, `pytest` | README:231-244 | All three test commands are non-functional |

---

## 3. README.md Claim Audit — One By One

Source: `README.md` (325 lines). Verdict legend: **Confirmed** / **Overstated** / **False**.

### 3.1 "📊 Features Implemented — Core Workflow" (lines 174-182)

| # | README claim | Verdict | Code evidence |
|---|---|---|---|
| C1 | ✅ **Client Ranking Algorithm** — Opportunity, Risk, Retention scoring | **Overstated** | Algorithm exists in `ranking_service.py:22-231` with real DB reads, but **always returns `[]` at runtime**: `backend.log:67,115,167,215,295,348,458,511,568,621,675` all show `Error ranking clients: can't subtract offset-naive and offset-aware datetimes`; caught by `except: return []` (81-83). `/dashboard/my-day` live probe returned `"ranked_clients": []`. No reason-code drill-down, no RM controls, no DNC exclusion. |
| C2 | ✅ **Market Data Integration** — Tiger Broker real-time quotes and news | **False** | `market_service.py:41` docstring *"Returns mock data for now since Tiger SDK has dependency issues"*; quotes from `hash(symbol)` (51-54); 3 hardcoded news items with `https://example.com/news/1` URLs (82-107). `requests`/`hmac` imported but **no network call**. `MARKET_NEWS_AND_LLM.md:5,53` repeats the false claim ("All news displayed on the dashboard comes from Tiger Broker's news feed") while the UI actually hardcodes `● LIVE · Reuters` (`page.tsx:306`). |
| C3 | ✅ **Brief Generation** — AI-powered 5-section client briefs | **Overstated** | 5 sections and a **live LLM** do exist (`copilot_service.py:123-151`; `backend.log:360,699` show `POST https://cc-vibe.com/v1/chat/completions 200 OK`). But `briefs.py:32-41` passes hardcoded "Kenneth Wong" + three **empty** data lists; the live response says *"Current holdings, allocation, and key portfolio metrics were not provided"*, *"No recent interactions were provided"*, *"No market news or signals were provided"*. Provenance labels are hardcoded strings (49-84), not source links. No regeneration, no versioning, no feedback. |
| C4 | ✅ **Three Approval Gates** — Gate 1 (Brief), Gate 2 (Consent), Gate 3 (Review) | **False** | All three endpoints return static dicts with TODOs and **zero persistence**: `briefs.py:64`, `workflow.py:49`, `workflow.py:69-73`. Live probes: approving non-existent `brief-123` returns 200 `"approved"`; `GET` afterwards still returns `"status":"draft"`; Gate 3 claims `actions_executed: [crm_sync, d5_memory_update, email_draft_saved]` but executes nothing; `GET /workflow/fake-wf-999` still says `in_progress`. In the mockup layer they are JS booleans (`app.js:166-207`). **No persisted server-side state, no approver record, no write protection.** |
| C5 | ✅ **Provenance Tracking** — Evidence chips on every AI statement | **False** | `copilot_service.py:49-84` attaches 5 hardcoded source names with `datetime.now()` as the timestamp; no `source_id`, no `as_of` of the underlying data, no clickable record. `BriefModal.tsx:39-58` fabricates `confidence: 0.92` / `1.0`. `page.tsx:306` prints `Reuters` while the API says `TigerBroker News`. `demo_data/README.md` defines the real C-1 envelope (8 columns) — **no running code implements it**. |
| C6 | ✅ **Shariah Compliance** — Screening, zakat calculation, reporting | **Overstated** | `screen_instrument` returns `"compliant": True, # Placeholder` (`shariah_service.py:37`) and callers pass `business_description: ""` → every holding is compliant by construction; live probe returned `compliance_percentage: 100.0` for a **non-Shariah client**. No financial-ratio screens, no SSB evidence, no drift monitoring. Zakat = flat 2.5% with a hardcoded `2025-01-01` hawl date (`clients.py:120`). `SHARIAH_TOOLS_PATH=/tmp` (`.env:36`) — no tools are imported. `designs/01_Requirements_Specification.md:104-105` explicitly puts FR-4.1/4.2/4.3 **out of scope**. |

### 3.2 "Dashboard (My Day)" (lines 184-190)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| D1 | ✅ KPI Cards with **real-time data** | **False** | `/dashboard/kpis` fully hardcoded (`dashboard.py:99-109`, `# TODO: Calculate from database`); `/my-day` hardcodes 3 of 5 KPIs (63-65). Live probe: `/kpis` says `client_count: 45, total_aum: 428.5M` while `/my-day` (real DB) says `total_clients: 3, total_aum: 198.5M` — **the two endpoints contradict each other**. |
| D2 | ✅ ECharts allocation donut chart | **Confirmed (but data is fake)** | `AllocationChart.tsx` renders correctly; input is the hardcoded 62/28/10 object from `dashboard.py:142-151`. |
| D3 | ✅ Performance trend line chart | **Confirmed (but data is fake)** | `PerformanceChart.tsx` renders correctly; input is the hardcoded arrays at `dashboard.py:165-168`. |
| D4 | ✅ Today's schedule with context | **False** | Fully hardcoded JSX with literal times/names/descriptions (`page.tsx:229-285`). No calendar integration, no `meetings_calendar.csv` wiring. |
| D5 | ✅ Live market news with indicators | **False** | Backend returns 3 hardcoded items (`market_service.py:82-107`); UI ignores them and prints hardcoded `HSBC Holdings +2.3%` with a `● LIVE · Reuters` chip and a browser clock (`page.tsx:294-311`). |
| D6 | ✅ Priority actions | **False** | 4 hardcoded `<div>`s (`page.tsx:322-350`) with no `onClick`; the API's `priority_actions` is `[]` at runtime and is **never read** by the frontend. |

### 3.3 "Integrations" (lines 192-196)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| I1 | ✅ Tiger Broker SDK for market data | **False** | No Tiger SDK import anywhere. `market_service.py` defines `base_url` and `_sign_request()` but never calls them; `.env` credentials (`TIGER_CLIENT_ID`, private key, token) are **never used**. |
| I2 | ✅ HubSpot CRM sync | **Overstated** | Real SDK code exists (`crm_service.py`), but `backend.log:391-408` shows DNS failure to `api.hubapi.com` **and** an SDK signature bug `BasicApi.create() missing 1 required positional argument: 'simple_public_object_input_for_create'`; all 3 clients fail yet `POST /crm/sync` returns `"status":"success"`. `GET /crm/status` falsely reports `connected`. It is a one-way bulk contact push, not the bidirectional post-meeting CRM integration in PRD §9. |
| I3 | ✅ Shariah tools integration | **False** | Path check + `sys.path.insert` only (`shariah_service.py:15-24`); **no import, no tool call**. `.env` points to `/tmp`. |
| I4 | ✅ OpenAI/Anthropic copilot | **Overstated (partially true)** | A real OpenAI-compatible client is used, but the configured provider is a third-party proxy `https://cc-vibe.com/v1`, model `gpt-6.1-sol` (`.env:22-23`), **not OpenAI/Anthropic**. Only 2 call sites; no orchestration, no model/prompt versioning, no zero-retention controls. |

### 3.4 "🏗️ Architecture" (lines 5-19) and "✨ Key Features Aligned with Specifications" (lines 317-325)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| A1 | Database: PostgreSQL with TimescaleDB **+ pgvector** | **Overstated** | PostgreSQL/TimescaleDB container is real (`docker-compose.yml:3`). But `init.sql:5` requests `CREATE EXTENSION vector` on `timescale/timescaledb:latest-pg15` (pgvector not bundled by default — clean-volume risk), `MarketTick` is **never made a hypertable** (comment only, `models.py:92`), and **no vector column, embedding, index or similarity query exists**. |
| A2 | Market Data: Tiger Broker OpenAPI SDK | **False** | See I1. |
| A3 | Frontend Charts: ECharts **+ TradingView Lightweight Charts** | **Overstated** | ECharts used; `lightweight-charts` in `package.json` but never imported. |
| A4 | State: **SWR** for data fetching | **False** | `swr` in `package.json`; **zero imports**. Data fetched with raw `axios` + `useEffect`. |
| A5 | "All features implemented according to the design specifications … `01_Requirements_Specification.md` - 34 functional requirements" | **False** | The referenced spec is for a **"RM Workbench MVP (Leadership Demo)"** — a *different, reduced scope* with 34 `MVP-FR-xx` items, and its §2.3 (lines 100-108) explicitly declares FR-16/17, FR-18/19, FR-4.1.2-4.1.4, FR-4.2/4.3, FR-5.1.2/5.2/5.3, FR-21 **out of scope**. Even against that reduced demo spec, the code fails: §1.1 (lines 40-53) requires the live market feed, provenance chips, audit writes, approval gates, re-rank and mode switch to be **REAL** — in code they are all mocked/echo/broken. The spec also requires the LLM to be **STUBBED with deterministic outputs** (line 49); the code instead calls a live third-party LLM. `designs/16_Executive_One_Pager.md` states *"No code exists today. Authorising a build is a separate, explicit decision."* **The implementation neither matches the PRD nor the design spec.** |
| A6 | "Provenance-first design with evidence chips" / "Three human approval gates" / "Honest degradation patterns" | **False** | See C4/C5. Honest degradation is contradicted by `/crm/status` → `connected`, Gate 3 → `workflow_complete: True`, `/health` → `database: connected`, and `POST /crm/sync` → `status: success` with 3 errors. |

### 3.5 API endpoint list (README lines 198-223) vs actual registration

| Check | Result |
|---|---|
| README lists | **16** endpoints (4 dashboard, 4 market, 4 clients, 4 briefs/workflow) |
| Actually registered under `/api/v1` | **25** (verified via live `/openapi.json` and 25 `@router` decorators) |
| README-listed endpoints that exist | **16 / 16 ✅** — no phantom routes claimed (one minor difference: README writes `GET /api/v1/clients`, actual path is `/clients/`, FastAPI 307-redirects) |
| **Undocumented real routes (9)** | `GET /dashboard/book-stats`, `POST /market/mode`, `GET /crm/status`, `POST /crm/sync`, `POST /crm/sync/{client_id}`, `GET /briefs/{brief_id}`, `POST /workflow/start`, `POST /workflow/extract-insights`, `GET /workflow/{workflow_id}` |
| Coverage of the documented list | **16 of 25 = 64%**; notably the **entire CRM router (3 routes, 162 lines) is undocumented**, and 2 of the 3 "approval gate" companion routes are undocumented |
| Root docs | `GET /` and `GET /health` omitted (health is mentioned in `RUNNING.md:41`) |

### 3.6 Setup / Testing claims

| Claim | Verdict | Evidence |
|---|---|---|
| "Start all services (PostgreSQL, Redis, Backend, Frontend)" via `docker-compose up -d` (README:47-51) | **False** | `docker-compose.yml` defines **only `postgres` + `redis`**. The working path is `start.sh`, which runs backend/frontend as local processes (56, 73). |
| "Run migrations: `alembic upgrade head`" (README:63) | **False** | `backend/alembic/` contains **only `env.py`**, no `versions/` migration scripts. Tables are created by `scripts/init_db.py:19` via `Base.metadata.create_all`, which **`start.sh` never invokes**. |
| "Seed demo data" (README:66) | **Overstated** | `seed_demo_data.py` seeds **3 hardcoded Python clients** (35-93), 3 holdings and 2 interactions — **not** the 43 CSV/12 JSON fixtures. `start.sh` never runs it. A clean `./start.sh` on a fresh volume produces a DB with **no tables** → all DB endpoints 500. `RUNNING.md:13-14` and `QUICKSTART.md:50-51` claim "Create database tables automatically / Seed demo data" — both false. |
| "Backend tests `pytest`" / "Frontend `npm run test`" / `docker-compose -f docker-compose.test.yml` (README:231-244) | **False** | **0 application test files**; `package.json` has no `test` script; `docker-compose.test.yml` does not exist. `pytest` is in `requirements.txt` but unused. |
| "3 clients with portfolios" (RUNNING.md:163-175) | **Partially false** | Live DB has 3 clients but **only Kenneth Wong has holdings (2, not 3)**; Ahmad Rahman and Tan Family Office have none. `is_family_office` is `False` for Tan Family Office in the live DB although `seed_demo_data.py:81` sets `True`, and `source_kind` is `null` on holdings — **the live DB content has drifted from the checked-in seed script**. |

### 3.7 Contradictions between the project's own documents

- `QUICKSTART.md:154-171` says "✅ Tiger Broker market data integration … ✅ Shariah tools integration" **and** "🔜 Not Yet Implemented: Real Tiger Broker market data … Real AI brief generation" — self-contradictory, and the second half is also wrong: real AI brief generation **is** live (`backend.log:360,699`), while Tiger data is not real and never can be without a code change.
- `MARKET_NEWS_AND_LLM.md:5,53` claims all market data is from Tiger Broker; `market_service.py:46` says it is mock.
- `README.md:93` prints `● LIVE MARKET DATA`; `page.tsx:384-389` prints `SYNTHETIC DEMO DATA · Not for production use`.
- `demo_data/README.md` says `no vendor is ever named`; the running code and UI name "TigerBroker" and "Reuters" everywhere.
- `designs/01_Requirements_Specification.md:49` requires a **stubbed deterministic LLM**; the code calls a live external LLM — the implementation diverges from its own design spec in the opposite direction from the README's claims.

---

## 4. Runtime Reality

### 4.1 Direct answers to the audit questions

| Question | Answer | Evidence |
|---|---|---|
| **PostgreSQL + TimescaleDB + pgvector?** | **PostgreSQL/TimescaleDB: yes (real, containerized). pgvector: no.** | `docker-compose.yml:3` uses `timescale/timescaledb:latest-pg15`; `.env:2` DB URL; live SQL in `backend.log` confirms real `asyncpg` queries. `init.sql:5` asks for `vector` extension but no vector column/index/query exists; `MarketTick` is never made a hypertable. Redis container runs but **is never used** (`REDIS_URL` declared only). |
| **Tiger Broker live or mocked?** | **Mocked — 100%.** | `market_service.py:41` *"Returns mock data for now since Tiger SDK has dependency issues"*; `hash(symbol)` prices; `example.com` news URLs; `requests` imported but never called; `.env:8-13` Tiger credentials are dead config. `POST /market/mode` LIVE/REPLAY changes only a label. |
| **HubSpot live or gracefully degraded?** | **Real SDK, but broken and falsely reported healthy.** | `backend.log:391-408`: DNS `NameResolutionError` for `api.hubapi.com` **plus** SDK bug `BasicApi.create() missing 1 required positional argument: 'simple_public_object_input_for_create'`. `crm.py:77-83` returns `"status":"success"` with all 3 clients in `error`. `GET /crm/status` live probe returned `"status":"connected"` — a **false positive** caused by `crm_service.py:44-46` swallowing exceptions. Not graceful degradation (PRD §6 requires visible pending/failed status and no false success). |
| **LLM live or mocked?** | **LIVE — a real external call, to a third-party proxy.** | `.env:21-23` `LLM_API_KEY`, `https://cc-vibe.com/v1`, `gpt-6.1-sol`. `copilot_service.py:20-24` real `AsyncOpenAI`. `backend.log:360,699`: `POST https://cc-vibe.com/v1/chat/completions "HTTP/1.1 200 OK"`. Two call sites only. Fallback (`_generate_fallback_brief`) is hardcoded text. **Governance concern**: client name/AUM/transcript are sent to an unvetted third-party endpoint with no zero-retention contract, no prompt minimisation, no PII controls — violates PRD §8. |
| **Authentication / RBAC / tenant isolation / audit logging?** | **None of the four.** | No auth middleware, no `HTTPBearer`, no JWT/session, no User/Role/Tenant model; `grep -rn "Depends("` across all endpoints returns only `Depends(get_db)`. `rm_id` is an unvalidated **query parameter defaulting to `"RM001"`** (`dashboard.py:20`, `ranking_service.py:35` filters `external_id LIKE 'RM001%'`). `SECRET_KEY` (`config.py:9`) is declared and **never used**. `python-jose`/`passlib` are in `requirements.txt` but unused. `AuditEvent` table exists but **no code writes to it**. CORS `allow_methods=["*"]`, `allow_headers=["*"]` (`main.py:25-26`). Any caller can read any client and trigger `POST /crm/sync` (an external write) with no identity. |
| **Are the three approval gates real persisted server-side state?** | **No. Cosmetic in every layer.** | Backend: `briefs.py:57-74`, `workflow.py:42-60`, `workflow.py:62-89` are echo endpoints with TODOs and zero DB writes. Live probes confirm approvals do not persist and non-existent IDs are accepted. `AuditEvent`/`WorkflowInstance`/`Brief` tables are never written. Mockups: `app.js:166-207` flips `AppState.briefApproved = true` etc. and shows a toast "CRM updates queued". Design docs define C-2/C-3/C-4 contracts — none implemented. Worse: `POST /crm/sync` is an **unguarded external write** with no gate. |
| **Any test suite?** | **No.** | 0 `test_*.py` / `*.test.tsx` / `*.spec.ts`; no `pytest.ini`; no `docker-compose.test.yml`; no `test` npm script. `frontend.log` shows `⚠ Fast Refresh had to perform a full reload due to a runtime error`. |
| **Does a clean start work?** | **No — integration/build defect.** | `start.sh` (98 lines) starts postgres+redis, `uv sync`, then `uvicorn` and `npm run dev`. It **never** calls `init_db.py`, `seed_demo_data.py`, or `alembic`. `main.py` has **no startup/lifespan hook**. The current DB was seeded manually at some earlier point. On a fresh volume every DB endpoint would 500. |

**Credential hygiene (additional cross-cutting risk):** `.env` contains real-looking Tiger/HubSpot/LLM credentials and a development `SECRET_KEY`; `.env` is gitignored, but `HUBSPOT_CREDENTIALS.md` and `HUBSPOT_SETUP.md` contain credential-shaped strings in the repository root and are not gitignored (`.gitignore` covers `.env` only). Rotate before any sharing.

**Transcript-in-URL privacy exposure (N9, cross-cutting — §4.1 addendum):** `/workflow/extract-insights` declares `transcript: str` and `client_id: str` as *bare* scalar arguments with no `Body(...)` and no Pydantic request model (`workflow.py:108-113`), so FastAPI binds both as **query parameters** — already proven by my §4.4 X2 probe, whose `422` body is `{"loc":["query","transcript"],…},{"loc":["query","client_id"],…}`. Consequence: the moment the frontend/backend contract is "fixed" to match the backend, the **entire client meeting transcript is serialized into the URL query string** and is persisted in Uvicorn access logs (`backend.log` records the full `POST …?…` request line), any reverse-proxy/WAF logs, browser history, `Referer` headers and APM traces — with no redaction, no retention limit and no deletion path. This conflicts with **NFR-05** (privacy / residency / retention / legal hold), **GOV-02** (zero provider retention / prompt minimisation) and the PRD's transcript retention / deletion policy. Both rows are already `Absent` in §5.9 / §5.10; this is a further, concrete violation on top of the third-party `cc-vibe.com` exposure noted above. **Attribution:** integration-level contract defect — backend `endpoints/workflow.py` (contract owner) + frontend `lib/api.ts:86-87` (caller), not a single-unit bug. **Fix (Iron Law #3):** introduce an explicit Pydantic request model (e.g. `ExtractInsightsRequest(transcript, client_id)`) so the transcript travels in the request **body**, plus query-string scrubbing in access logs. **Severity P1 / privacy.** It is latent today only because `workflowApi` is entirely dead (0 UI imports, §2.4) and the current call returns 422 — "broken" is *accidentally* masking "unsafe", which is not a control. Raised by `code-reviewer` (item N9 in `03_Copilot_Capability_Review.md`) from the §4.4 evidence in this report.

### 4.2 The silent ranking failure (P0 blocker, quoted from logs)

```
backend.log:67   ERROR:app.services.ranking.ranking_service:Error ranking clients:
                 can't subtract offset-naive and offset-aware datetimes
backend.log:69   ERROR:app.api.v1.endpoints.dashboard:Error loading dashboard: name 'select' is not defined
backend.log:72   INFO: ... "GET /api/v1/dashboard/my-day?rm_id=RM001 HTTP/1.1" 500 Internal Server Error
... (repeated at lines 115,167,215,295,348,458,511,568,621,675 — still failing at the last log line)
```

The `select` NameError was hot-fixed by a reload (`backend.log:229`), so `/my-day` now returns 200 — but the datetime bug in `ranking_service.py:178-179` was **never fixed**. Because `rank_clients` catches all exceptions and returns `[]` (81-83), the failure is invisible to the caller: **HTTP 200, empty Top 10, empty priority actions, no error surfaced to the RM**. This is the exact "false success" the PRD §6 boundary table forbids.

### 4.3 Live end-to-end probe transcript (2026-11-07, actual responses)

| Step | Call | Actual result |
|---|---|---|
| 1 | `GET /api/v1/clients/` | `200` — 3 real DB clients: Kenneth Wong (HKD 45.2M), Ahmad Rahman (SGD 32.8M), Tan Family Office (SGD 120.5M). `is_family_office` **False** for all. |
| 2 | `GET /api/v1/dashboard/my-day` | `200` — `kpis: {total_aum: 198500000.0, total_clients: 3, meetings_today: 3, open_actions: 7, ytd_performance: 5.8}`; **`ranked_clients: []`**; **`priority_actions: []`**; 3 hardcoded news items (`url: https://example.com/news/1`); 3 `hash()`-derived "TigerBroker" signals; `workflow: {current_stage:"rank.clients", correlation_id:"8f21a4b2"}`. |
| 3 | `GET /api/v1/dashboard/kpis` | `200` — `total_aum: 428500000.0, client_count: 45` — **contradicts step 2**. |
| 4 | `GET /api/v1/market/quotes?symbols=HSBC,00700.HK` | `200` — `{"symbol":"HSBC","price":50.0,"change":-2.5,"change_percent":-5.0,"source_id":"TigerBroker","source_kind":"live_feed","mode":"LIVE"}` — fabricated, labelled live. |
| 5 | `POST /api/v1/briefs/generate` | `200` — real LLM; 5 sections with content: *"Current holdings, allocation, and key portfolio metrics were not provided…"*, *"No recent interactions were provided."*, *"No market news or signals were provided."* Provenance: `source:"TigerBroker News"`, `source:"D5 Client Memory"` — **sources that were never queried**. `status:"draft", requires_approval:true`. |
| 6 | `POST /api/v1/briefs/approve` with `brief_id:"does-not-exist-123"` | `200` — `{"brief_id":"does-not-exist-123","status":"approved","approved_by":"RM001","gate":"gate1"}`. No validation. |
| 7 | `GET /api/v1/briefs/does-not-exist-123` | `200` — `{"brief_id":"does-not-exist-123","client_id":"client-123","version":1,"status":"draft"}`. **Approval did not persist; no 404.** |
| 8 | `POST /api/v1/workflow/consent` | `200` — `{"status":"consent_recorded","gate":"gate2"}` — nothing stored. |
| 9 | `POST /api/v1/workflow/review/approve` with `workflow_id:"fake-wf-999"` | `200` — `{"gate":"gate3","status":"approved","actions_executed":["crm_sync","d5_memory_update","email_draft_saved"],"workflow_complete":true}` — **all three actions are TODOs and did not run**. |
| 10 | `GET /api/v1/workflow/fake-wf-999` | `200` — `{"status":"in_progress","current_stage":"brief.generate"}` — **contradicts step 9**. |
| 11 | `POST /api/v1/workflow/start` | `200` — in-memory dict with `stages: []`, no persistence. |
| 12 | `GET /api/v1/crm/status` | `200` — `{"status":"connected","message":"Successfully connected to HubSpot API"}` — **false** (log shows DNS failure). |
| 13 | `GET /api/v1/clients/{id}/shariah-report` | `200` — 2 holdings, `compliant_holdings: 2`, `compliance_percentage: 100.0`, `criteria_checked` lists "Financial ratios screening" although **no ratio is computed**; hardcoded `AAOIFI Standard`. |
| 14 | `GET /health` | `200` — `{"database":"connected","crm":"active"}` — hardcoded. |

**End-to-end conclusion:** the *Prepare → Meet → Follow up* loop does **not** close. Brief generation produces content from empty context; the gates accept anything and persist nothing; no CRM update, email draft, ticket, memory update or re-rank ever occurs. The only genuinely executed cross-tier actions are: 3 DB `SELECT`s and 1 external LLM HTTP call.

### 4.4 Frontend ↔ backend contract defects (integration-level, found by live probes)

| # | Defect | Owner unit | Severity | Live evidence |
|---|---|---|---|---|
| X1 | `workflowApi.start` posts `{workflow_type, client_id, trigger}` in the **body**, but `/workflow/start` declares them as **query params** (`workflow.py:26-30`) | Frontend `lib/api.ts:74-75` + Backend `workflow.py` | **P1** | `422 {"detail":[{"loc":["query","workflow_type"],"msg":"Field required"},{"loc":["query","client_id"],...}]}` |
| X2 | `workflowApi.extractInsights` posts transcript in the **body**, but `/workflow/extract-insights` expects **query params** (`workflow.py:109-112`) | Frontend `lib/api.ts:86-87` + Backend `workflow.py` | **P1** | `422 {"detail":[{"loc":["query","transcript"],...},{"loc":["query","client_id"],...}]}` |
| X3 | `marketApi.getNews` builds a URL with **two `?`**: `/market/news?symbols=X?limit=N` (`lib/api.ts:36`) → symbols silently ignored | Frontend `lib/api.ts` | P2 | `GET /market/news?symbols=HSBC?limit=10` → `200` with all 3 unfiltered items |
| X4 | All three "Open Brief" buttons index `rankedClients[0..2]`, which is `[]` at runtime → **`clientId='demo'`** passed to `BriefModal` (`page.tsx:238,255,272`) | Frontend `page.tsx` + Backend `dashboard.py`/`ranking_service.py` | **P0** | Live `my-day` returns `ranked_clients: []`; backend ignores `client_id` anyway |
| X5 | `briefApi.approve('brief-123', …)` hardcodes the brief ID; `edited_agenda` is accepted by the API model but discarded → **RM edits are lost** | Frontend `BriefModal.tsx:77` + Backend `briefs.py:19-22,57-74` | **P1** | Probe: approve with `edited_agenda:"MY EDITED AGENDA"` → `GET` still `status:"draft"`, no agenda field |
| X6 | `GET /clients` (no trailing slash) vs registered `/clients/` → silent 307 redirect on every call | Frontend `lib/api.ts:48` | P3 | `200` after redirect |
| X7 | `start.sh` never creates tables or seeds; `alembic/versions/` is empty → clean start fails | Build/release | **P0** | `grep` of `start.sh` + `main.py` confirms no init hook |
| X8 | Duplicate `CRMService` (`hubspot_service.py`) and duplicate brief UI (`brief/[clientId]/page.tsx`) — Iron Law #1 violation; the approval-aware CRM implementation is the orphaned one | Backend `crm/` + Frontend `app/brief` | P2 | `grep hubspot_service` → no imports |

### 4.5 Global integration checks (my release-gate checklist)

| Check | Result |
|---|---|
| Can the whole system build/start from a clean checkout? | 🔴 **No** — no table creation/seed on startup; no migrations; `init.sql` pgvector risk (§4.1) |
| All P0 features pass integration? | 🔴 **No** — 0/15 P0 FRs implemented; Top 10 returns empty |
| Cross-unit data transfer / state flow works? | 🔴 **No** — brief → gates → CRM/email/memory chain is entirely TODO; no persistence |
| Permission continuity (D0) end-to-end? | 🔴 **No** — no auth at any layer; unguarded external write at `POST /crm/sync` |
| No orphan / unclaimed functionality? | 🔴 **No** — 20 orphan endpoints, 1 dead service, 1 orphan page, 55 unwired fixtures, 5 unused ORM tables |
| Common modules used consistently? | 🔴 **No** — duplicate `CRMService`, duplicate brief UI, two conflicting KPI sources, frontend-provenance vs backend-provenance mismatch (Reuters vs TigerBroker) |
| Exception handling correct in integrated environment? | 🔴 **No** — silent `except: return []`, false `status:"success"`, false `connected`, false `workflow_complete` |
| Test evidence for the integration verdict? | 🔴 **None** — no test suite; verdict rests on direct live probes |

---

## 5. PRD Coverage Map

**Layer legend (the crux of Alan's complaint — used in every row below):**

| Code | Layer | Concrete contents |
|---|---|---|
| **a** | **CSV/JSON demo fixtures** | `demo_data/` — 43 CSV + 12 JSON = 55 data files (+ `README.md`, `checksums.sha256`), 5,695 lines. All rows carry the 8-column C-1 envelope. `demo_data/README.md` states: *"These files are the SPECIFIED OUTPUT SHAPE of a future generator … They are DATA, not a running generator, not application code … No generator, script or executable is included here."* |
| **b** | **Static HTML mockups** | `mockup/` — 9 HTML + `app.js` (277 lines), 6,513 lines. Client-side `AppState` navigation/approvals; no backend. `screens-manifest.md` names 10 screens; **9 of the 10 named HTML files do not exist** (the stated strategy is "All screens in one HTML file"). |
| **c** | **Design specification documents** | `designs/` — **12** markdown files (numbered 00–16 with gaps), 7,361 lines / ~798 KB. Plus root docs: `README.md`, `IMPLEMENTATION_PLAN.md`, `RUNNING.md`, `QUICKSTART.md`, `MARKET_NEWS_AND_LLM.md`, `REVISED_UI_ARCHITECTURE.md`, `SCREEN_ARCHITECTURE_PLAN.md`, `RM_Workbench_MVP_Design_Package.md`, `HUBSPOT_*.md`, `REGISTRATION_GUIDE.md`. |
| **d** | **Real running code** | `backend/app/` (2,631 Python lines), `frontend/` (1,325 TS/TSX lines), `start.sh`, `docker-compose.yml`, `.env` — 3,956 lines total. |

> **Volume contrast:** layers **a + b + c = 19,569 lines** of fixtures, mockups and specs vs **3,956 lines** of real code — roughly **5× more "looks implemented" surface than running implementation**. This is the quantitative root of the complaint.

Statuses use `{Implemented, Partial, Stub, Mock-data-only, Absent}` per the §1 rubric. `d†` denotes code that exists but is **broken at runtime**.

### 5.1 Epic 1 — AI Meeting Intelligence (P0) — 10 items

| ID | Capability | Status | Layers | Evidence (file:line) | One-line justification |
|---|---|---|---|---|---|
| FR-01 | Brief on demand / from calendar / correct client resolution / auth | `Stub` | a,b,c,d | `briefs.py:24-51`; `demo_data/bookings.csv`, `meetings_calendar.csv`; `mockup/system-complete.html` | Hardcodes "Kenneth Wong" regardless of `client_id`; no calendar, no auth, no identity resolution |
| FR-02 | 5 required sections, each source-linked, agenda distinguishable | `Stub` | a,b,c,d | `copilot_service.py:123-151`, `49-84`; `briefs.py:39-41`; `BriefModal.tsx:31-60` | LLM runs on 3 empty lists; live brief says "not provided"; provenance = 5 hardcoded strings; frontend injects fabricated content |
| FR-03 | Partial data / regeneration / feedback / audited versions | `Absent` | a,c | `demo_data/artefacts.json` (`meeting_brief_versions`); `briefs.py:15-17` | `force_regenerate` ignored; no version, no feedback, no per-section status; `Brief` table never written |
| FR-04 | Consent, recording indicator, pause/stop, consent audit | `Stub` | a,b,c,d | `workflow.py:42-60` (`# TODO: Store consent in database with C-4 audit log`); `demo_data/consent_state.csv`, `retell_call.json`, `email_templates.json` (`consent_wording`); `mockup/app.js:176-193` | Echo endpoint; in mockups a JS boolean; no audio, no state, no audit |
| FR-05 | Timestamped speaker-labelled transcript + structured extraction, editable, evidence-linked | `Stub` | a,b,c,d | `workflow.py:108-126`; `copilot_service.py:201-244` (hardcoded `confidence:0.85`); `demo_data/transcript_utterances.csv`, `extraction_items.csv` | Raw transcript string → LLM JSON; no speakers/timestamps/evidence links/editing; frontend contract broken (422) |
| FR-06 | Failure recovery (audio loss, provider failure, no fabricated "complete") | `Absent` | c | `designs/01_Requirements_Specification.md` X-01/X-02/X-05/X-15 | No retry, no last-confirmed position, no recovery state |
| FR-07 | Unified post-meeting review (notes/CRM/tasks/prefs/email/ticket side-by-side) | `Absent` | a,b,c | `demo_data/crm_old_new_preview.csv`, `artefacts.json`; `mockup/system-complete.html`, `rm-workbench-enhanced.html`; `mockup/app.js:195-207` | No such UI in the running frontend; Gate 3 screen exists only as static HTML/JS |
| FR-08 | CRM update + task creation with old/new preview + idempotency | `Stub` | a,b,c,d | `crm.py:16-140`; `crm_service.py:102-166`; `demo_data/crm_sync_log.csv` (idempotency), `crm_tasks.csv`, `crm_opportunities.csv`, `crm_old_new_preview.csv` | Real SDK diff exists but is a bulk contact push (not meeting-driven), has no idempotency keys, is runtime-broken and reports false success |
| FR-09 | Follow-up email draft (draft default, disclosures, RM-attributable send) | `Absent` | a,b,c | `demo_data/email_threads.csv`, `email_messages.csv`, `email_templates.json` (`disclosures`), `demo_sink_messages.csv`; `mockup/rm-workbench-enhanced.html` | Only the string `"email_draft_saved"` in `workflow.py:83`; no draft, no send, no logging |
| FR-10 | Pre-filled trade-ticket handoff gated on suitability | `Absent` | a,c | `demo_data/README.md` ("HARD-BLOCKED — no trade/order table, no execution path"); `designs/01_Requirements_Specification.md:50` | No ticket, no suitability gate (intentionally out of demo scope, but absent from PRD V1.1 delivery) |

### 5.2 Epic 2 — Intelligent Prioritization & Outreach (P0) — 5 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| FR-11 | Daily Top 10, refresh on signals, ≤10, exclusions, last-updated | `Stub` | a,b,c,d† | `ranking_service.py:22-83`; `dashboard.py:18-88`; `demo_data/artefacts.json` (`priority_list_versions`), `market_signals.csv`; `mockup/scr-02-my-day.html` | **Always returns `[]` at runtime** (datetime bug swallowed); no timestamps, no DNC/permission exclusion, no re-rank |
| FR-12 | Reason codes + evidence + rank-change explanation + no protected attributes | `Stub` | a,b,c,d† | `ranking_service.py:203-255`; `demo_data/market_ticks_live.csv`; `mockup/rm-workbench-enhanced.html` (Reason Code Card) | `max()` of 3 scores + 3 static descriptions; hardcoded `"rank.clients v1.2"` evidence chip; no drill-down UI |
| FR-13 | Snooze / dismiss-with-reason / contacted / pin / outcome capture / audit | `Absent` | a,c | `demo_data/audit_events.csv`, `config_versions.csv`; `designs/01_Requirements_Specification.md` MVP-FR-13 | No endpoints, no UI, no persistence; grep confirms `snooze`/`dismiss` absent from backend |
| FR-14 | Grounded outreach draft (reason, portfolio facts, opener, channel/template) | `Absent` | a,b,c | `demo_data/email_templates.json`, `email_messages.csv`; `mockup/rm-workbench-enhanced.html` (Outreach) | No outreach service/endpoint in backend or running frontend |
| FR-15 | DNC / consent / disclosure checks; explicit approval before send; send logging | `Absent` | a,b,c | `demo_data/demo_sink_messages.csv` (`send_count=0`), `approval_tokens.json`; `designs/01_Requirements_Specification.md` MVP-FR-22/23 | No send path, no policy checks, no send log; `DNC` absent from all backend code |

### 5.3 Epic 3 — Enhanced Product Recommendation (P1, depends on D3) — 4 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| FR-16 | NL product search, interpreted correctable filters, entitled products | `Absent` | a,c | `demo_data/products.csv`, `instruments.csv`; `designs/01_Requirements_Specification.md:102` (**explicitly OUT**) | No product model, no endpoint, no query interpreter |
| FR-17 | Result explanation, comparison, ESG attributes, as-of, suitability status | `Absent` | a,c | `demo_data/products.csv` (`shariah_screened_placeholder`), `instruments.csv` | No result surface of any kind |
| FR-18 | Red/Yellow/Green assessment with rule-level justification | `Absent` | a,b,c | `demo_data/suitability_state.csv`; `mockup/index.html` (suitability text); `designs/01_Requirements_Specification.md:103` (**OUT**) | No suitability service/endpoint; `suitability_expiry` appears only in `ranking_service.py:133-139` as a score increment, never a rating |
| FR-19 | Overrides with reason + non-overridable hard stops + compliance audit | `Absent` | a,c | `demo_data/README.md` ("HARD-BLOCKED"); `designs/01_Requirements_Specification.md:103` | No override records, no hard-stop matrix; grep confirms `override`/`hard_stop` absent |

### 5.4 Epic 4 — Islamic Wealth (P1 pilot) — 3 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| FR-4.1 | Shariah preference profile, compliant universe, per-criterion screening, drift | `Stub` | a,c,d | `shariah_service.py:26-70` (`"compliant": True, # Placeholder`); `clients.py:103` (empty business description); `models.py:57`; `demo_data/products.csv`; `designs/01_Requirements_Specification.md:104` (**OUT**) | Every instrument is compliant by construction; no ratio screens, no SSB evidence, no drift alerts |
| FR-4.2 | Zakat / purification, configurable methodology, nisab/hawl, disclaimer | `Stub` | b,c,d | `shariah_service.py:72-122`; `clients.py:120` (hardcoded `"2025-01-01"`); `mockup/index.html` (Zakat) | Flat 2.5% × (Equity+Cash); no nisab, no lunar convention, no purification ratios; disclaimer string present |
| FR-4.3 | Versioned evidence pack, SSB references, finalization gate | `Absent` | c | `designs/01_Requirements_Specification.md:105` (**OUT**) | `generate_shariah_report` returns ad-hoc JSON in the HTTP response; no archive, no version, no gate |

### 5.5 Epic 5 — Family Office (P1/P2 pilot) — 3 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| FR-5.1 | Household/entity graph, entitlements, consolidation, look-through, doc intelligence | `Mock-data-only` | a,b,c,d | `FamilyGraphModal.tsx:22-95` (hardcoded 7 nodes / 6 links); `seed_demo_data.py:83-91` (flat JSONB list); `demo_data/graph_nodes.csv`, `graph_edges.csv`, `graph_source_docs.csv`, `entitlement_matrix.csv`, `entitlement_decisions.csv`; `mockup/rm-workbench-enhanced.html` | Pure front-end graph with invented values summing to 241.0M vs claimed 120.5M; no backend, no entitlement enforcement |
| FR-5.2 | Per-attendee entitled family packs, commitments, succession scenarios | `Absent` | a,b,c | `demo_data/family_packs.json` (`packs`, `diff_result`), `meeting_attendees.csv`; `mockup/screens-manifest.md` | Fixtures describe entitled pack versions; no code produces or delivers them |
| FR-5.3 | Alternatives / capital calls / 90-day liquidity forecasts / Risk reason codes | `Absent` | c | `designs/01_Requirements_Specification.md:106` (**OUT**); PRD FR-5.3 | No commitments table, no notice parsing, no forecasts, no liquidity alerts |

### 5.6 Cross-Cutting FR-20..22 — 3 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| FR-20 | Universal human review with identifiable review state and approver | `Stub` | a,b,c,d | `briefs.py:57-74`; `workflow.py:42-89`; `models.py:22-30,192-209`; `demo_data/approval_tokens.json`, `artefacts.json` (`c2_state_sequence`), `audit_events.csv`; `mockup/app.js:166-207` | Gate endpoints echo "approved"; `ArtefactState`/`AuditEvent`/`WorkflowInstance` never written; non-existent IDs accepted |
| FR-21 | Mobile parity (lookup, briefs, priorities, outreach approval) | `Absent` | c | `designs/01_Requirements_Specification.md:93,108` (**OUT**) | No mobile flows or approvals; desktop-only hardcoded layout |
| FR-22 | Admin config of mappings, ranking policies, templates, consent rules, credentials, versioned+audited | `Absent` | a,c | `demo_data/config_versions.csv`, `version_registry.csv`, `crm_field_mapping.csv`; `designs/01_Requirements_Specification.md` MVP-FR-33/34 | No admin API/UI; only `POST /market/mode` changes anything, in memory |

### 5.7 Foundational Dependencies D0..D5 — 6 items

| ID | Capability | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| D0 | Identity, tenant isolation, RBAC, audit, AI-provider controls | `Absent` | a,c | `demo_data/audit_events.csv`, `rm_books.csv`, `entitlement_matrix.csv`; `designs/01_Requirements_Specification.md:127-149` | No auth code, no User/Role/Tenant model, `SECRET_KEY` unused, `rm_id` an unvalidated query param, zero audit writes |
| D1 | Client, portfolio, CRM, calendar integration | `Partial` | a,c,d | `models.py:33-90`; `clients.py`; `crm_service.py`; `demo_data/clients.csv`, `accounts.csv`, `holdings.csv`, `crm_contacts.csv`, `meetings_calendar.csv` | Real DB reads for 3 seeded clients + HubSpot SDK push; **no calendar, no core banking, no bidirectional CRM** |
| D2 | Consent and recording policy service | `Stub` | a,c,d | `workflow.py:42-60`; `demo_data/consent_state.csv` | Echo endpoint, no policy engine, no persistence, no audio |
| D3 | Entitled market/product data + current KYC/suitability | `Absent` | a,c | `demo_data/products.csv`, `instruments.csv`, `suitability_state.csv`, `market_ticks_*.csv` | Fixtures only; market data in code is fabricated; no entitlement checks |
| D4 | Ranking / outcome telemetry | `Absent` | c | `designs/01_Requirements_Specification.md` (telemetry aggregator SVC-15) | No events, no outcomes, no metrics |
| D5 | Client Memory & Relationship Graph | `Stub` | a,c,d | `models.py:115-139` (`Interaction`), `models.py:50,54` (JSONB blobs); `demo_data/memory_facts.csv`, `graph_nodes.csv` | 2 seeded interaction rows and flat JSONB; no graph tables, no context assembly, no entitlement filtering, no cross-skill reuse |

### 5.8 Boundary & Exception Behaviour B-01..B-12 (§6) — 12 items

| ID | Scenario | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| B-01 | Source unavailable/stale → partial, labelled, never invented | `Stub` | b,c,d | `copilot_service.py:157-175`; `demo_data/feed_status.csv` | Fallback strings exist but no per-section as-of/status; `BriefModal.tsx:31-60` **invents** content |
| B-02 | Conflicting records → flag both, block handoff | `Absent` | c | `designs/01_Requirements_Specification.md` X-08 | No conflict detection |
| B-03 | Consent declined/withdrawn → stop, manual notes, audit | `Stub` | a,b,c,d | `workflow.py:55-56`; `mockup/app.js:185-193` | A `consent_given=False` branch returns a string; nothing stops/persists/audits |
| B-04 | Low confidence / insufficient evidence → label + review + suppress | `Absent` | c | `copilot_service.py:236` (hardcoded `0.85`) | Confidence is a constant, not a signal |
| B-05 | CRM/email/SMS outage → pending/failed, idempotent retry, no false success | `Absent` | a,c | `crm.py:77-83`; `demo_data/vendor_health.csv` | Code returns `status:"success"` with 3 errors — **the opposite** |
| B-06 | No high-priority clients → honest empty state | `Stub` | b,c,d† | `dashboard.py:70-77`; `mockup/DESIGN_STRATEGY.md` CMP-15 | API returns `[]` **because of a bug**, but no criteria/last-evaluation UI; the dashboard shows 4 hardcoded actions anyway |
| B-07 | DNC / channel opt-out → exclude + block send | `Absent` | a,c | `demo_data/consent_state.csv` | No DNC logic anywhere |
| B-08 | No suitable product → no-result explanation, no auto-relaxation | `Absent` | c | — | No product search |
| B-09 | Suitability missing/expired → Yellow at best, block handoff | `Absent` | a,c | `demo_data/suitability_state.csv` | No suitability rating or handoff |
| B-10 | Model/service failure → manual fallback, status, preserve edits | `Stub` | c,d | `copilot_service.py:89-91,153-155`; `ranking_service.py:81-83` | Fallback exists but is **silent** and RM edits are discarded (`edited_agenda` unused) |
| B-11 | Shariah-sensitive client, non-compliant candidate → exclude by construction | `Absent` | a,c | `shariah_service.py:37` | Everything is marked compliant → cannot exclude |
| B-12 | Intra-family entitlement boundary → context-level filtering | `Absent` | a,b,c | `demo_data/entitlement_decisions.csv`, `family_packs.json` | Fixtures describe decisions; no filtering in code |

### 5.9 Non-Functional Requirements NFR-01..11 (§7) — 11 items

| ID | Area | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| NFR-01 | Performance (brief <10s p95, search <5s p95) | `Absent` | c | `designs/03_Technical_Solution.md` | Live LLM call unbounded; no latency measurement/SLO |
| NFR-02 | Scale (1,000 concurrent users, tenant isolation) | `Absent` | c | `database.py:15-22` (pool 10/20) | No load test, no tenant isolation |
| NFR-03 | Availability 99.5%, graceful degradation | `Stub` | c,d | `main.py:44-54`; `copilot_service.py:89-91`; `market_service.py:69-71` | try/except fallbacks exist but health endpoint lies and failures are silent |
| NFR-04 | Security (SOC 2, TLS, RBAC, secrets, session timeout) | `Absent` | c | `config.py:9` (unused `SECRET_KEY`); `.env:26` (`demo_secret_key_for_development_change_in_production`) | No auth, no TLS enforcement, plaintext dev secret committed |
| NFR-05 | Privacy / residency / retention / legal hold | `Absent` | c | `.env:21-23`; `copilot_service.py:140-148` | Client name/AUM/transcript sent to third-party `cc-vibe.com`; no residency/retention controls |
| NFR-06 | Auditability (immutable logs for consent, approvals, writes, overrides) | `Stub` | a,c,d | `models.py:192-209`; `demo_data/audit_events.csv` | `AuditEvent` table declared; **zero writes** |
| NFR-07 | AI explainability (source + timestamps + rationale) | `Stub` | a,b,c,d | `copilot_service.py:49-84`; `BriefModal.tsx:39-58` | Hardcoded source names and browser-clock timestamps; no record links |
| NFR-08 | Mobile | `Absent` | c | `page.tsx` (fixed 1920px grid) | Explicitly out of demo scope; no mobile controls |
| NFR-09 | Accessibility WCAG 2.1 AA | `Absent` | c | `mockup/DESIGN_STRATEGY.md:514-524` | Design-only; running UI uses colour-only status chips and hardcoded text |
| NFR-10 | Observability (correlated technical/AI/business telemetry) | `Absent` | a,c | `demo_data/vendor_health.csv`, `feed_status.csv` | Only uvicorn access logs; no telemetry emission |
| NFR-11 | Recoverability (backup/DR, no lost accepted writes) | `Absent` | c | `docker-compose.yml:11` (volume only) | No backup/DR objectives, no idempotent retry, no outbox |

### 5.10 AI Governance GOV-01..08 (§8) — 8 items

| ID | Control | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| GOV-01 | Human-in-the-loop on all external/writing actions | `Stub` | a,b,c,d | `workflow.py:62-89`; `crm.py:16-18` | Gates cosmetic; `POST /crm/sync` is an **unguarded external write** |
| GOV-02 | Zero provider retention / training | `Absent` | c | `.env:22`; `copilot_service.py:140-148` | Third-party proxy, no contract/DPA evidence, no prompt minimisation |
| GOV-03 | Grounding & explainability (faithful, not rationalisations) | `Stub` | a,c,d | `copilot_service.py:49-84` | Provenance claims sources that were never queried — **unfaithful** |
| GOV-04 | Override & feedback with structured reasons | `Absent` | a,c | `demo_data/audit_events.csv` | No override/feedback mechanism |
| GOV-05 | Model/prompt/template/rule-pack versioning + rollback | `Absent` | a,c | `demo_data/config_versions.csv`, `version_registry.csv`; hardcoded `"v1.2"` in `copilot_service.py:52,80`; `"rank.clients v1.2"` in `ranking_service.py:250` | Version labels are literal strings, not a registry |
| GOV-06 | Compliance ownership / jurisdictional approvals | `Absent` | c | — | No compliance artefacts |
| GOV-07 | Monitoring + kill switch | `Absent` | a,c | `demo_data/vendor_health.csv` | `kill_switch` absent from all backend code |
| GOV-08 | Fairness & data minimisation | `Absent` | c | `ranking_service.py` | No protected-attribute check, no monitoring, no data-minimisation policy |

### 5.11 Integration Requirements INT-01..11 (§9) — 11 items

| ID | System | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| INT-01 | Core banking (identity, households, accounts) | `Absent` | a,c | `demo_data/clients.csv`, `accounts.csv` | No integration; 3 seeded rows only |
| INT-02 | Portfolio management (holdings, allocation, performance, risk) | `Stub` | a,c,d | `clients.py:64-83`; `models.py:69-90` | Real holdings read; no aggregation, no stale/conflict labelling |
| INT-03 | Market data (prices, news, entitlements, attribution) | `Stub` | a,c,d | `market_service.py:38-113`; `demo_data/market_ticks_live.csv`, `news_items.csv`, `feed_status.csv` | Fabricated data labelled `live_feed`/`TigerBroker`; no entitlements, no attribution |
| INT-04 | CRM (bidirectional, field mapping, old/new preview, idempotent writes, sync status) | `Partial` | a,c,d | `crm_service.py:102-166`; `crm.py`; `demo_data/crm_field_mapping.csv`, `crm_sync_log.csv`, `crm_old_new_preview.csv`, `crm_tasks.csv` | Real SDK + diff, but one-way bulk push, broken at runtime, no idempotency, false status |
| INT-05 | Calendar (Outlook/Google, attendee resolution) | `Absent` | a,b,c | `demo_data/meetings_calendar.csv`, `meeting_attendees.csv`; `page.tsx:229-285` | Schedule hardcoded in JSX |
| INT-06 | Email/SMS draft handoff + RM-approved send | `Absent` | a,b,c | `demo_data/email_messages.csv`, `demo_sink_messages.csv`, `email_templates.json` | No send path |
| INT-07 | Product / suitability source | `Absent` | a,c | `demo_data/products.csv`, `instruments.csv`, `suitability_state.csv` | Fixtures only |
| INT-08 | Shariah rule/source data (versioned SSB rule packs) | `Stub` | a,c,d | `shariah_service.py:39,51,175` (hardcoded `"AAOIFI Standard"`) | Static label, no versioned rule packs |
| INT-09 | Custodian / entity sources (multi-custodian, per-node entitlements) | `Mock-data-only` | a,b,c,d | `FamilyGraphModal.tsx:22-95`; `demo_data/graph_*.csv`, `entitlement_matrix.csv`, `family_packs.json` | Hardcoded graph, no feeds, no reconciliation, no entitlements |
| INT-10 | Identity / administration (SSO, role, book assignment, tenant policy) | `Absent` | a,c | `demo_data/rm_books.csv` | No server-side authorization |
| INT-11 | Freshness SLAs, API limits, authoritative-source ownership | `Absent` | a,c | `demo_data/vendor_health.csv`, `feed_status.csv` | Fixtures describe it; no code implements it |

### 5.12 Success Metrics M-01..10, Telemetry TEL-01..10, Guardrails GRD-01..10, Release Gates GATE-01..04+X

| Group | Items | Status | Layers | Evidence | One-line justification |
|---|---|---|---|---|---|
| M-01..M-10 (§10.1) | 10 | `Absent` (all) | a,c | `demo_data/manifest_v1.3.json`, `integrity_report.json` | No instrumentation for prep time, adoption, touchpoints, orchestration rate, retention, etc. |
| TEL-01..TEL-10 (§10.2) | 10 | `Absent` (all) | a,c | `demo_data/audit_events.csv`, `workflow_stages.csv`, `demo_sink_messages.csv` | No `brief_requested`, `consent_shown`, `crm_update_approved`, `suitability_rating`, `copilot_workflow_*` or any other event is emitted; no correlation ID plumbing (the one `8f21a4b2` is a hardcoded literal at `dashboard.py:80`) |
| GRD-01..GRD-10 (§10.3) | 10 | `Absent` (all) | a,c | `demo_data/integrity_report.json` (zero counters) | Several guardrails hold only **trivially** because the capability does not exist (no sends, no trades) — absence of a feature is not an implemented monitoring control. Conversely, provenance/consent/compliance guardrails are actively violated |
| GATE-01..04 + GATE-X (§11) | 5 | `Absent` (all) | c | `designs/04_Feature_Unit_Plan.md:425-513` (pre-flight, G1…G11, OD-1…11 go/no-go) | No security/residency sign-off, no compliance approval, no SSB sign-off, no pilot cohorts, no test sets, no feature flags, no entitlement leakage tests |

---

## 6. The Four Layers — Explicit Separation (CRITICAL)

Alan's complaint is that things "look implemented" when they are only fixtures or design docs. Here is the hard separation.

| Layer | Path | Volume | What it is | What it is **NOT** | Wired to runtime? |
|---|---|---|---|---|---|
| **(a) CSV/JSON demo fixtures** | `demo_data/` | 43 CSV + 12 JSON = 55 data files, 5,695 lines | Static, labelled, synthetic **data rows** describing a *future* seeded world: `cl_wong_001` IDs, `SYN-` symbols, `@demo.invalid` emails, 8-column C-1 provenance envelope, approval tokens, idempotency keys, entitlement matrices, graph edges, workflow stages, audit events, `integrity_report.json` | Not a generator, not code, not DDL, not a migration. `demo_data/README.md` says so verbatim: *"They are DATA, not a running generator, not application code … No generator, script or executable is included here."* | ❌ **ZERO references** from `backend/app/**` or `frontend/**`. The DB is seeded from **hardcoded Python literals** in `seed_demo_data.py:35-178` using a **completely different ID scheme** (`RM001-C001`, `0005.HK`, `example.com`) — the fixtures and the running DB are incompatible datasets |
| **(b) Static HTML mockups** | `mockup/` | 9 HTML + `app.js` = 6,513 lines | Clickable, self-contained SPA mockups with `AppState`, `navigateTo()`, `approveBrief()`, `acceptConsent()`, `approveReview()`, toasts, drawers, Gate 1/2/3 screens, consent banners, outreach, audit viewer, family graph, Zakat/suitability/reason-code surfaces | Not React, not connected to the API, not persisted. Approvals are `AppState.briefApproved = true` + a `setTimeout` toast (`app.js:166-207`). `screens-manifest.md` names 10 screens; 9 of the 10 named HTML files do not exist (the stated strategy is "All screens in one HTML file") | ❌ No `fetch()`/axios; served as static files, never imported by `frontend/` |
| **(c) Design specification documents** | `designs/` (12 md, 7,361 lines / ~798 KB) + root docs | ~700+ KB | `01_Requirements_Specification.md` (34 `MVP-FR-xx` for a **"Leadership Demo"**, explicitly a *reduced scope*), `02_Product_Design_Specification.md`, `03_Technical_Solution.md` (18 services SVC-01…18), `04_Feature_Unit_Plan.md` (24 `FU-xx` units, G1…G11 acceptance, OD-1…11 go/no-go), data-enhancement briefs 10…16; plus README/IMPLEMENTATION_PLAN/RUNNING/QUICKSTART/MARKET_NEWS_AND_LLM/architecture docs | Not executable. `04_Feature_Unit_Plan.md:669` states: *"It contains no application code, no runnable scripts, no executed DDL, no scaffold, no test files … All design work stops before any build."* `designs/16_Executive_One_Pager.md` states *"No code exists today. Authorising a build is a separate, explicit decision."* | ❌ The specs define C-1…C-5 contracts, 18 services, 24 feature units, 14 screens, RLS, outbox, idempotency, kill masks — **none of which exist in `backend/app/`** |
| **(d) Real running code** | `backend/app/` + `frontend/` + `start.sh` + `docker-compose.yml` + `.env` | 3,956 lines | FastAPI with 25 `/api/v1` routes, 5 active services (+1 dead duplicate), 7 ORM tables, 2 Next.js routes, 4 components, 1 API client; boots on ports 8000/3000 with a real Postgres container and a live LLM proxy | Not the PRD, not the design spec, not the fixtures | ✅ This is the only layer that actually executes |

### 6.1 Layer matrix — where each headline capability exists

| Capability | (a) Fixtures | (b) Mockups | (c) Design docs | (d) Running code | What a reviewer actually sees |
|---|---|---|---|---|---|
| Live market feed, entitlements, attribution | ✅ `market_ticks_live.csv`, `news_items.csv`, `feed_status.csv` | ✅ "LIVE" chips | ✅ MVP-FR-01…04 marked **REAL** | ❌ `hash()` mock labelled `TigerBroker` | "Implemented" — actually **mock** |
| Daily Top 10 + reason codes + RM controls | ✅ `artefacts.json` (`priority_list_versions`), `market_signals.csv` | ✅ `scr-02-my-day.html`, Reason Code Card | ✅ MVP-FR-11…13 | ⚠️ `ranking_service.py` **returns `[]`** | "Implemented" — actually **empty** |
| Three approval gates / approval tokens / artefact states | ✅ `approval_tokens.json`, `artefacts.json` (`c2_state_sequence`), `audit_events.csv` | ✅ Gate 1/2/3 screens, `approveReview()` | ✅ C-2/C-3/C-4 contracts | ⚠️ 3 echo endpoints, zero writes | "Implemented" — actually **cosmetic** |
| Post-meeting CRM/email/ticket automation | ✅ `crm_old_new_preview.csv`, `crm_sync_log.csv`, `crm_tasks.csv`, `email_messages.csv`, `email_templates.json`, `demo_sink_messages.csv` | ✅ Gate 3 "CRM updates queued" toast | ✅ MVP-FR-18…23 | ❌ absent (one fake string `"email_draft_saved"`) | "Implemented" — actually **absent in code** |
| Outreach drafts + approved send | ✅ `email_templates.json`, `demo_sink_messages.csv` (`send_count=0`) | ✅ Outreach screen | ✅ MVP-FR-22/23 | ❌ absent | "Implemented" — actually **absent in code** |
| NL product search + R/Y/G suitability + hard stops | ✅ `products.csv`, `instruments.csv`, `suitability_state.csv` | ⚠️ suitability/zakat text | ✅ PRD Epic 3; **explicitly OUT** in demo spec §2.3 | ❌ absent | "Specified" — **never built** (and out of demo scope by design) |
| Shariah screening / zakat / evidence pack | ✅ `products.csv` (`shariah_screened_placeholder`) | ✅ Zakat mentions in 7 HTML | ✅ §2.3 **OUT** | ⚠️ placeholder that returns `compliant: True` for everything | "Implemented" (README) — actually a **false compliance label** |
| Household graph / per-node entitlements | ✅ `graph_nodes.csv`, `graph_edges.csv`, `graph_source_docs.csv`, `entitlement_matrix.csv`, `entitlement_decisions.csv`, `family_packs.json` | ✅ family graph screen | ✅ MVP-FR-06, FR-24 | ⚠️ hardcoded ECharts with no reconciliation | "Implemented" — actually a **hardcoded picture** |
| Provenance envelope / audit chain / version registry | ✅ 8-column C-1 envelope on every CSV row, `audit_events.csv`, `config_versions.csv`, `version_registry.csv`, `integrity_report.json` | ✅ evidence chips CMP-01, source drawer CMP-02, audit table CMP-12 | ✅ C-1/C-4, FU-02/FU-04/FU-06 | ❌ no envelope, no audit writes, hardcoded `"v1.2"` strings | "Implemented" — actually **design + fixtures only** |
| Copilot orchestration / skills / closed loop | ✅ `workflow_instances.csv`, `workflow_stages.csv`, `memory_facts.csv` | ✅ workflow stage trace in header | ✅ SVC-06/07/08, FU-11…14, 12 typed skills | ⚠️ `orchestrate_workflow()` returns `stages: []` | "Implemented" — actually a **static dict** |
| Telemetry / observability / kill switch | ✅ `vendor_health.csv`, `feed_status.csv`, `demo_sink_messages.csv` | ✅ health footer SCR-10 | ✅ SVC-15, FU-15, FR-10 kill mask | ❌ no events, no kill switch | "Specified" — **never built** |

### 6.2 The systemic failure mode

Three separate "worlds" were built and never joined:

1. The **fixture world** (a) is a coherent, internally-validated synthetic dataset with its own manifest, checksums (`checksums.sha256`), integrity report and zero counters.
2. The **design world** (c) is a coherent, detailed engineering spec for a leadership demo (34 FRs, 24 feature units, 18 services, 14 screens, C-1…C-5 contracts).
3. The **running code** (d) is a **third, independent** implementation that follows neither: it invents its own IDs, its own 3-client seed, its own "Sarah Chen / Kenneth Wong" copy, its own hardcoded gate responses and its own mock market data.

The README then describes world (c)/(a) as if it were world (d). **Nothing in `backend/app/` reads `demo_data/`; nothing in `frontend/` reads `mockup/`; nothing implements `designs/` contracts.** That is why the project "looks implemented". Notably, layers (a) and (c) are themselves *honest* about being design artefacts — it is the README/marketing layer that mislabels them.

---

## 7. Coverage Percentages and Final Verdict

### 7.1 Coverage by category (authoritative 111-item inventory from `deliverables/01_PRD_Requirement_Inventory.md`)

| # | Category | Items | Weighted score | Coverage |
|---|---|---:|---:|---:|
| 1 | Functional — Epic 1 (FR-01…10, P0) | 10 | 1.25 | **12.5%** |
| 2 | Functional — Epic 2 (FR-11…15, P0) | 5 | 0.50 | **10.0%** |
| 3 | Functional — Epic 3 (FR-16…19, P1) | 4 | 0.00 | **0.0%** |
| 4 | Functional — Cross-Cutting (FR-20…22) | 3 | 0.25 | **8.3%** |
| 5 | Functional — Epic 4 (FR-4.1…4.3) | 3 | 0.50 | **16.7%** |
| 6 | Functional — Epic 5 (FR-5.1…5.3) | 3 | 0.15 | **5.0%** |
| 7 | Foundational Dependencies (D0…D5) | 6 | 1.00 | **16.7%** |
| 8 | Boundary / Exception (B-01…B-12) | 12 | 1.00 | **8.3%** |
| 9 | Non-Functional Requirements (NFR-01…11) | 11 | 0.75 | **6.8%** |
| 10 | AI Governance (GOV-01…08) | 8 | 0.50 | **6.2%** |
| 11 | Integration Requirements (INT-01…11) | 11 | 1.40 | **12.7%** |
| 12 | Success Metrics (M-01…10) | 10 | 0.00 | **0.0%** |
| 13 | Required Telemetry (TEL-01…10) | 10 | 0.00 | **0.0%** |
| 14 | Guardrails (GRD-01…10) | 10 | 0.00 | **0.0%** |
| 15 | Phased Rollout Gates (GATE-01…04 + X) | 5 | 0.00 | **0.0%** |
| | **OVERALL** | **111** | **7.30** | **6.6%** |
| | *Functional requirements only (28)* | 28 | 2.65 | **9.5%** |
| | ***P0 only (15 FRs) — PRD release gate*** | 15 | 1.75 | **11.7%** |

**Status distribution across 111 items:** `Implemented 0` · `Partial 2` (D1, INT-04) · `Stub 24` · `Mock-data-only 2` (FR-5.1, INT-09) · `Absent 83`.

**Scoping caveat (req-analyst §12.2 Tier A/B/C/D, applied):** the 6.6% figure is an unweighted audit of **all** 111 frozen IDs, not a claim that every item is a GA blocker. Under the PRD's own release policy, the Tier A core/P0 set is FR-01…15 + FR-20/FR-22 + D0/D1/D2/D4/D5 (Tier A = 11.7% P0 coverage above, still a hard FAIL); Epic 3 (FR-16…19, D3) is Tier B ("must not delay P0 launch"); Epics 4/5 pilots, B-11/B-12, INT-08/09 and the v1.1 telemetry/guardrail extensions are Tier C ("roll into V2"); §12 out-of-scope, §1.5 non-goals, §14 open decisions and §13 risks are Tier D and were **not** counted as gaps here. **The 0%-fully-implemented verdict survives every scope cut**: 0 of the 15 P0 FRs, 0 of the 22 core GA FRs, 0 of all 28 FRs satisfy their AC. Per the PRD front matter, numeric success targets (45→10 min, 60% adoption, ≥70% orchestration, <10s/<5s p95, 1,000 users, 99.5% uptime, +15–20% retention, 100% Shariah coverage, −70% family reporting effort) are **planning assumptions, not observed facts**; this audit tests whether the *measurement path* (metric definitions + TEL-01…10 telemetry) exists — it does not — and does not score whether a target number was hit. M-08/M-10 require baselines first. Behavioural ACs ("source-linked", "idempotent", "auditable", "before explicit confirmation", "blocks on stale data") were scored against behaviour, not against the presence of a screen/field: e.g. FR-02 is `Stub` rather than `Implemented` because the market-news section exists but carries a fabricated `LIVE_FEED / "TigerBroker News"` label over `market_signals = []` (`briefs.py:40`, `copilot_service.py:71-76`), which is a false provenance claim, not provenance; FR-03 is `Absent` because the fallback says "unavailable" while the badge says LIVE, so the state is not unambiguously unavailable (also B-01, B-04, INT-03, GOV-03, NFR-07, TEL-01).

**Alternative grouping (75 capability items, coarser):** overall **8.4%**; Epic 1 12.5%, Epic 2 10.0%, Dependencies 16.7%, Integrations 14.0%, NFRs 6.8%, AI Governance 6.2%, Telemetry/Rollout 0.0%. The two computations agree within ~2 points; I cite **6.6%** as the headline because it uses the team's authoritative 111-item inventory.

**Complementary runtime-surface metrics (not requirement coverage, but honest about "how much works"):**

| Metric | Value |
|---|---|
| Routes returning genuine DB data | 3 / 25 = 12% |
| Routes making a real external LLM call | 2 / 25 = 8% |
| Routes that are hardcoded / mock / echo | 16 / 25 = 64% (17 / 25 = 68% incl. the stub Shariah report) |
| Routes reachable from the frontend | 5 / 25 = 20% |
| ORM tables written by any endpoint | 0 / 7 |
| PRD capabilities existing **only** in layers (a)/(b)/(c) | ≥ 40 / 111 |

### 7.2 Final verdict

> ### 🔴 **Verdict: NOT DELIVERABLE — "UI mockup with a thin, largely read-only API"**
> **Conclusion (integration acceptance): 未完成，需修复 (Development not complete; must be fixed before delivery).**

Precisely, among the three candidate labels:

- **Production system?** ❌ **No.** No authentication, no RBAC, no tenant isolation, no audit logging, no tests, no migrations, no telemetry, no policy checks, no error honesty, no data provenance, hardcoded secrets, an unvetted third-party LLM receiving client context, and a P0 ranking path that silently fails. It fails every PRD §7 NFR and every §11 release gate.
- **Functional demo prototype?** ⚠️ **Only in the narrowest sense.** The stack boots, renders a polished dashboard, reads 3 real DB clients, calls a real LLM, and can be clicked through a 5-section brief modal. But **none of the four PRD core workflows closes end-to-end** (§4.3). Even against the much smaller "Leadership Demo" design spec (`designs/01`), the items it declares **REAL** — live market feed, provenance chips, audit writes, approval gates, re-rank, mode switch — are all mocked/echo/broken in code.
- **UI mockup with a thin read-only API?** ✅ **This is the accurate label.** 3 read-only DB endpoints, 2 LLM calls, and 20 endpoints that are hardcoded constants or echo stubs over a largely static React dashboard, with a much richer parallel universe of 55 CSV/JSON fixtures, 9 HTML mockups and 12 design specs that were never connected.

**Per the PRD's own release policy (§4.1 line 108): "Epic 1 and Epic 2 are P0 for V1"** and per my integration rule (100% P0 required), **P0 coverage is 11.7%, therefore the project cannot be declared development-complete.** This verdict is not a judgement about effort — it is a statement that the four layers were never integrated.

**Reconciliation with the team-lead's compilation (now consolidated in `GAP_ANALYSIS_RM_WORKBENCH.md`):** the team-lead's independent compilation reaches the same factual findings (3 real routes, mocked market data, cosmetic gates, no auth, unwired fixtures, broken HubSpot) but frames the verdict as a *"functional demo prototype with a thin, largely hardcoded API"* and reports **0 of 28 FRs fully implemented / 43% code-trace coverage (partial + stub)**. Both numbers are honest and compatible: theirs measures "is there any code trace at all" across the 28 FRs, mine weights acceptance-criteria completion across all **111** requirements (28 FRs + 83 dependencies/NFRs/governance/integrations/telemetry/gates). The consolidated report should cite **both with the denominator stated**. The only substantive difference in classification is emphasis: I place the system in the "UI mockup with thin API" category because 68% of endpoints return hardcoded/echo data and the four PRD workflows do not close; the lead's "functional demo prototype" label is defensible if the baseline is the reduced *Leadership Demo* spec rather than PRD V1.1.

---

## 8. The 10 Biggest Gaps (ordered by severity)

| # | Gap | Severity | Owner unit (for return) | Evidence |
|---|---|---|---|---|
| 1 | **D0 is entirely absent** — no authentication, RBAC, tenant isolation, audit logging, or write protection. `rm_id` is an unvalidated query param; `POST /crm/sync` is an unguarded external write. | **P0 blocker** | Backend foundation / `main.py`, `core/`, all endpoints | `main.py:20-33`; `config.py:9` (unused `SECRET_KEY`); `models.py:192-209` (never written) |
| 2 | **P0 Daily Top 10 silently returns empty.** `ranking_service.rank_clients` throws a datetime error on every call, swallows it, returns `[]`; `/my-day` returns HTTP 200 with `ranked_clients: []` and `priority_actions: []`. | **P0 blocker** | `services/ranking/ranking_service.py:178-179,81-83`; `endpoints/dashboard.py` | `backend.log:67,115,167,215,295,348,458,511,568,621,675` |
| 3 | **The three approval gates are fake.** Approve non-existent IDs → 200 `"approved"`; state never persists; Gate 3 claims `crm_sync`/`d5_memory_update`/`email_draft_saved` executed when all three are TODOs. Violates FR-07/08/20 and "never show false success". | **P0 blocker** | `endpoints/briefs.py:57-74`, `endpoints/workflow.py:42-89` | Live probes §4.3 steps 6-10 |
| 4 | **Four-layer disconnect** — 43 CSV + 12 JSON fixtures, 9 HTML mockups and 12 design specs exist with rich capability shapes, but **zero** are wired to code; the running DB uses an incompatible hardcoded seed. This is the root cause of "looks implemented". | **P0 systemic** | Build/release + all units | `grep demo_data backend/app frontend` → no matches; `demo_data/README.md:17-21`; `seed_demo_data.py:35-93` |
| 5 | **Tiger Broker "real-time" market data is 100% fabricated** and labelled `live_feed` / `TigerBroker` / `● LIVE`; news URLs point to `example.com`; the UI prints a different fake source (`Reuters`). Provenance is actively misleading. | **P0 (trust)** | `services/market/market_service.py`; `frontend/app/page.tsx:294-311` | `market_service.py:41,46,51,89`; README:178 |
| 6 | **Brief generation runs a live LLM over empty context** — `portfolio_data=[]`, `market_signals=[]`, `interaction_history=[]`; hardcodes the client; the UI then fabricates interactions/news with invented confidence scores. FR-02 (5 sourced sections) is not met. | **P0** | `endpoints/briefs.py:31-45`; `components/BriefModal.tsx:31-60`; `services/copilot/copilot_service.py:49-84` | Live probe §4.3 step 5 |
| 7 | **Entire Epic 2.2 (outreach drafts + policy checks + approved send), Epic 3 (NL search + R/Y/G suitability + hard stops) and Epic 1.3 (post-meeting automation) are absent from running code** — they exist only as fixtures/mockups/specs. | **P0/P1** | Epic 1.3, 2.2, 3 units (unclaimed) | `grep DNC\|suitability\|outreach\|override\|hard_stop backend/app` → absent; `designs/01_Requirements_Specification.md:102-106` explicitly defers them |
| 8 | **Clean-start build is broken** — `start.sh` never creates tables or seeds; `alembic/versions/` is empty; `main.py` has no startup hook; `init.sql` requests a pgvector extension the chosen image may not ship. A fresh clone produces 500s on every DB endpoint. | **P0 (release)** | Build/release: `start.sh`, `backend/init.sql`, `backend/alembic/`, `main.py` | `start.sh:45-59`; `find backend/alembic -type f` → only `env.py` |
| 9 | **Frontend↔backend contract drift + duplicate implementations** — `workflow/start` and `workflow/extract-insights` return 422 for the frontend's own payloads; `marketApi.getNews` builds a malformed URL; dashboard brief buttons pass `clientId='demo'`; duplicate `CRMService` and duplicate brief page; 20 of 25 endpoints orphaned. | **P1** | `frontend/lib/api.ts`, `frontend/app/page.tsx`, `backend/app/api/v1/endpoints/workflow.py`, `services/crm/hubspot_service.py`, `app/brief/[clientId]/page.tsx` | Live 422 probes §4.4; Iron Law #1 violation |
| 10 | **No tests, no telemetry, no governance** — 0 test files; all three README test commands are non-functional; no `brief_requested`/`consent_shown`/`suitability_rating`/override events; `AuditEvent`/`WorkflowInstance`/`Brief`/`MarketTick` tables never written; no model/prompt versioning; no kill switch; client data sent to third-party `cc-vibe.com` with no zero-retention controls. | **P1 / release gate** | Cross-cutting (all units) + §8/§10/§11 | `find . -name 'test_*'` → 0 app tests; `backend/app` telemetry grep → none; `.env:21-23` |

---

## 9. Integration Acceptance View (release-engineer sign-off)

### 9.1 End-to-end business-flow verification (PRD §2.2)

| Core workflow | Units involved | Expected | Actual (live probe) | Conclusion |
|---|---|---|---|---|
| **Prepare → meet → follow up** (calendar → brief → consent → notes → approved CRM/email/ticket) | `dashboard`, `briefs`, `workflow`, `copilot`, `crm`, frontend | Sourced 5-section brief; persisted consent; reviewed notes; CRM update + email draft + ticket with approver and audit | Brief from empty context; gates echo and persist nothing; no notes/CRM/email/ticket artefacts; `edited_agenda` silently dropped | 🔴 **FAIL** |
| **Prioritize → converse** (Top 10 → reason/evidence → client detail → outreach → approved send) | `ranking`, `dashboard`, frontend | ≤10 ranked clients with reason codes, evidence drill-down, editable draft, blocked/approved send + logging | `ranked_clients: []`; no reason UI; no outreach endpoint; no send path; 4 hardcoded "Priority Actions" with no handlers | 🔴 **FAIL** |
| **Discover → assess** (NL query → filters → results → R/Y/G → RM decision + audit) | (no units) | Entitled products, suitability rating, overrides/hard stops | No endpoints, services, models or UI | 🔴 **FAIL (absent)** |
| **Serve new needs** (Shariah / household through the same copilot skills) | `shariah`, frontend graph | Preference-aware screening, zakat, evidence pack, permissioned graph | Always-compliant placeholder; flat 2.5% zakat; hardcoded ECharts graph with no entitlements | 🔴 **FAIL** |
| **Closed loop** (meeting outcomes → ranking → next briefs → memory) | `copilot`, `ranking`, `models` | One `correlation_id`, stage trace, context reuse, re-rank | `correlation_id` is the literal `"8f21a4b2"`; `stages: []`; no memory writes; no re-rank | 🔴 **FAIL** |

### 9.2 Integration problem list with ownership

| # | Problem | Attributed unit | Severity | Status |
|---|---|---|---|---|
| INT-01 | Ranking returns `[]` due to naive/aware datetime subtraction; error swallowed | `services/ranking/ranking_service.py` | P0 | Open — return to unit |
| INT-02 | Gates do not persist; accept non-existent IDs; Gate 3 false `actions_executed` | `endpoints/briefs.py`, `endpoints/workflow.py`, `models.py` writers | P0 | Open — return to unit |
| INT-03 | Brief context empty; client hardcoded; provenance fabricated | `endpoints/briefs.py`, `services/copilot/copilot_service.py`, `components/BriefModal.tsx` | P0 | Open — return to unit |
| INT-04 | Market data fully mocked but labelled live; mode switch is a no-op | `services/market/market_service.py`, `frontend/app/page.tsx` | P0 | Open — return to unit |
| INT-05 | No auth/RBAC/tenant/audit; unguarded `POST /crm/sync` | `main.py`, `core/config.py`, all endpoints | P0 | Open — return to foundation unit |
| INT-06 | False success/health: `/health`, `/crm/status`, `POST /crm/sync`, Gate 3 | `main.py`, `endpoints/crm.py`, `services/crm/crm_service.py`, `endpoints/workflow.py` | P0 | Open — return to unit |
| INT-07 | Frontend/backend contract mismatches (422 ×2, malformed news URL, `'demo'` client IDs, lost edits) | `frontend/lib/api.ts`, `frontend/app/page.tsx`, `endpoints/workflow.py`, `endpoints/briefs.py` | P1 | Open — return to unit |
| INT-08 | Duplicate `CRMService`, duplicate brief UI, dead API client groups, 20 orphan endpoints, 5 unused ORM tables | `services/crm/`, `frontend/app/brief/`, `frontend/lib/api.ts` | P2 / Iron Law #1 | Open — return to unit |
| INT-09 | Clean start has no table creation/seed/migration | `start.sh`, `main.py`, `backend/alembic/`, `backend/init.sql` | P0 | Open — return to release unit |
| INT-10 | `demo_data/` (55 data files), `mockup/` (9 HTML), `designs/` (12 specs) never wired to code | Integration / all units | P0 systemic | Open — return to team lead for scope decision |

### 9.3 Global checks

| Check | Result |
|---|---|
| All P0 implemented? | 🔴 **No** — 0/15 P0 FRs implemented; 11.7% weighted |
| 100% completion required for delivery? | 🔴 **Not met** — verdict is "not complete" |
| No orphan / unclaimed functionality? | 🔴 **No** — 20 orphan endpoints, 1 dead service, 1 orphan page, 55 unwired fixtures |
| Common modules used consistently? | 🔴 **No** — duplicate CRM service, duplicate brief UI, conflicting KPI sources, conflicting provenance labels |
| Builds and starts cleanly? | 🔴 **No** — no startup init/seed; no migrations |
| End-to-end genuinely run? | ✅ **Yes, this audit ran it** — and it fails (§4.3) |
| Test suite exists? | 🔴 **No** |
| Integration problems attributed to a concrete unit? | ✅ **Yes** (§9.2) |
| Scope reduction applied to hide gaps? | ✅ **No** — no feature was removed or reclassified; all PRD capabilities audited as-is |

### 9.4 Delivery checklist

| Deliverable | Path | Status |
|---|---|---|
| 01 · PRD requirement inventory (requirements side) | `deliverables/01_PRD_Requirement_Inventory.md` | ✅ Written (req-analyst) |
| **02 · Implementation feature completeness audit (this report)** | **`deliverables/02_Implementation_Feature_Audit.md`** | ✅ **Written** |
| 02-L · Team-lead independent compilation | folded into `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` | ✅ Consolidated by team lead |
| 03 · AI Copilot capability code review | `deliverables/03_Copilot_Capability_Review.md` | ✅ Written (code-reviewer) |
| Consolidated gap analysis | `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` | ✅ Written (team lead) |
| Application source (read-only audited, not modified) | `backend/app/`, `frontend/` | ✅ Unmodified |
| Integration conclusion sent to team lead | `SendMessage → team-lead` | ✅ Sent |

### 9.5 Residual risks and recommendations

1. **Do not demo or publish this as "implemented".** The footer already says "Not for production use"; the README header, feature list and API docs contradict it. Align all documentation with the four-layer table in §6 before any external review.
2. **Fix or remove false-success paths first**: `/health`, `/crm/status`, `POST /crm/sync`, Gate 3, and `ranking_service`'s bare `except: return []`. A system that reports success while failing is worse than one that reports failure.
3. **Decide the target baseline with the team lead (Alan)**: the PRD V1.1 (111 requirements) and `designs/01` "Leadership Demo" (34 MVP-FRs, many explicitly OUT) are **different products**. Coverage against the PRD is 6.6%; against the demo spec it is higher but still fails the spec's own "REAL" items. Re-baselining is a scope decision, not an audit decision — per Iron Law #4, no scope cut may be applied silently here.
4. **If the demo spec is the target**, implement its declared REAL items in code: real provenance envelope (C-1), artefact state machine + approval tokens (C-2/C-3), audit event writes (C-4), workflow instances (C-5), live/replay feed binding, re-rank and mode switch — then **either wire `demo_data/` into the seed or delete it** so the fixture layer stops masquerading as implementation.
5. **Freeze the contracts (Iron Law #3)**: publish and enforce one OpenAPI contract; fix the 3 frontend/backend mismatches; remove the duplicate `CRMService` and duplicate brief page (Iron Law #1) — note the approval-aware `hubspot_service.py` is the orphaned one and should be the survivor.
6. **Add a startup hook + migrations + a smoke test**. As an integration engineer I cannot sign off on a system that cannot be rebuilt from a clean checkout.
7. **Address the LLM governance exposure**: `cc-vibe.com` is not OpenAI/Anthropic; there is no DPA, zero-retention evidence, prompt minimisation, or residency control. Until reviewed, do not send client context/transcripts to it.
8. **Rotate the exposed credentials** referenced by `HUBSPOT_CREDENTIALS.md` / `HUBSPOT_SETUP.md` (not gitignored) and replace the development `SECRET_KEY` in `.env` before any sharing.

### 9.6 Release note (as-is)

- **Deployment**: `./start.sh` (Postgres + Redis via Docker; FastAPI + Next.js as local processes). Ports 3000 / 8000 / 5432 / 6379. **Does not create tables or seed on a clean volume** — requires manual `python -m app.scripts.init_db` and `python -m app.scripts.seed_demo_data`.
- **Environment requirements**: Python 3.11+ (`uv`), Node 20+, Docker; `.env` currently contains live-looking third-party credentials and a development `SECRET_KEY`.
- **Known limitations**: everything in §8. In particular: no authentication, no audit, mock market data, non-functional P0 ranking, non-persistent approval gates, no outreach/product/suitability/post-meeting capabilities, no tests, and 55 fixtures + 9 mockups + 12 specs that are not connected to the running code.

---

## Appendix A · Critical Code Quotes

```python
# backend/app/api/v1/endpoints/briefs.py:31-45  — brief "generation" ignores the client
# TODO: Fetch client, portfolio, market data, interactions from DB
client_data = {"name": "Kenneth Wong", "aum": 45.2e6, "currency": "HKD",
               "risk_profile": "Moderate"}
portfolio_data = []
market_signals = []
interaction_history = []
brief = await copilot_service.generate_brief(
    client_data, portfolio_data, market_signals, interaction_history)
```

```python
# backend/app/api/v1/endpoints/workflow.py:62-86  — Gate 3: false success
# TODO: Execute all approved actions:
# - CRM sync / - D5 memory update / - Email draft / - Update workflow status
return {
    "workflow_id": request.workflow_id, "gate": "gate3", "status": "approved",
    "approved_by": request.approved_by,
    "actions_executed": ["crm_sync", "d5_memory_update", "email_draft_saved"],
    "workflow_complete": True
}
```

```python
# backend/app/services/market/market_service.py:41,46,51  — "real-time" quotes
"""Get real-time quotes ... Returns mock data for now since Tiger SDK has dependency issues"""
# Mock data for demo - replace with actual API calls when Tiger SDK is working
"price": 50.0 + hash(symbol) % 100,
```

```python
# backend/app/services/shariah/shariah_service.py:35-38  — always compliant
screening_result = {
    "symbol": symbol,
    "compliant": True,  # Placeholder
    ...
}
```

```python
# backend/app/services/ranking/ranking_service.py:178-183  — the P0 blocker
last_interaction = interactions[0].interaction_date      # tz-aware (Postgres)
days_since = (datetime.now() - last_interaction).days    # naive - aware -> TypeError
...
except Exception as e:
    logger.error(f"Error ranking clients: {e}")
    return []                                            # silent empty Top 10
```

```python
# backend/app/main.py:44-54  — health endpoint lies
return {"status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "services": {"market_data": "active", "copilot": "active", "crm": "active"}}
```

```tsx
// frontend/components/BriefModal.tsx:77  — hardcoded approval ID; edits discarded by backend
await briefApi.approve('brief-123', 'Sarah Chen', editing ? editedAgenda : undefined);
```

```tsx
// frontend/app/page.tsx:238  — empty ranked list -> fake client id
onClick={() => handleOpenBrief(rankedClients[0]?.client_id || 'demo', ...)}
```

```javascript
// mockup/app.js:166-170  — the "approval gate" in the mockup layer
function approveBrief() {
    AppState.briefApproved = true;
    showToast('Brief approved successfully', 'success');
    ...
}
```

```text
# demo_data/README.md:17-21  — the fixtures explicitly disclaim being implementation
"These files are the SPECIFIED OUTPUT SHAPE of a future generator ... They are DATA,
not a running generator, not application code ... No generator, script or executable
is included here."
```

---

*End of report · 02_Implementation_Feature_Audit.md · Read-only audit; no application code modified.*

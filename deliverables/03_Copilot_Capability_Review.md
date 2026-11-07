# 03 · AI Copilot Capability Review

**Reviewer:** 严过关 (Yan Guoguan), Code Reviewer, software R&D team
**Audit:** `rm-workbench-gap-audit` · central question assigned by team-lead
**Subject:** Alan's complaint — *"nor do I see any copilot feature, it is not copilot at all"*
**Contract under review:** PRD V1.1 Section 3 "AI Copilot Architecture (v1.1)", plus §1.1, §2.2, §8, §10 (full text at `/tmp/prd_full.txt`)
**Repository:** `/Volumes/Orico/code/capco/wealth-workbench`
**Date:** 2026-11-07
**Method:** Every file in the stated scope was read in full and verified by grepping the code body. Capability was **not** inferred from file/folder names, README claims, or CSV column names. A runtime log (`backend.log`, 701 lines) was used to distinguish "code exists" from "code runs".

---

## 0. Verdict up front

| Item | Finding |
|---|---|
| **Binary verdict** | **NO — this codebase cannot legitimately be called an "AI Copilot" as defined by PRD Section 3.** |
| **What it actually is** | **A demo dashboard + a scripted five-section brief renderer over hardcoded/synthetic fixtures, with one bolted-on single-shot LLM completion and a real but unguarded HubSpot sync.** More precisely: a real Postgres CRUD read layer for 3 seeded clients, one deterministic arithmetic scoring function, one `hash()`-based mock market feed, one placeholder Shariah/zakat calculator, three decorative "gates", and a *separate, unexecuted static design-spec data pack*. |
| **Copilot maturity** | **1.0 / 5** — "AI-assisted single-shot text generation". PRD Section 3 is level 4–5. |
| **Alan's complaint** | **UPHELD**, with one important nuance: the repo is *not* AI-free. There are **two real `chat.completions.create` call sites** (one reachable from the UI). Two single-shot prompts are not a copilot. |
| **Conclusion code** | 🔴 **退回重做 (Reject / re-build)** — as a *copilot* claim. The CRUD dashboard itself is a legitimate, working reduced scope and should be relabelled as such. |

### Fairness statement (read this before dismissing the review)

I am required to be harsh but **not** inaccurate. Three facts cut in the repo's favour and are stated explicitly:

1. **A genuine LLM HTTP call exists and succeeds at runtime.** `backend.log:360` and `:699` show `HTTP Request: POST https://cc-vibe.com/v1/chat/completions "HTTP/1.1 200 OK"`, immediately followed by `INFO:app.services.copilot.copilot_service:Generated brief with correlation_id ...` (`:361`, `:700`). This is a real model invocation, not a stub.
2. **Real infrastructure exists**: FastAPI, SQLAlchemy/asyncpg against Postgres, a real HubSpot SDK client, a Next.js frontend, and 3 seeded clients (2 live holdings, 2 interactions) that are genuinely queried (`backend.log` shows `SELECT ... FROM clients WHERE external_id LIKE 'RM001%'`). The live DB has **drifted from the checked-in seed script** — see the live-probe note in §8.2.
3. **The `demo_data/` pack is honest about itself.** Its README says, verbatim: *"These files are the **SPECIFIED OUTPUT SHAPE of a future generator** … They are **DATA**, not a running generator, not application code … No generator, script or executable is included here."* (`demo_data/README.md:16-22`). The problem is that the repository's README presents this pack's *shape* as implemented features.

So the verdict is **not** "there is no AI". The verdict is: **the AI that exists is one isolated point feature, and none of the five PRD copilot layers (Experience / Orchestration / Context-D5 / Skills / Trust) is implemented.**

This conclusion independently matches `deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` §0/§3 ("NOT an AI copilot", "1/5", "two real, working LLM calls"). This document supplies the line-level code evidence behind that verdict.

---

## 1. Q1 — Is there ANY real LLM/AI invocation?

### 1.1 YES — exactly one real invocation path, with two call sites

`backend/app/services/copilot/copilot_service.py` is the **only** file in the entire backend that imports an LLM SDK (confirmed by repo-wide grep for `openai|anthropic|AsyncOpenAI|chat.completions`; all other hits are dependency metadata or third-party `venv` files).

```python
# copilot_service.py:9, 20-24
from openai import AsyncOpenAI
...
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = settings.LLM_MODEL
```

```python
# copilot_service.py:123-151  (call site 1 — brief generation)
    async def _generate_with_ai(self, context: str) -> Dict:
        ...
126     prompt = f"""You are a wealth management AI assistant. Generate a concise 5-section client brief based on the following context.
...
140         response = await self.client.chat.completions.create(
141             model=self.model,
142             messages=[
143                 {"role": "system", "content": "You are a professional wealth management assistant."},
144                 {"role": "user", "content": prompt}
145             ],
146             temperature=0.7,
147             response_format={"type": "json_object"}
148         )
150         brief = json.loads(response.choices[0].message.content)
151         return brief
```

```python
# copilot_service.py:211-232  (call site 2 — transcript insight extraction)
211         prompt = f"""Analyze this meeting transcript and extract:
...
222         response = await self.client.chat.completions.create(
223             model=self.model,
224             messages=[
225                 {"role": "system", "content": "You are a meeting analysis assistant."},
226                 {"role": "user", "content": prompt}
227             ],
228             temperature=0.5,
229             response_format={"type": "json_object"}
230         )
232         insights = json.loads(response.choices[0].message.content)
```

**Runtime proof** (`backend.log`, secrets redacted):
```
:359  OPTIONS /api/v1/briefs/generate          200 OK
:360  HTTP Request: POST https://cc-vibe.com/v1/chat/completions "HTTP/1.1 200 OK"
:361  app.services.copilot.copilot_service:Generated brief with correlation_id 012d2eef-...
:362  POST /api/v1/briefs/generate              200 OK
:699  HTTP Request: POST https://cc-vibe.com/v1/chat/completions "HTTP/1.1 200 OK"
:701  POST /api/v1/briefs/generate              200 OK
```
Only the brief path was exercised in the captured log (2 calls); `/workflow/extract-insights` was **never called** — the log's full endpoint inventory is `my-day`, `performance-trend`, `allocation`, `crm/sync`, `briefs/generate`, `health`, `clients/`.

**What this call is NOT:** there is **no** tool/function calling, **no** streaming, **no** retry/backoff, **no** token or latency accounting, **no** prompt/model version pinning, **no** max-token or timeout guard, **no** structured output validation beyond a bare `json.loads`, and **no** grounding check. It is a single-turn completion — a point feature, not an agent.

**What it is fed is empty.** The only UI-reachable caller passes literal empty context:

```python
# backend/app/api/v1/endpoints/briefs.py:24-45
24  @router.post("/generate")
25  async def generate_brief(request: BriefGenerateRequest, ...):
29      """Generate a client brief (Gate 1)"""
31      # TODO: Fetch client, portfolio, market data, interactions from DB
32      client_data = {
33          "name": "Kenneth Wong",          # hardcoded; request.client_id is NEVER used
34          "aum": 45.2e6,
35          "currency": "HKD",
36          "risk_profile": "Moderate"
37      }
39      portfolio_data = []                  # empty
40      market_signals = []                  # empty
41      interaction_history = []             # empty
43      brief = await copilot_service.generate_brief(
44          client_data, portfolio_data, market_signals, interaction_history
45      )
```
`request.client_id` and `request.force_regenerate` are both **ignored**. Every brief, for every client, is generated from the same hardcoded "Kenneth Wong" string and three empty lists. `_build_context()` (`copilot_service.py:93-121`) therefore produces a prompt with no holdings, no signals and no interactions. **There is no context assembly** (see Q2/Q3). This is a PRD FR-01/FR-02/FR-14 violation: "no news or portfolio fact is presented without provenance" is impossible when no portfolio facts are supplied.

### 1.2 The fallback path — hardcoded strings, and a silent false-success

```python
# copilot_service.py:37-46, 86-91
46          brief = await self._generate_with_ai(context)
...
86          logger.info(f"Generated brief with correlation_id {correlation_id}")
87          return brief
89      except Exception as e:
90          logger.error(f"Error generating brief: {e}")
91          return self._generate_fallback_brief()
```

```python
# copilot_service.py:153-155
153     except Exception as e:
154         logger.error(f"AI generation error: {e}")
155         return self._generate_fallback_brief()
```

```python
# copilot_service.py:157-175  — the "AI" output when the call fails
157 def _generate_fallback_brief(self) -> Dict:
158     """Fallback brief when AI fails"""
159     return {
160         "portfolio_overview": {"content": "Portfolio data temporarily unavailable. Please review manually."},
163         "material_changes":   {"content": "No significant changes detected."},
166         "recent_interactions":{"content": "Interaction history available in client record."},
169         "market_news":        {"content": "Market news feed temporarily unavailable."},
172         "proposed_agenda":    {"content": "1. Review portfolio performance\n2. Discuss investment objectives\n3. Address any client questions"}
174     }
```

**Review finding (blocking, silent failure):** `_generate_with_ai` swallows the exception and returns a *successful-looking* dict. `generate_brief` cannot distinguish real model output from the fallback, still attaches provenance claiming `"source": "Copilot Brief Generator"` (`:51`, `:80`), and still logs `Generated brief with correlation_id ...` (`:86`). The API returns `200 OK` with `status: "draft"` (`briefs.py:47-51`). A failed or unreachable LLM is therefore **indistinguishable from success** to the caller, the UI, and telemetry. PRD §6 explicitly requires "show status; preserve user edits" and §8 requires "faithful summaries, not unsupported rationalizations".

### 1.3 Everything else labelled "AI" is f-strings, hardcoded dicts, `hash()` mocks or static CSVs

| Claimed capability | Decisive code | What it actually is |
|---|---|---|
| "AI-generated, source-linked brief" | `BriefModal.tsx:31-67` | **Frontend injects hardcoded narrative** (see Q5). |
| "AI-ranked daily list" | `ranking_service.py:48-52`, `:203-231` | Deterministic `opp*0.4 + risk*0.35 + ret*0.25`; reason strings hardcoded in a 3-entry dict. No model. |
| "reason codes / explanations" | `ranking_service.py:221-225` | `descriptions = {"OPPORTUNITY": "Portfolio drift triggered by market event", ...}` — fixed literals, unrelated to the client's actual data. |
| "evidence chips" | `ranking_service.py:242-253` | `f"{signal['symbol']} {signal['change_percent']:+.2f}%"` and a hardcoded `{"source": "rank.clients v1.2", "description": "Ranking algorithm"}`. |
| "real-time quotes" | `market_service.py:46-63` | `"price": 50.0 + hash(symbol) % 100`, `"change_percent": ((hash(symbol) % 5) - 2.5) / 50.0 * 100`. Docstring: *"Returns mock data for now since Tiger SDK has dependency issues"* (`:41`). |
| "Tiger Broker News Feed" | `market_service.py:81-107` | 3 hardcoded items; `"url": "https://example.com/news/1"`. |
| "Tiger Broker HTTP API integration" | `market_service.py:25`, `:29-36` | `self.base_url = "https://openapi.tigerbrokers.com.hk/gateway"` is **never used**; `_sign_request()` is **never called**; `requests`, `base64`, `hmac`, `hashlib` imported and **never used**. **Zero HTTP calls to any market vendor.** |
| "KPI cards with real-time data" | `dashboard.py:63-65`, `:100-109`, `:123-129`, `:142-152`, `:166-168` | `meetings_today: 3  # TODO`, `open_actions: 7 # TODO`, `ytd_performance: 5.8`, `"↑ $12.3M this month (+2.9%)"`, hardcoded chart arrays `[0, 1.2, 2.5, ...]`. |
| "Shariah screening engine" | `shariah_service.py:35-64` | `"compliant": True,  # Placeholder` + a 5-keyword blacklist. |
| "Shariah-compliant alternatives" | `shariah_service.py:133-142` | A single fabricated `f"ALT-{symbol}-1"` with `"name": "Shariah Compliant Alternative 1"`. |
| Live dashboard / schedule / news / priority actions / book stats | `page.tsx:97-115`, `:229-285`, `:293-311`, `:322-375` | Static JSX literals, including `Workflow ID: 8f21a4b2` and `"Tuesday, 16 March 2026"`. |

**`MARKET_NEWS_AND_LLM.md:5` claims "All market data and news are sourced from Tiger Broker" and `:53` "All news displayed on the dashboard comes from Tiger Broker's news feed." Both are false per the code above.**

---

## 2. Q2 — Orchestrator / agent loop / skill registry / chaining / context assembly / state machine?

**NO.** The endpoints are independent, stateless read/write handlers wired as six flat routers:

```python
# backend/app/api/v1/__init__.py:10-15
api_router.include_router(clients.router,   prefix="/clients",   tags=["clients"])
api_router.include_router(market.router,    prefix="/market",    tags=["market"])
api_router.include_router(briefs.router,    prefix="/briefs",    tags=["briefs"])
api_router.include_router(workflow.router,  prefix="/workflow",  tags=["workflow"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(crm.router,       prefix="/crm",       tags=["crm"])
```

### 2.1 `orchestrate_workflow()` is a stub that returns a static dictionary

```python
# copilot_service.py:177-199
177 async def orchestrate_workflow(self, workflow_type, client_id, trigger) -> Dict:
183     """Orchestrate complete workflow from trigger to completion"""
186     correlation_id = uuid.uuid4()
187     workflow_instance = {
188         "correlation_id": str(correlation_id),
189         "workflow_type": workflow_type,
190         "client_id": client_id,
191         "trigger": trigger,
192         "stages": [],                                  # <-- always empty
193         "current_stage": WorkflowStage.RANK_CLIENTS.value,
194         "status": "in_progress",
195         "created_at": datetime.now().isoformat()
196     }
198     logger.info(f"Starting workflow {workflow_type} with correlation_id {correlation_id}")
199     return workflow_instance                          # <-- returned, never persisted, never advanced
```
There is **no loop, no skill invocation, no stage transition, no persistence, no context assembly, no error/rollback handling**. The method name and docstring are the entire "orchestrator". The `WorkflowStage` enum (`models.py:16-20`: `RANK_CLIENTS → BRIEF_GENERATE → MEETING_CAPTURE → REVIEW_APPROVE`) is declared but **no code ever transitions between its values** (the only use is initialising the literal above).

### 2.2 No persisted state, no skill registry, no chaining

- `Brief`, `WorkflowInstance`, `AuditEvent`, `MarketTick` tables are **declared** (`models.py:141-209`) but **never written**. Repo-wide grep for `session.add(` / `db.add(` / `Brief(` / `WorkflowInstance(` / `AuditEvent(` / `MarketTick(` in `backend/app` returns exactly **three** `session.add` calls, all in `seed_demo_data.py:98,125,175` for `Client`, `Holding`, `Interaction` only.
- `ArtefactState` (8 states, `models.py:22-30`) is referenced **only** in its own definition and its column default (`:149`). No artifact ever changes state.
- `backend/alembic/versions/` is **empty** (no migrations); `backend/app/schemas/` is **empty**.
- `workflow.py:91-106` `get_workflow()` returns a hardcoded `{"status": "in_progress", "current_stage": "brief.generate"}` with `# TODO: Fetch from database`.
- **The entire workflow API is dead from the UI — and would 422 if wired.** `frontend/lib/api.ts:73-88` defines `workflowApi` (`start`, `recordConsent`, `approveReview`, `getWorkflow`, `extractInsights`), but grep across all `.ts/.tsx` files shows **zero imports/usages**. Only `briefApi.generate` and `briefApi.approve` are called (`BriefModal.tsx:28,77`; `brief/[clientId]/page.tsx:21,33`). Worse, the two LLM-adjacent methods have **broken contracts**: `workflow.py:25-31` declares `workflow_type: str` and `client_id: str` as *query* params (only `trigger: Dict` is a body param), while `lib/api.ts:75` posts all three in the JSON body; `workflow.py:108-113` declares both `transcript: str` and `client_id: str` as *query* params, while `lib/api.ts:87` posts both in the body. Both therefore return **422 Unprocessable Entity** for the frontend's own payloads — independently confirmed by live probes in `02_Implementation_Feature_Audit.md` §4.4. So the workflow API is not merely unused, it is **non-functional by construction**. (See also N9 on the privacy consequence of putting a meeting transcript in a query string.)
- The "workflow stage" strip the user sees is static JSX, not state: `page.tsx:97-115` hardcodes steps 1–4 and `Workflow ID: 8f21a4b2`, the same literal as `dashboard.py:80` (`"correlation_id": "8f21a4b2"`).

### 2.3 No closed loop

PRD §3: *"meeting outcomes feed the ranking model; ranking drives the next briefs; briefs carry the latest preferences."* In code:
- `ranking_service.rank_clients()` reads only `Client`, `Holding`, `Interaction` and an in-memory `market_signals` argument (`ranking_service.py:22-83`). It never reads a meeting outcome, approval, or preference written after a meeting.
- `generate_brief()` is passed `interaction_history = []` (`briefs.py:41`), so briefs never carry preferences.
- `/workflow/review/approve` claims `"d5_memory_update"` (`workflow.py:82`) but executes nothing (Q4).
- There is no cross-skill task to complete, so PRD §10.1's **≥85% cross-skill completion** and **≥70% copilot orchestration rate** are not merely unmet — they are **uninstrumented and unmeasurable**, effectively 0.

### 2.4 🚩 Duplicate implementations and dead abstractions (Iron Law 1: simplicity first)

These are **blocking** in a code review even before the copilot question:

1. **Two `CRMService` classes, both exporting a `crm_service` singleton:**
   - `backend/app/services/crm/crm_service.py:13,169` — writes to HubSpot **immediately** inside `sync_client_to_hubspot()` (`:128-148`).
   - `backend/app/services/crm/hubspot_service.py:11,103` — implements the **correct** two-phase pattern: `sync_client()` returns `{"diff": ..., "status": "pending_approval"}` (`:59-63`) and a separate `execute_sync()` (`:69-100`).
   - `backend/app/services/crm/__init__.py:4` exports `crm_service` from **`crm_service.py`** (the unsafe one). `hubspot_service.py` is **orphaned dead code** — grep shows `sync_client` / `execute_sync` are **never called anywhere**. The repo duplicated the wheel **and wired the wrong copy**. The one file that models the mandated approval gate is the one nobody uses.
2. **Three unguarded CRM write paths** for the same operation: `crm.py:16-87` (`/crm/sync`), `crm.py:90-140` (`/crm/sync/{id}`), and `backend/app/scripts/sync_to_hubspot.py:10-71`. All three re-implement the same contact-property mapping.
3. **Two brief renderers with duplicated hardcoded fallback copy**: `BriefModal.tsx:31-67` and `app/brief/[clientId]/page.tsx` — both call `briefApi.approve('brief-123', 'Sarah Chen', ...)`.
4. **Unused dependency / over-abstraction**: `requirements.txt:14` declares `pgvector==0.2.4`; grep finds **zero** `embedding`/`vector` usage. `market_service.py:8-11` imports `requests`, `base64`, `hmac`, `hashlib` — all unused. `config.py:9` `SECRET_KEY`, `requirements.txt:25-26` `python-jose`/`passlib` — all unused (no auth anywhere, see Q4). `SourceKind`/`WorkflowStage`/`ArtefactState` enums define a vocabulary that no state machine consumes.

---

## 3. Q3 — Does a Client Memory / Relationship Graph (D5) exist IN CODE?

**NO D5 service exists.** What exists is a flat interaction table, two flat JSONB columns, a hardcoded chart, and static CSVs. There is **no memory service, no graph traversal, no memory write path, and no entitlement-aware context assembly**.

| Artefact | Evidence | Why it is not D5 |
|---|---|---|
| `Interaction` table | `models.py:114-139`, comment `# Interaction History (D5 Client Memory)` | A flat per-client log. Only consumed by `ranking_service._calculate_retention()` (`:158-201`) to count days since last contact. No graph, no entity resolution, no versioning, no supersession. |
| `Client.preferences` / `Client.family_entities` | `models.py:50`, `:54` (JSONB) | Flat JSON blobs, seeded with hardcoded literals (`seed_demo_data.py:47-52`, `:83-91`). Never read by the copilot: `briefs.py:41` passes `interaction_history = []`. |
| **Family / Relationship Graph** | `frontend/components/FamilyGraphModal.tsx:22-95` | A **hardcoded `graphData` object** — 7 nodes (`patriarch`, `son1`, … `operating`) with hardcoded AUM values (`120.5`, `35.2`, `28.8` …) and 6 hardcoded links with `"full"` / `"education-only"` / `"restricted"` entitlements. **The file imports no API module and makes no network call.** Entitlements are rendered as a `<div>` legend (`:223-229`), not enforced. |
| `memory_facts.csv`, `graph_nodes.csv`, `graph_edges.csv`, `entitlement_decisions.csv`, `graph_source_docs.csv` | `demo_data/` | **Static fixtures.** Grep for `demo_data|memory_facts|graph_nodes|graph_edges|...` across `backend/app` → **0 matches**. Nothing loads them. |
| `demo_data/README.md:16-22` | *"These files are the SPECIFIED OUTPUT SHAPE of a future generator — a static, labelled preview … They are DATA, not a running generator, not application code, not a scaffold, not executed DDL … No generator, script or executable is included here."* | The pack **explicitly declares itself a design spec for a future generator**, i.e. precisely "CSV fixtures and design documents". |

Consequence for PRD FR-5.1 (*"intra-family entitlements are enforced in copilot context assembly, not only in UI; entitlement tests are a hard release gate"*): there is **no context assembly at all**, so there is nowhere to enforce entitlements; and there are **no tests** (see Q6). `demo_data/entitlement_decisions.csv` contains plausible-looking `granted` rows with `ent_matrix_v1`, but they are pre-written fiction, not decisions computed by code.

---

## 4. Q4 — Are the three approval gates enforced server-side with persisted state and write protection?

**NO. All three "gates" are decorative return values. There is no persisted state, no sequencing check, and no write protection.**

### Gate 1 — brief approval
```python
# backend/app/api/v1/endpoints/briefs.py:57-74
57  @router.post("/approve")
58  async def approve_brief(request: BriefApprovalRequest, ...):
62      """Approve brief (Gate 1 approval)"""
63      try:
64          # TODO: Update brief status in database
65          return {
66              "brief_id": request.brief_id,
67              "status": "approved",          # <-- literal string, nothing persisted
68              "approved_by": request.approved_by,
69              "gate": "gate1",
70              "next_stage": "meeting.capture"
71          }
```

### Gate 2 — consent
```python
# backend/app/api/v1/endpoints/workflow.py:42-60
42  @router.post("/consent")
43  async def record_consent(request: ConsentRequest, ...):
47      """Record client consent (Gate 2)"""
48      try:
49          # TODO: Store consent in database with C-4 audit log
50          return {
52              "consent_given": request.consent_given,   # <-- echoed straight from the request body
53              "consent_method": request.consent_method,
54              "gate": "gate2",
55              "status": "consent_recorded" if request.consent_given else "consent_declined",
56              "next_stage": "meeting.capture" if request.consent_given else "manual_notes"
57          }
```
`consent_given` is caller-supplied and **not validated, not stored, and not checked by any downstream operation**. PRD FR-04 ("No audio is captured or transmitted before required consent") is moot — there is no capture — but the gate itself has no enforcement semantics.

### Gate 3 — review approval (the most damaging finding)
```python
# backend/app/api/v1/endpoints/workflow.py:62-89
62  @router.post("/review/approve")
63  async def approve_review(request: ReviewApprovalRequest, ...):
67      """Approve all meeting outcomes (Gate 3)"""
68      try:
69          # TODO: Execute all approved actions:
70          # - CRM sync
71          # - D5 memory update
72          # - Email draft
73          # - Update workflow status
75          return {
76              "workflow_id": request.workflow_id,
77              "gate": "gate3",
78              "status": "approved",
79              "approved_by": request.approved_by,
80              "actions_executed": [                    # <-- claims actions that NEVER RUN
81                  "crm_sync",
82                  "d5_memory_update",
83                  "email_draft_saved"
84              ],
85              "workflow_complete": True
86          }
```
This endpoint **reports successful execution of a CRM sync, a memory update and an email-draft save that it does not perform**. It accepts **any** `workflow_id` — there is no check that Gate 1 or Gate 2 ever occurred, no lookup of a `WorkflowInstance`, no `ArtefactState` transition, no `AuditEvent`, no approver authentication. This is a **false-success response**, explicitly forbidden by PRD §6 ("never show false success") and FR-07 ("Nothing is written, sent or submitted before explicit RM confirmation … the final review identifies who approved and when").

### No write protection — and there IS an unguarded external write
```python
# backend/app/api/v1/endpoints/crm.py:16-18, 26-27, 57-65
16  @router.post("/sync")
17  async def sync_all_clients_to_hubspot(db: AsyncSession = Depends(get_db)):
20      """Sync all RM Workbench clients to HubSpot CRM. Shows diff before applying changes"""
26      result = await db.execute(select(Client))
27      clients = result.scalars().all()
...
57          # Sync to HubSpot
58          result = await crm_service.sync_client_to_hubspot(client_data)
```
```python
# backend/app/services/crm/crm_service.py:128-148  (diff is computed, then the write happens in the SAME call)
128         if existing:
130             diff = self._calculate_diff(existing['properties'], properties)
133             result = await self.update_contact(existing['id'], properties)   # WRITE
...
142             result = await self.create_contact(properties)                   # WRITE
```
The docstring says "Shows diff before applying changes" — it does **not**: diff and write occur in one unguarded POST. There is **no approval token, no idempotency key, no `ArtefactState` check, no old/new preview surfaced to an RM, and no authentication**. A second unguarded path is `scripts/sync_to_hubspot.py:10-71`. The frontend even fabricates the approver: `await briefApi.approve('brief-123', 'Sarah Chen', ...)` (`BriefModal.tsx:77`, `brief/[clientId]/page.tsx:33`).

**Security finding:** grep for `Depends(` across all endpoints returns **only** `Depends(get_db)` — there is **no authentication, no authorisation, no RBAC, no tenant isolation** anywhere. `SECRET_KEY` is configured (`config.py:9`) but never used. Combined with the unauthenticated `POST /crm/sync` that writes to a real external CRM, PRD D0 ("Identity, tenant isolation, RBAC, audit and AI-provider controls: required by every epic") is **entirely absent**.

**The only correct approval implementation in the repo is orphaned:** `hubspot_service.py:59-63` returns `"status": "pending_approval"` and `:69-100` `execute_sync()` performs the write in a separate step. It is never imported (`crm/__init__.py:4` re-exports the other class). See §2.4.

---

## 5. Q5 — Is provenance real? Are "confidence" values real?

**NO. Provenance is a set of hardcoded labels attached *after* generation; evidence chips are literal JSX; confidence values are hardcoded literals.**

### 5.1 Backend provenance is a post-hoc hardcoded f-string dict

```python
# copilot_service.py:48-84 (abridged; all five blocks are identical in shape)
48  # Add provenance to each section
49  brief["portfolio_overview"]["provenance"] = {
50      "source_kind": SourceKind.DERIVED.value,
51      "source": "Copilot Brief Generator",       # <-- literal label, not a source record
52      "version": "v1.2",                         # <-- literal, no registry
53      "timestamp": datetime.now().isoformat(),   # <-- generation time, NOT data as-of
54      "correlation_id": str(correlation_id)
55  }
57  brief["material_changes"]["provenance"] = {
58      "source_kind": SourceKind.LIVE_FEED.value,
59      "source": "TigerBroker + Copilot", ... }
64  brief["recent_interactions"]["provenance"] = {
65      "source_kind": SourceKind.RM_MANUAL.value,
66      "source": "D5 Client Memory", ... }         # <-- no D5 read occurred
71  brief["market_news"]["provenance"] = {
72      "source_kind": SourceKind.LIVE_FEED.value,
73      "source": "TigerBroker News", ... }
```

Defects: (a) **no source IDs, no links, no as-of timestamps bound to any statement** — PRD FR-02 requires "Every material fact, alert and news item links to its source and timestamp" and "selecting a source opens the originating record"; (b) attached to a **section**, not a statement; (c) the LLM prompt only asks for free-text `content` strings (`copilot_service.py:130-138`: *"Each section should have 'content' as a string"*), so **no per-statement evidence can exist**; (d) labels name sources that were never consulted — "TigerBroker News" while `market_signals=[]` and the market service returns `hash()` mocks; "D5 Client Memory" while `interaction_history=[]`; (e) `"version": "v1.2"` is a literal, not a registry lookup.

### 5.2 Frontend "evidence chips" are hardcoded JSX with a browser clock

```tsx
// BriefModal.tsx:137-141
<span className="inline-block px-2 py-1 bg-green-50 border border-green-600 ... rounded">
  ● LIVE · TigerBroker
</span>
```
```tsx
// app/brief/[clientId]/page.tsx:88-92
<span className="... ">  ● LIVE · TigerBroker  </span>
```
```tsx
// app/page.tsx:92-94  and  :303-309
<div className="px-4 py-1 bg-green-600 ...">  ● LIVE MARKET DATA · {formatTime(currentTime)}  </div>
...
<span ...>  ● LIVE · Reuters · {formatTime(currentTime)}  </span>
```
`formatTime(currentTime)` is a `setInterval` **browser clock** (`page.tsx:22-24`), not a feed as-of timestamp. The dashboard chip says **"Reuters"**, the brief chip says **"TigerBroker"**, and the backend says `"TigerBroker News"` — three mutually inconsistent hardcoded source names for the same supposed feed. The market-news list at `page.tsx:293-311` maps over `marketNews` but renders the **hardcoded** strings `"HSBC Holdings +2.3%"` and `"Strong Q3 earnings, guidance upgraded"` — the `news` variable is never used for content.

### 5.3 Confidence is hardcoded

| Location | Value | Reality |
|---|---|---|
| `copilot_service.py:236` | `"confidence": 0.85` | Literal constant attached to every insight extraction, regardless of model output. |
| `BriefModal.tsx:42` | `confidence: 0.92` | Hardcoded inside injected narrative. |
| `BriefModal.tsx:57` | `confidence: 1.0` | Hardcoded "TigerBroker News · LIVE". |
| `seed_demo_data.py:153,165` | `0.95`, `0.92` | Seeded literals, no computation. |
| `demo_data/memory_facts.csv`, `extraction_items.csv`, `audit_events.csv` | `0.94`, `0.91`, `0.88`, `1.000` … | Static CSV columns. |

No model returns a confidence score, no calibration exists, and `response.choices[0]` is used without reading logprobs or any uncertainty signal. PRD §8 ("confidence/limitations") and FR-05 ("view confidence/source timestamps before accepting notes") are not met.

### 5.4 The "AI" brief content itself is largely hardcoded in the frontend

```tsx
// BriefModal.tsx:31-60
31  // Enrich with real data if missing
32  if (!briefData.recent_interactions?.content) {
33      briefData.recent_interactions = {
34          content: `Last meeting (15 days ago): Client expressed preference for gradual rebalancing to minimize tax impact. Mentioned daughter may join next meeting.
36  Previous meeting (30 days ago): Discussed Hong Kong tech sector opportunities. Client interested in fintech exposure.
38  Action items: Send consolidated quarterly statement by Nov 20.`,
39          provenance: { source: 'CRM & D5 Memory', timestamp: new Date().toISOString(), confidence: 0.92 }
44      };
45  }
47  if (!briefData.market_news?.content) {
48      briefData.market_news = {
49          content: `HSBC Holdings (0005.HK) +2.3%: Strong Q3 earnings announced today, guidance upgraded for FY2026. Analysts raising price targets.
51  Hong Kong Tech Sector Rally: ...
53  Portfolio Impact: HSBC position represents 51% of equity allocation. Recent movement has caused 6% drift from target allocation.`,
54          provenance: { source: 'TigerBroker News · LIVE', timestamp: new Date().toISOString(), confidence: 1.0 }
59      };
60  }
63  setEditedAgenda(briefData.proposed_agenda?.content || `1. Review portfolio drift due to HSBC +2.3% movement ...`);
```
The comment `// Enrich with real data if missing` is the opposite of what the code does: it **replaces missing model output with hardcoded demo copy** and labels it with fabricated provenance and confidence. Combined with the backend fallback (§1.2), **every visible "AI" artifact in this app can be produced without a single successful model call.**

---

## 6. Q6 — Telemetry, model/prompt/template versioning, kill switch, zero-retention, audit logs?

**NONE are implemented in application code.** A repo-wide grep over `backend/app` for `telemetry|kill.?switch|feature.?flag|version_registry|prompt_version|model_version|zero.?retention|audit_log|event_type|emit_event|track\(` returns **0 matches**.

| PRD requirement | Code reality |
|---|---|
| Correlated orchestration telemetry (§10.2: `copilot_workflow_started/stage_approved/completed/abandoned`, *skill invocation chain*, *manual-stitch interventions*, model/prompt/template/rule-pack version + source timestamps + tenant-safe correlation ID) | Only unstructured `logger.info/error` calls. `correlation_id` is generated per call (`copilot_service.py:38`, `:186`) but **never propagated** across endpoints; `dashboard.py:80` uses the **literal** `"8f21a4b2"`. No event taxonomy exists. |
| Model / prompt / template / rule-pack versioning + rollback (§8) | Hardcoded literals only: `"version": "v1.2"` (`copilot_service.py:52,81`), `"rank.clients v1.2"` (`ranking_service.py:250`), `"Shariah Screening Engine v1.0"` (`shariah_service.py:49`), `"Zakat Calculator v1.0"` (`:114`). `config.py:40` default `gpt-4-turbo-preview` is overridden by `.env:23` `LLM_MODEL=gpt-6.1-sol`; no pinning, no eval, no rollback. |
| Feature / stage-level kill switch (§8, §13) | Absent. `market_service.set_mode()` (`market_service.py:171-177`) flips a `LIVE`/`REPLAY` **label**; the generated data is identical either way — it is not a kill switch. |
| Immutable audit log (§7, §8) | `AuditEvent` table declared (`models.py:191-209`) and **never written**. `workflow.py:49` literally says `# TODO: Store consent in database with C-4 audit log`. |
| Zero provider retention / training (§8) | No controls. Client name, AUM, risk profile and preferences are sent to a third-party endpoint (`cc-vibe.com`, `.env:22`) with no contract, no prompt minimisation, no redaction, no residency, and no provider-logging configuration. |
| Versioned Shariah rule packs with SSB sign-off | `shariah_service.py:24` logs `"Shariah tools path not found - using stub implementation"`; `.env:36` sets `SHARIAH_TOOLS_PATH=/tmp` (the `.env.example:42` path `/Volumes/Orico/code/capco/islamic-ai/shariah` is not used). No rule pack exists. |
| Eval suite / tests | **No project test files.** Glob for `test_*.py`, `*.test.ts(x)`, `*.spec.ts`, `conftest.py` returns only third-party files inside `venv/` and `node_modules/`. `README.md:231-244` documents `pytest`, `npm run test`, `docker-compose.test.yml` — none of these targets exist. Entitlement leakage tests, hard-stop tests and the "end-to-end orchestration eval suite" (PRD §13) are absent. |

### The trap: rich governance machinery exists — as STATIC FIXTURES

`demo_data/` contains a remarkably complete-looking governance dataset:
- `audit_events.csv` — 18 events with `prev_hash` / `row_hash` **hash chain** and `from_state`/`to_state`.
- `approval_tokens.json` — `"immutable": true`, `"zero_writes_zero_sends_before_approve": true`, `"scope": [...5 items...]`, `"post_approve_declaration": "CRM write-back → sandbox portal succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades"`.
- `workflow_stages.csv` — 6 stages (`tick_ingest → signal_raised → brief_generated → review → approval`), `workflow_instances.csv` — status `completed`.
- `version_registry.csv`, `config_versions.csv` — rule-pack v1, ranking-policy v1, drift threshold 6%.
- `artefacts.json` — `"evidence_chips": ["seeded · prior close"]`, states `draft/pending_review/approved`.
- `entitlement_decisions.csv`, `suitability_state.csv`, `consent_state.csv`, `demo_sink_messages.csv` — `"0 sends · 0 trades · 0 real dialled calls"`.

**Not one of these files is read by any code** (grep over `backend/app` → 0 matches). `demo_data/README.md:16-22` states they are the *"SPECIFIED OUTPUT SHAPE of a future generator"*, i.e. a design document. `demo_data/README.md:1-3` says `100% synthetic · DESIGN ONLY`; `:35` declares `0 real dialled calls · 0 real client-facing sends · 0 real PII`. **These CSVs describe a governance system that does not exist.** This is the single strongest explanation for why the repo *looks* implemented: the spec of the copilot was written down as data, and the README then reported that spec as features.

### Security note (secrets redacted)
`.env` is committed to the working tree and contains real-looking credentials: an RSA private key (`:9`), HubSpot API key / access token / personal access key (`:16-18`), a Tiger token (`:13`), and an LLM API key (`:21`). Values are deliberately **not reproduced** in this report. `.env.example:1-46` correctly uses placeholders; the live `.env` does not. This should be remediated independent of the copilot question.

---

## 7. Q7 — Transcription, consent capture, NL product search, suitability R/Y/G, zakat, screening: code or fixtures/docs?

| Capability | In application code? | Decisive evidence | Where it DOES exist |
|---|---|---|---|
| **Transcription / ASR / recording** | ❌ **No** | `workflow.py:108-126` accepts a `transcript: str` **supplied by the caller**; `copilot_service.py:201-244` only inserts that string into a prompt. There is no audio capture, no recording indicator, no pause/stop, no ASR provider, no speaker diarisation, no timestamped excerpts. | `demo_data/transcript_utterances.csv` — `stub_declaration: "STUB · declared (scripted transcript via test call)"`; `demo_data/retell_call.json`. |
| **Consent capture / recording policy** | ❌ **No enforcement** | `workflow.py:42-60` echoes `consent_given` from the request body with `# TODO: Store consent in database with C-4 audit log`. `Interaction.recording_consent`/`consent_method` columns exist (`models.py:128-129`) but are only seeded (`seed_demo_data.py:151-152,163-164`) and never checked. | `demo_data/consent_state.csv` (`accepted` / `withdrawn` / `declined` rows). |
| **Natural-language product search** | ❌ **No** | No endpoint, no service, no query interpretation, no interpreted filters, no product entitlement check. Grep for `product.?search|natural.language` in `backend/app` → 0 matches. | `demo_data/products.csv`, `instruments.csv`; PRD FR-16/17. |
| **Suitability Red/Yellow/Green engine** | ❌ **No** | No rating, no rule/signal justification, no overrides, no hard stops. Only tangential: a `suitability_expiry` string in `Client.preferences` used to add `+5.0` to a risk score (`ranking_service.py:133-139`) and a hardcoded reason string `"Suitability review required or concentration risk"` (`:223`). | `demo_data/suitability_state.csv` (`current` / `expired` / `missing` only — no R/Y/G); PRD FR-18/19. |
| **Zakat engine** | ⚠️ **Trivial arithmetic, not an engine** | `shariah_service.py:72-118`: `if holding.get("asset_class") in ["Equity", "Cash"]: total_zakatable += current_value`, then `zakat_rate = 0.025; zakat_amount = total_zakatable * zakat_rate`. Hardcoded rate, hardcoded `"calculation_method": "Simplified Hawl Method"`. The sole call site passes a **hardcoded hawl date**: `clients.py:120` `"2025-01-01"  # Would calculate actual hawl date`. No nisab, no lunar/solar convention, no configurable AAOIFI methodology, no purification ratio. | PRD FR-4.2; `demo_data/` has no zakat output file. |
| **Shariah screening engine** | ⚠️ **Placeholder** | `shariah_service.py:26-70`: `"compliant": True,  # Placeholder` (`:37`), `methodology: "AAOIFI Standard"` and `criteria_checked` are hardcoded labels (`:39-44`), and the only "logic" is a 5-word blacklist `["alcohol","gambling","pork","interest","tobacco"]` (`:56-64`). **The sole call site defeats it**: `clients.py:101-105` passes `{"business_description": ""}  # Would fetch from market data`, so the blacklist can never fire and every holding is reported compliant. Service self-declares `"using stub implementation"` (`:24`). | PRD FR-4.1/4.3; `demo_data/` has no SSB evidence file. |

**Conclusion:** six of the seven capabilities are **represented only as CSV fixtures and design documents**; the two that have code are placeholders that are inert at their only call site.

---

## 8. Q8 — Binary verdict, what it is, and maturity grade

### 8.1 Binary verdict

> **NO.** Under PRD Section 3 — *"All AI capabilities are delivered as skills behind a single orchestrating copilot, not as independent features"*, five layers (Experience, Orchestration, Context-D5, Skills, Trust), closed loop, cross-skill task completion ≥85%, context reuse — **this codebase cannot be called an AI Copilot.**

Direct comparison against the contract:

| PRD §3 requirement | Present? | Evidence |
|---|---|---|
| Single orchestrating copilot / single entry point | ❌ | Six flat independent routers (`api/v1/__init__.py:10-15`); `orchestrate_workflow()` returns a static dict (`copilot_service.py:177-199`); `workflowApi` never called from UI. |
| Skills behind the copilot (skill registry, contracts, chaining) | ❌ | No registry, no skill interface, no chaining. Two isolated prompts. |
| Context layer = D5 Client Memory & Relationship Graph | ❌ | No service; hardcoded ECharts graph (`FamilyGraphModal.tsx:22-95`); static CSVs. |
| Context assembly / context reuse | ❌ | `briefs.py:39-41` passes three empty lists to the brief generator. |
| Closed loop (outcomes → ranking → briefs → preferences) | ❌ | No outcome capture; no write path to memory; ranking reads only seeded tables. |
| Cross-skill task completion ≥85% / ≥70% copilot orchestration rate | ❌ | No chained skills exist ⇒ 0; no telemetry ⇒ unmeasurable. |
| Trust layer (gates, provenance, versioning, kill switch, zero-retention) | ❌ | Gates are return strings; provenance is hardcoded labels; versioning/kill switch/audit/retention absent. |
| Orchestration quality measured by *task completion*, not chat volume | ❌ | No measurement of any kind. |

### 8.2 What it IS (precise description)

> **A demo dashboard + scripted five-section brief renderer over hardcoded/synthetic fixtures, with one bolted-on single-shot LLM completion and a real but unguarded HubSpot sync.**

Component-by-component, what a user actually gets:
- **Real**: FastAPI + Postgres CRUD over 3 seeded clients / **3 holdings in `seed_demo_data.py` but only 2 in the live DB** / 2 interactions; a Next.js dashboard with ECharts; a real HubSpot SDK client; **one working single-shot LLM call** for brief text.
- **Scripted**: a deterministic weighted-sum ranking with hardcoded reason strings; a `hash()`-based mock quote feed and 3 hardcoded news items; hardcoded KPIs, chart arrays, schedule, priority actions, book stats, workflow stage strip and workflow ID; a 2.5% zakat multiply and a keyword-blacklist "screening"; a hardcoded 7-node family graph.
- **Decorative**: three "approval gates" that return labels; provenance chips that are literal JSX; confidence numbers that are literals; a version string `"v1.2"`; a `"database": "connected"` health check (`main.py:48`, `# TODO: Add actual DB health check`) and `"copilot": "active"` (`:51`).
- **Unexecuted**: **57** `demo_data/` files (43 CSV + 12 JSON + 1 `checksums.sha256` + 1 `README.md`), read by **zero** code paths, describing a future generator; plus 2 orphaned/dead code units (`hubspot_service.py`, `workflowApi`). *Count reconciliation (agreed across all three deliverables):* the pack's own README declares "the 51 emitted data files PLUS a 52nd control-file verification line" (`demo_data/README.md:73-79`) and `checksums.sha256` has 52 non-comment lines — those are *checksummed* data files, a subset. `ls -ld demo_data` prints `drwxr-xr-x 59` — that `59` is the **directory link count** (2 + 57 entries), **not** a file count, and is the source of an earlier "59" in this review. **57 is the canonical file count** (`find demo_data -type f | wc -l`), matching `02_Implementation_Feature_Audit.md` §1–§2 and `GAP_ANALYSIS_RM_WORKBENCH.md` §1–§2. *Citation-stability note:* cross-document references in this review use **section anchors, not absolute line numbers** — 02 and the gap analysis are still being edited by team-lead, so line numbers would silently drift. All `file:line` references elsewhere in this review point to frozen **repository source files** (`backend/app/**`, `frontend/**`, `demo_data/README.md`, root docs), not to teammate deliverables.
- **Broken at runtime**: `GET /api/v1/dashboard/my-day` — the primary UI endpoint — returned **4× HTTP 500 and 8× 200** across 12 calls in `backend.log`; `POST /api/v1/crm/sync` returned **404 twice**. The tagline `main.py:41` — *"AI orchestrates the workflow. You orchestrate the relationship."* — is a string in a JSON response, not behaviour.

**Live-probe deltas (from `release-integrator`, `02_Implementation_Feature_Audit.md` §3.6 and §4.4 — cited by section, not line number).** My review read code bodies and `backend.log`; their audit also ran live HTTP probes, which surfaced three facts a static read cannot see, all of which **strengthen** this verdict:

1. **The live DB has drifted from the checked-in seed script.** `seed_demo_data.py:112-116` defines **3** holdings for Kenneth Wong, but `GET /clients/{id}/portfolio` returns only **2** (`0005.HK`, `00700.HK`); `is_family_office` is **`False`** for Tan Family Office in the live DB although `seed_demo_data.py:81` sets `True`; and `source_kind` is **`null`** on holdings. Precise wording for the pack: **"3 seeded clients / 2 live holdings / 2 interactions"**. This is a further provenance failure (a `null` `source_kind` on a holding) and means even the small real data layer is not the state the repo claims.
2. **Two frontend↔backend contract defects return 422** (already folded into §2.2 above): `workflow/start` and `workflow/extract-insights` declare query params while the frontend posts JSON bodies.
3. **`/openapi.json` exposes 27 paths** = 25 under `/api/v1` + `GET /` + `GET /health`. Note 02 §2.1 now correctly says "all 25 `/api/v1` operations", so **the pack is internally consistent at 25 / 27**; an earlier "26 registered routes" draft has been superseded by team-lead's rewrite. No action needed.

The repo's own footer admits it: `page.tsx:383-389` renders `SYNTHETIC DEMO DATA` / `"Demo environment • All data synthetic • Not for production use"`. **The frontend is honest; the README is not.**

### 8.3 README claim audit (contract vs claim)

| `README.md` claim | Verdict | Code evidence |
|---|---|---|
| `:3` "Full Stack Implementation … **AI-powered copilot orchestration**" | ❌ False | §2 — `orchestrate_workflow` is a static dict. |
| `:12` "**AI**: OpenAI/Anthropic for copilot orchestration" | ⚠️ Misleading | One real completion endpoint exists, but it is not orchestration. |
| `:177` "✅ Client Ranking Algorithm" | ⚠️ Partial | Deterministic arithmetic exists; no reason/evidence model, no outcome learning (FR-12/13). |
| `:178` "✅ Market Data Integration – Tiger Broker real-time quotes and news" | ❌ False | `market_service.py:41,46,81` — all mock; `base_url` unused, zero vendor HTTP calls. |
| `:179` "✅ Brief Generation – AI-powered 5-section client briefs" | ⚠️ Partial | One real LLM call, but empty context, hardcoded frontend copy, silent fallback. |
| `:180` "✅ **Three Approval Gates**" | ❌ False | Three endpoints returning literals; no state, no enforcement (§4). |
| `:181` "✅ **Provenance Tracking – Evidence chips on every AI statement**" | ❌ False | Hardcoded labels + JSX chips; no per-statement source IDs/links (§5). |
| `:182` "✅ Shariah Compliance – Screening, zakat calculation, reporting" | ❌ False | Placeholder that can never fail at its only call site (§7). |
| `:319` "**All features implemented** according to the design specifications" | ❌ False | No product search, suitability engine, transcription, consent capture, D5 service, telemetry, or eval suite. |

### 8.4 Copilot maturity: **1.0 / 5**

Scale defined up front, then applied:

| Level | Criteria | This repo |
|---|---|---|
| **0** | No AI invocation at all; pure static UI. | ✗ (a real LLM call exists) |
| **1** | ≥1 real LLM invocation producing content, but no grounding, no persisted artifacts, no enforced gates, no orchestration. | ✅ **← HERE** |
| **2** | Grounded generation on real entitled data + persisted versioned artifacts + server-side enforced approval gates + real provenance. | ✗ |
| **3** | Skill registry + orchestrator chaining ≥2 skills with shared context and a persisted state machine. | ✗ |
| **4** | D5 persistent memory/graph + closed outcome→ranking→brief loop + correlated telemetry, versioning, kill switch, audit. | ✗ |
| **5** | PRD-complete: ≥85% cross-skill completion, ≥70% single-entry orchestration, entitlement enforcement, eval suite as release gate, zero-retention. | ✗ |

**Score = 1.0/5**, awarded solely because one genuine, UI-reachable LLM completion exists. Deductions are not recoverable by adding more prompts: the missing 4 levels are **architecture**, not model access. PRD Section 3 sits at level 4–5.

---

## 8.5 Frozen C-01…C-16 qualification checklist (adopted from req-analyst, `01_PRD_Requirement_Inventory.md` §11.3)

The req-analyst supplied a frozen 18-item YES/NO contract. I adopt its decision rule verbatim (`01_PRD_Requirement_Inventory.md` §11.3, "Decision rule" — cited by section, not line number):

1. An implementation qualifies as **"the AI Copilot" of PRD v1.1 only if C-01…C-16 are ALL YES.**
2. **Any single NO ⇒ "a collection of AI point features, not the PRD's copilot."** Extra features or more LLM calls do not compensate.
3. **Independently disqualifying:** `C-01`, `C-04`, `C-05`, `C-12`.
4. `C-17` / `C-18` are pilot-tier — **not** gaps for a V1 core GA (Epics 1–3) claim.
5. `C-03` is an **[INFERENCE]**; if rejected, reclassify as supporting evidence — C-01, C-02, C-11, C-12 still independently require skill-level identifiability and stage-level control.
6. `C-06` / `C-07` are numeric targets: the gap is the **missing measurement path** (TEL-08, M-05, M-06), not an unmet percentage.

### Result: **0 YES / 16 NO — 4 independently disqualifying NOs. Verdict unchanged and now mechanically determined, not a judgement call.**

The `Related requirement IDs` column lets the final report express each finding in the PRD's own control IDs without a second mapping pass. IDs are taken from `01_PRD_Requirement_Inventory.md` §2–§11 and were verified against that document before use; all listed IDs are **Tier A** per its §12.2, which deliberately mixes **P0 features** with **pre-production / gating Dependencies** (both GA-blocking): `D5`, `GOV-02`, `NFR-05`, `NFR-06`, `NFR-10`, `NFR-11`, `GATE-01`, `TEL-10` are priority *Dependency*, not P0. `GOV-06` (compliance ownership) is Tier B and is deliberately not listed. `§2.2 WF-01…04` are **workflow definitions / section references**, not counted controls (§15 supplementary content; excluded from the 111 total) — cited for C-01/C-15 because §2.2 is the source of "same copilot skills and client memory — not separate modules".

| Check | Verdict | Decisive code evidence (verified in this review) | Related requirement IDs (Tier-A: P0 / Dependency) |
|---|---|---|---|
| **C-01** | ❌ **NO — disqualifying** | Six flat independent routers (`api/v1/__init__.py:10-15`); `orchestrate_workflow()` returns a static dict (`copilot_service.py:177-199`); `workflowApi` never called (`lib/api.ts:73-88`). The two prompts are standalone point features; the RM is the integration layer. | §3, §1.1, §1.2, §2.2 WF-01…04 (section refs); GATE-01; M-05 |
| **C-02** | ❌ NO | Only the Experience layer exists, as a static dashboard (`page.tsx`). No Orchestration, Context (D5), Skills or Trust layer. `ArtefactState` (`models.py:22-30`) is a decorative enum. | §3 Fig. 1; D5 (§2.3); GATE-01 |
| **C-03** | ❌ NO *(M\*, [INFERENCE] — downgrade to supporting evidence does not change the verdict)* | No skill registry/catalog, no invocable versioned skills, no skill invocation chain, no stage-level control. No `skill` abstraction exists anywhere in `backend/app`. | §3, §1.1; TEL-08; GOV-07; §13 (inference) |
| **C-04** | ❌ **NO — disqualifying** | No D5 service. `FamilyGraphModal.tsx:22-95` is a hardcoded 7-node ECharts object with **no API call**; `models.py:114-139` is a flat interaction log; `demo_data/README.md:16-22` declares the graph/memory CSVs "DATA, not … application code". | D5 (§2.3); §3; GATE-01; FR-5.1 |
| **C-05** | ❌ **NO — disqualifying** | `ranking_service.py:22-83` reads only seeded `Client`/`Holding`/`Interaction` + an in-memory argument — never a meeting outcome. `briefs.py:41` passes `interaction_history = []`, so briefs never carry preferences. `workflow.py:82` claims `d5_memory_update` but executes nothing. No loop. | §3; FR-13; FR-05; M-06; FR-03 |
| **C-06** | ❌ NO | No chained skills exist (0%) **and** no TEL-08 / M-06 measurement path. Per rule 6 the gap is the absent instrumentation, not the unmet percentage. | M-06; TEL-08; §3 |
| **C-07** | ❌ NO | No single entry point (`workflowApi` unused; 4-step strip is static JSX at `page.tsx:97-115`); no M-05 measurement path. | M-05; §1.4; TEL-08 |
| **C-08** | ❌ NO | `copilot_service.py:49-84` post-hoc literal labels with `datetime.now()` (generation time, not as-of); no source records, links, material factors; confidence literals `0.85` (`:236`), `0.92` / `1.0` (`BriefModal.tsx:42,57`); `BriefModal.tsx:31-60` injects hardcoded copy. See the `market_news` fabrication note below. | **FR-02, FR-03, B-01, B-04, GOV-03, NFR-07, INT-03, TEL-01, GRD-09, GOV-07** |
| **C-09** | ❌ NO | Gates are TODO-only returns (`briefs.py:64`, `workflow.py:49,69-73`); `ArtefactState` never written; no approver identity check (frontend hardcodes `'Sarah Chen'`, `BriefModal.tsx:77`). `/crm/sync` writes to real HubSpot with **no gate, no approver, no auth** (`crm.py:16-87`) → violates "zero autonomous client actions". | FR-20; GOV-01; FR-07…FR-10; FR-15; §1.5; B-04 |
| **C-10** | ❌ NO | Hardcoded literals `"v1.2"` (`copilot_service.py:52,81`), `"rank.clients v1.2"` (`ranking_service.py:250`); no registry, no representative test sets (**no project tests at all**), no rollback. | GOV-05; FR-22; NFR-06; TEL-10; §13 |
| **C-11** | ❌ NO | Grep for `kill.?switch|feature.?flag` in `backend/app` → 0. `market_service.set_mode()` (`:171-177`) flips a `LIVE`/`REPLAY` **label** only; generated data is identical. No stage exists to disable. | GOV-07; §13; NFR-10; NFR-03 |
| **C-12** | ❌ **NO — disqualifying** | No `copilot_workflow_started/stage_approved/completed/abandoned`, no skill invocation chain, no manual-stitch events. Grep for `telemetry|event_type|emit_event|...` → 0. `correlation_id` is generated at `copilot_service.py:38,186` and **never propagated**; `dashboard.py:80` uses the literal `"8f21a4b2"`. | TEL-08; TEL-10; NFR-10; NFR-06; M-05; M-06 |
| **C-13** | ❌ NO | No retention/training controls, no prompt minimisation, no redaction, no provider-logging configuration, no residency. Client name/AUM/risk profile/preferences are sent to a third-party endpoint (`.env:22`) with no contract in the repo. Real-looking credentials are committed (`.env:9,13,16-18,21`). | GOV-02; NFR-05; NFR-04; §12 |
| **C-14** | ❌ NO | The "Copilot Core skeleton" is a static-dict method bolted alongside point features; `alembic/versions/` is empty; `WorkflowInstance` is never written. Orchestration is not a Q1 foundation here. | GATE-01; §11 Months 1–3 |
| **C-15** | ❌ NO | Epic 4/5 are **separate modules**, contra §2.2 WF-04: `shariah_service.py` is invoked **directly** from `clients.py:101-128`, never through a copilot; `FamilyGraphModal.tsx` is a standalone hardcoded component. | §2.2 WF-04; FR-4.1; FR-5.1 |
| **C-16** | ❌ NO | No cross-skill completion or context-reuse measurement of any kind. *(The "no general-purpose chatbot" half is incidentally satisfied — there is no chat UI at all — but the check is conjunctive.)* | §3; §12; M-06; TEL-08; GRD-09 |

**Notes on applying the rule honestly**

- **Downgrade test (rule 5):** reclassifying C-03 as supporting evidence still leaves **15 NOs** and all four independently disqualifying NOs intact. The verdict does not depend on the inference.
- **C-06 / C-07 (rule 6):** I am **not** marking a gap because ≥85% / ≥70% were not achieved (they are planning targets, per req-analyst §1.2). I am marking it because **TEL-08 does not exist**, so the metrics are unmeasurable. This is the correct gap.
- **C-17 / C-18 (rule 4):** excluded from the V1 core GA verdict. For completeness only: there is no context assembly at all (so no per-node entitlement filtering) and no SSB-reviewed rule packs (`shariah_service.py:24` logs "using stub implementation"). **Neither is counted as a gap.**
- **Scope discipline (`01_PRD_Requirement_Inventory.md` §11.1, "What the PRD does NOT specify"):** I do **not** count as gaps the absence of a chat UI, a named LLM vendor/model, a RAG/agent framework, a specific orchestration engine, a specific skill taxonomy/count, or any language/database. My C-01 / C-02 / C-11 / C-12 findings concern **observable behaviour** — persisted stage transitions, a skill invocation chain, correlated lifecycle events, and the ability to disable a stage while preserving manual workflows — not which library implements them. A 200-line hand-written state machine would satisfy the behaviour; no framework is required.
- **Extra C-08 detail (fabricated as-of claim):** `copilot_service.py:71-76` stamps the `market_news` section with `"source_kind": SourceKind.LIVE_FEED.value, "source": "TigerBroker News"` even though `briefs.py:40` passes `market_signals = []` and `_build_context()` (`:113-115`) emits an empty "Market Signals:" block. The fallback string at `:170` literally reads *"Market news feed temporarily unavailable."* — yet it still receives a "LIVE_FEED / TigerBroker News" provenance stamp. This is a **fabricated source assertion on content that was never supplied**, which is worse than a missing link.

- **One defect, eight Tier-A controls (P0 / Dependency) breached at once** (cross-reference supplied by req-analyst; IDs verified against `01_PRD_Requirement_Inventory.md` §2–§10). The `LIVE_FEED / "TigerBroker News"` stamp is **not** merely a C-08 / GOV-03 issue. It is a single code defect that simultaneously violates eight Tier-A controls — the eight primary IDs (FR-02, FR-03, B-01, B-04, GOV-03, NFR-07, INT-03, TEL-01) are all **P0**; the additional monitoring IDs in the last row also include **Dependency**-priority controls (NFR-10) alongside P0 ones (GRD-09, GOV-07):

  | Control | Requirement (Tier-A: P0 / Dependency) | How `copilot_service.py:71-76` breaches it |
  |---|---|---|
  | **FR-02** | No news or portfolio fact is presented without provenance; every news item links to its source + timestamp | Asserts a source that was never consulted; no link exists |
  | **FR-03** | Missing data produces an explicit "unavailable" state, **never inferred values**; a failed feed must not block other sections | The honest `"Market news feed temporarily unavailable."` fallback (`:170`) is masked by a live-source label |
  | **B-01** | Show partial output with per-section status/as-of time; **never invent or silently substitute data** | Invents a live feed where `market_signals = []` |
  | **B-04** | Low confidence / insufficient evidence → label item, require explicit review, **suppress unsupported client-facing assertions** | Converts an unsupported section into an apparently verified one |
  | **GOV-03** | Explanations must be faithful summaries, **not unsupported rationalizations** | The provenance is unfaithful to the data actually used |
  | **NFR-07** | Material recommendations show source data and timestamps | No source data exists; `datetime.now()` is generation time, not data-as-of |
  | **INT-03** | Market data must respect entitlements, attribution and source timestamps; an unavailable feed must not block unrelated sections | Fakes attribution instead of reporting unavailability |
  | **TEL-01 / NFR-10 / GRD-09 / GOV-07** | `source completeness` is a required telemetry field; data staleness requires an alert; RM-reported unsupported facts must be monitored | No completeness/staleness event is emitted, so the false-green is **invisible to monitoring** |

  **Why this is worse than a missing link:** a *fabricated* provenance assertion converts a fail-safe ("unavailable") into a **false-green an RM can act on** — precisely the "RM distrust or automation bias / blind acceptance / high unsupported-fact reports" risk in §13 row 1 and the GRD-09 guardrail. FR-02's acceptance criteria already fail on *absent* provenance; *wrong* provenance fails it harder and additionally fails B-01's "never invent". This is the strongest single piece of evidence in the review for the Trust-layer verdict, and it is a **P0 code defect, not just a PRD gap** — it warrants its own blocking item (B8 above) independent of the copilot verdict.

**Cross-check:** §8.1's 0-of-8 §3 requirements and §8.4's 1.0/5 grade are consistent with 0-of-16 here. The req-analyst's framing — *"the PRD's AI Copilot is an ARCHITECTURAL definition, not a feature count"* — is exactly the point: adding the missing brief sections, a chat box, or ten more LLM calls cannot convert 16 NOs into a YES.

---

## 9. Q9 — Minimum component set to satisfy the PRD copilot definition, in dependency order

Each item is a **hard prerequisite** of the next. Do not build out of order — the current repo's core mistake was building the Experience layer and the *shape* of the Trust layer as fixtures before the layers beneath them existed.

| # | Component (must build) | Why it must come before the next | Concrete fact it must fix here |
|---|---|---|---|
| **0** | **D0 foundation: authn/authz/RBAC/tenant isolation, secrets management, DB migrations, config contract.** | Nothing can be safely persisted or gated without identity and a real schema. | No `Depends` other than `get_db`; `alembic/versions/` empty; live credentials in `.env`. |
| **1** | **Provenance & version model (contract, frozen).** Typed `Evidence{source_id, source_kind, as_of, ingested_at, link, confidence, version_stamp, correlation_id}`; immutable append-only `AuditEvent` with hash chain; a real `VersionRegistry` for models/prompts/templates/rule-packs. | Every artifact, skill output and telemetry event must carry this envelope. Build it first or you retrofit provenance as labels (exactly what happened). | Replace `copilot_service.py:49-84` literals; actually write `AuditEvent` (`models.py:191-209`). |
| **2** | **D5 Client Memory & Relationship Graph service.** `MemoryFact` (with supersession + state), `GraphNode`/`GraphEdge`, per-node entitlements, and an `assemble_context(client_id, purpose, actor)` API that enforces entitlements **server-side**. | Context assembly (#4) and the closed loop (#6) both read from D5; the orchestrator cannot be grounded without it. | Replace `FamilyGraphModal.tsx:22-95` hardcoded graph; stop treating `Client.preferences` JSONB as memory. |
| **3** | **Skill contracts + registry.** One versioned interface: `Skill(context_refs) → Artifact{sections, per-statement evidence[], confidence, skill_version, idempotency_key}`; register `brief.generate`, `transcript.extract`, `priority.rank`, `outreach.draft`, `product.search`, `suitability.assess`, `shariah.screen`, `zakat.calc`, `family.consolidate`. | The orchestrator (#4) can only chain things with a uniform, typed, idempotent contract. | Replace the two free-text prompts and the hardcoded `ranking_service`/`shariah_service` stubs. |
| **4** | **Orchestrator / persisted stage state machine.** `WorkflowInstance` persisted with stage transitions, skill invocation chain, per-stage evidence/confidence, retry/rollback, correlated telemetry on every transition, **stage-level kill switch**. | Gates (#5) and the closed loop (#6) are transitions/edges of this machine; they cannot exist as standalone endpoints. | Replace `orchestrate_workflow()` (`copilot_service.py:177-199`) and the six flat routers' ad-hoc calls. |
| **5** | **Mandatory human approval gates, server-side.** Gate 1 brief, Gate 2 consent, Gate 3 review — persisted `ArtefactState` transitions + approval tokens; **hard write protection**: no CRM write / no send / no trade ticket before a valid token. | The Trust layer is meaningless until writes are actually blocked. | Delete or gate `crm.py:16-140` and `scripts/sync_to_hubspot.py`; adopt the orphaned `hubspot_service.py:59-100` two-phase pattern; stop reporting fake `actions_executed` (`workflow.py:80-84`). |
| **6** | **Closed feedback loop.** Outcome capture → ranking model; ranking → next briefs; briefs read latest preferences from D5; preference writes only from Gate-3-approved extractions. | This is the defining behaviour of PRD §3's copilot; without it you have independent features. | `ranking_service.rank_clients()` must consume outcomes; `briefs.py:39-41` must pass real assembled context. |
| **7** | **Grounded data adapters.** Real entitled market/product/KYC/suitability feeds with as-of stamps, partial-failure degradation, stale/conflict labelling, no invented values. | A copilot cannot be explainable on `hash()` data. | Replace `market_service.py:38-169` mocks and the 3 hardcoded news items. |
| **8** | **Telemetry + governance.** PRD §10.2 event taxonomy with tenant-safe `correlation_id` propagated end-to-end; model/prompt/template/rule-pack versioning + rollback; feature/stage kill switch; zero-retention controls; drift/hallucination monitoring; admin config versioning (FR-22). | Required to *measure* the ≥85% / ≥70% targets at all. | Replace `logger.info` with correlated events; remove hardcoded `"8f21a4b2"`. |
| **9** | **End-to-end orchestration eval suite (release gate).** Cross-skill task completion, context reuse, provenance completeness, entitlement-leakage red-team, hard-stop/override tests, gate-bypass tests, provider-failure degradation. | PRD §13 calls these a hard release gate; without them no "completed implementation" claim is testable. | No project tests exist today. |
| **10** | **Single copilot entry point (Experience layer)** + instrumentation of the ≥70% orchestration rate. | Last, because it is a *surface* over #1–#9, not a substitute for them. | Replace the 4-step static JSX strip (`page.tsx:97-115`) with live state. |

**Shortest honest alternative:** if the goal is a leadership demo rather than PRD V1, do **not** build #1–#10. Relabel the repo as *"RM Workbench demo: dashboard + LLM-assisted brief draft (synthetic data, no orchestration)"*, delete the "copilot / three gates / provenance on every statement / all features implemented" claims from `README.md`, and treat `demo_data/` and `designs/` as the design specification they are. That is a legitimate, defensible scope. What is not defensible is the current labelling.

---

## 10. Blocking gaps (must fix before the label "AI Copilot" may be used)

| # | Location | Problem | Contract basis | Required fix |
|---|---|---|---|---|
| B1 | `copilot_service.py:177-199` | `orchestrate_workflow` returns a static dict with `"stages": []`; no orchestration exists | PRD §3, §3 closed loop | Implement persisted stage machine + skill chain (§9 #4). |
| B2 | `briefs.py:31-45` | LLM brief generated from hardcoded client + three empty lists; `client_id` ignored | FR-01/02/14, §8 grounding | Assemble real entitled context via D5 (#2, #6). |
| B3 | `workflow.py:62-89` | Gate 3 returns `actions_executed: [crm_sync, d5_memory_update, email_draft_saved]` that never run; false success | FR-07, §6 "never show false success" | Delete fake list; execute only approved, audited actions. |
| B4 | `briefs.py:57-74`, `workflow.py:42-60` | Gates 1 & 2 persist nothing; no sequencing check between gates | FR-20, §8 human-in-the-loop | Persisted `ArtefactState` + approval tokens + transition guards. |
| B5 | `crm.py:16-140`, `scripts/sync_to_hubspot.py:10-71` | Unguarded, unauthenticated, non-idempotent external CRM writes | FR-07/08/15, D0 | Gate behind approval token; add authn/RBAC; idempotency keys; old/new preview. |
| B6 | `crm_service.py` **vs** `hubspot_service.py`; `crm/__init__.py:4` | Duplicate `CRMService` implementations; the safe two-phase one is orphaned dead code | Iron Law 1 (no duplicate wheels) | Delete one; wire the pending-approval/execute split. |
| B7 | `copilot_service.py:153-155`, `:89-91` | LLM failure silently downgrades to hardcoded fallback but still logs/reports success and attaches provenance | §6, §8 faithfulness | Distinguish degraded state; surface status; never attach fake provenance. |
| B8 | `copilot_service.py:49-84`, `BriefModal.tsx:31-67,137-141`, `page.tsx:303-309` | Provenance/confidence are hardcoded labels, JSX chips and literals | FR-02, §8 | Per-statement evidence with source IDs, links and as-of stamps; real confidence. |
| B9 | `FamilyGraphModal.tsx:22-95`, `models.py:114-139` | No D5 memory/graph service; entitlements rendered, not enforced | D5, FR-5.1 (hard release gate) | Build #2 with server-side entitlement filtering in context assembly. |
| B10 | `backend/app` (grep) | No telemetry, no version registry, no kill switch, no audit writes, no zero-retention controls, no tests | §8, §10.2, §13 | Build #8 and #9. |
| B11 | `market_service.py:41,46,81-107`, `:25/:29-36` | "Real-time" market data is `hash()` mocks + 3 hardcoded news; zero vendor HTTP calls | FR-02, §9, §6 | Real entitled adapters with as-of stamps (#7). |
| B12 | `clients.py:101-105,120`, `shariah_service.py:37,56-64,98` | Screening placeholder can never fail at its only call site; zakat is a 2.5% multiply with a hardcoded hawl date | FR-4.1/4.2/4.3 | Versioned rule packs with per-criterion evidence + SSB sign-off. |
| B13 | `README.md:3,12,177-182,319`; `MARKET_NEWS_AND_LLM.md:5,53` | "AI-powered copilot orchestration", "Three Approval Gates", "Evidence chips on every AI statement", "All features implemented" | Contracts frozen | Relabel to the true reduced scope, or rebuild. |
| B14 | `.env:9,13,16-18,21` (values redacted) | Real-looking credentials committed; no auth on any endpoint | §7 Security, D0 | Rotate, move to secrets manager, `.gitignore`, add authn. |

## 11. Non-blocking observations

> **Severity-scope note (cross-deliverable consistency).** The §10/§11 split is a **verdict-gating** partition only: "blocking" = must be fixed before the label "AI Copilot" may be used; "non-blocking" = does not change the §0 verdict. It is **not** a fix-priority scale. In particular **N9 is a P1 / privacy defect** (`02_Implementation_Feature_Audit.md` §4.1 addendum; `GAP_ANALYSIS_RM_WORKBENCH.md` §7, defect 26 — "P1 / privacy, not a P0-GA blocker") and must be fixed before any production handling of client transcripts. Do not read "non-blocking" here as "optional" or "low severity". Likewise B14 sits in §10 because an unauthenticated external write fails the Trust layer, not because of its fix priority.

| # | Location | Observation |
|---|---|---|
| N1 | `copilot_service.py:1-5`, `README.md` | Docstrings/comments are in English and are largely `# TODO` placeholders or restatements of the obvious (`"""Generate a client brief (Gate 1)"""`). No comment explains a non-obvious *why*. Iron Law 2 asks for Chinese WHY-comments at critical logic/boundary points; none exist. Not blocking for a capability audit, but required for any accepted patch. |
| N2 | `requirements.txt:14` (`pgvector`), `market_service.py:8-11` (4 unused imports), `config.py:9`, `requirements.txt:25-26` | Unused dependencies/imports suggest planned capability rather than implemented capability. Remove until used. |
| N3 | `models.py:22-30` (`ArtefactState`, 8 states), `:16-20` (`WorkflowStage`) | Vocabulary defined, state machine absent. Either implement or delete; do not leave decorative enums. |
| N4 | `BriefModal.tsx` + `app/brief/[clientId]/page.tsx` | Two near-identical brief UIs with duplicated hardcoded fallback copy. Consolidate into one component. |
| N5 | `frontend/lib/api.ts:73-88` | `workflowApi` defined but never imported. Delete or wire. |
| N6 | `main.py:44-54` | `/health` reports `"database": "connected"` and `"copilot": "active"` as literals with a `# TODO`. Health checks must probe real dependencies. |
| N7 | `demo_data/README.md:16-22` | This file is the *most* honest artefact in the repo. Promote its honesty posture to the top-level README. |
| N8 | `backend.log` | `GET /api/v1/dashboard/my-day` returned 500 in 4/12 calls and `/crm/sync` 404 twice. Intermittent, not permanent — worth a stability pass but not a copilot blocker. |
| N9 | `workflow.py:108-113`, `frontend/lib/api.ts:87` | Beyond the 422 contract defect (§2.2): because `transcript: str` is declared as a **query parameter**, any correctly-formed call would place the **entire client meeting transcript in the URL query string**, where it lands in access logs, proxy logs and browser history. This conflicts with NFR-05 (privacy/residency), GOV-02 (zero provider retention / prompt minimisation) and the PRD's retention/deletion policy for transcripts. Fix the contract with an explicit Pydantic request model, not by moving data into the URL. |

## 12. Checklist verification

| Check item | Result |
|---|---|
| Contract consistency (PRD §3, §1.1, §2.2, §8, §10) | ❌ **Fail** — 0 of 8 §3 requirements implemented (§8.1 table). |
| Scope compliance (claimed vs delivered) | ❌ **Fail** — 6 of 9 README "Features Implemented" claims false/misleading (§8.3). |
| No duplicate implementation | ❌ **Fail** — two `CRMService` classes, 3 CRM write paths, 2 brief renderers (§2.4). **One-vote rejection under Iron Law 1.** |
| Simplicity / no over-abstraction | ❌ **Fail** — unused enums, unused `pgvector`, unused imports, dead `_sign_request`, static-dict "orchestrator". |
| Comment discipline (Chinese WHY-comments at boundaries) | ❌ **Fail** — English `# TODO` placeholders only. |
| Boundary / exception handling | ❌ **Fail** — silent LLM fallback reported as success; no partial-data states; no idempotency; no retries. |
| Security risk | ❌ **Fail** — no authn/RBAC/tenant isolation; unguarded external CRM writes; committed credentials. |
| Real LLM invocation | ✅ **Pass (partial)** — one working path, 2 call sites, verified 200 OK in log. |
| Real persistence layer | ✅ **Pass (partial)** — Postgres CRUD for 3 seeded clients; **live DB has drifted from the seed script** (2 live holdings vs 3 declared, `is_family_office=False`, `source_kind=null`) — see §8.2 live-probe note. |
| Approval gates / provenance / telemetry / D5 / eval | ❌ **Fail** — all absent or decorative. |
| Deliverable written to disk (Iron Law 4) | ✅ **Pass** — this file. |
| Application code modified | ✅ **None** — review only, as instructed. |

## 13. Re-review requirements

A re-review will only be scheduled when the following are supplied together:

1. A **single entry point** that executes a 2+ skill chain with a persisted `WorkflowInstance`, with a request/response trace showing stage transitions and the skill invocation chain.
2. A **D5 context-assembly** call whose output is actually fed into the brief prompt, plus an entitlement-leakage test proving cross-entity data is filtered server-side.
3. **Server-side gate enforcement**: a test proving `POST /crm/sync` (and any send/trade path) is rejected without a valid Gate-3 approval token, and that the approval is written to an immutable audit log.
4. **Per-statement provenance** on a generated brief with resolvable source IDs, links, and data-as-of timestamps (not generation time).
5. **Correlated telemetry** for one full workflow showing model/prompt/rule-pack versions and a stage-level kill switch demonstration.
6. An **eval suite** reporting cross-skill task completion and context reuse against a representative test set.
7. An updated `README.md` whose claims match the delivered behaviour.

Until then the verdict remains 🔴 **退回重做** for the copilot claim.

---

## Appendix A — Evidence index (all quoted lines verified by reading file bodies)

**Backend services**
- `backend/app/services/copilot/copilot_service.py` — `:9`, `:20-24`, `:27-91`, `:37-46`, `:48-84`, `:86-91`, `:93-121`, `:123-155`, `:157-175`, `:177-199`, `:201-244`, `:247`
- `backend/app/services/ranking/ranking_service.py` — `:16-20`, `:22-83`, `:85-121`, `:123-156`, `:158-201`, `:203-231`, `:233-255`
- `backend/app/services/market/market_service.py` — `:8-11`, `:25`, `:29-36`, `:38-71`, `:73-113`, `:115-140`, `:142-169`, `:171-177`
- `backend/app/services/shariah/shariah_service.py` — `:15-24`, `:26-70`, `:72-118`, `:124-148`, `:150-193`
- `backend/app/services/crm/crm_service.py` — `:13-15`, `:48-100`, `:102-152`, `:154-169`
- `backend/app/services/crm/hubspot_service.py` — `:11-13`, `:15-67`, `:69-100`, `:103` (orphaned)
- `backend/app/services/crm/__init__.py` — `:4`

**Endpoints / app**
- `backend/app/api/v1/endpoints/briefs.py` — `:15-22`, `:24-55`, `:57-74`, `:76-92`
- `backend/app/api/v1/endpoints/workflow.py` — `:15-23`, `:25-40`, `:42-60`, `:62-89`, `:91-106`, `:108-126`
- `backend/app/api/v1/endpoints/dashboard.py` — `:18-88`, `:90-112`, `:114-132`, `:134-154`, `:156-186`
- `backend/app/api/v1/endpoints/clients.py` — `:27-62`, `:64-83`, `:85-134`
- `backend/app/api/v1/endpoints/market.py` — `:12-78`
- `backend/app/api/v1/endpoints/crm.py` — `:16-87`, `:90-140`, `:143-162`
- `backend/app/api/v1/__init__.py` — `:10-15`
- `backend/app/main.py` — `:12-18`, `:35-54`
- `backend/app/models/models.py` — `:9-30`, `:33-66`, `:68-90`, `:93-112`, `:114-139`, `:141-172`, `:174-189`, `:191-209`
- `backend/app/core/config.py` — `:5-60`; `backend/app/core/database.py` — `:15-46`
- `backend/app/scripts/init_db.py`, `seed_demo_data.py` (`:35-93`, `:102-128`, `:130-178`), `sync_to_hubspot.py` (`:10-71`)
- `backend/alembic/versions/` — empty; `backend/app/schemas/` — empty

**Frontend**
- `frontend/lib/api.ts` — `:13-88`
- `frontend/components/BriefModal.tsx` — `:25-73`, `:75-84`, `:118-183`, `:188-208`
- `frontend/app/brief/[clientId]/page.tsx` — `:18-38`, `:69-133`, `:136-150`
- `frontend/app/page.tsx` — `:18-48`, `:79-124`, `:135-180`, `:222-315`, `:316-375`, `:378-406`
- `frontend/components/FamilyGraphModal.tsx` — `:16-95`, `:97-173`, `:219-244`

**Config / docs / runtime**
- `.env` — `:9`, `:13`, `:16-18`, `:20-23`, `:36` (values redacted in this report); `.env.example` — `:17-29`, `:42`
- `backend/requirements.txt` — `:14`, `:17`, `:19-20`, `:25-26`, `:32-34`
- `README.md` — `:3`, `:8-13`, `:174-196`, `:198-222`, `:231-244`, `:317-325`
- `MARKET_NEWS_AND_LLM.md` — `:5`, `:8-17`, `:53`, `:55-111`
- `backend.log` — `:8`, `:72`, `:120`, `:172`, `:220`, `:359-362`, `:699-701` (12 `my-day` calls: 8×200 / 4×500)
- `demo_data/README.md` — `:1-3`, `:16-22`, `:24-35`, `:64-81`, `:83-94`
- `demo_data/`: `artefacts.json`, `memory_facts.csv`, `graph_nodes.csv`, `graph_edges.csv`, `workflow_stages.csv`, `workflow_instances.csv`, `approval_tokens.json`, `audit_events.csv`, `version_registry.csv`, `config_versions.csv`, `transcript_utterances.csv`, `extraction_items.csv`, `suitability_state.csv`, `entitlement_decisions.csv`, `demo_sink_messages.csv`, `consent_state.csv`
- Contract: `/tmp/prd_full.txt` — §1.1 (`:42-48`), §2.2 (`:74-78`), §2.3 D5 (`:85`), §3 (`:86-90`), §6 (`:165-181`), §8 (`:200-208`), §10.1 (`:226-241`), §10.2 (`:243-253`), §13 (`:283-298`)

## Appendix B — Relation to other audit deliverables

`deliverables/GAP_ANALYSIS_RM_WORKBENCH.md` (team-lead) independently reaches the same verdict ("NOT an AI copilot", "1/5", "two real, working LLM calls", "dashboard + two scripted LLM text-generation endpoints over a 7-table CRUD database") and frames the root cause as "three different products in one repository". This review is the **independent code-level substantiation** of that verdict and adds: exact line citations, the duplicate-`CRMService` / orphaned-safe-implementation finding, the silent-fallback false-success finding, the unguarded CRM write + missing auth security finding, the "static fixtures describe a non-existent system" finding, and the dependency-ordered minimum component set.

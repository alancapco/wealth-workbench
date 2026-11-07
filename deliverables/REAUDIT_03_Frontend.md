# REAUDIT 03 — Frontend

**Repository:** `/Volumes/Orico/code/capco/wealth-workbench`
**Scope:** `frontend/` (read-only), cross-checked against `backend/app/api/v1/`
**Auditor role:** frontend-auditor
**Date:** 2026-11-07
**Constraint:** No application file was modified. Only this report was written. No `npm install`, no server started.

### Claim under test (G-26)

> "G-26 Frontend↔backend contract fixes — Frontend can now call APIs without 422 errors."
> — `PROGRESS.md:55-58` ("Fixed briefApi.generate() to use correct URL format / Fixed approval endpoint payload structure / Updated workflow/start endpoint / Impact: Frontend can now call APIs without 422 errors")

**Verdict: FALSE, and the change was regressive.** The frontend source was not touched (`frontend/lib/api.ts` mtime 2026-11-07 00:02; all other frontend files 12:07–12:42; the backend "fixes" are 15:31–15:37). The backend changed its route shapes underneath an unchanged client, converting the two brief calls into guaranteed **404**s, leaving the workflow **422** defect untouched (it is now merely *latent*, because the `workflowApi` wrapper is never imported), and — independently — the backend cannot currently start at all, so every call is a connection failure.

Scorecard:

| G-26 sub-claim | Verified result |
|---|---|
| briefApi.generate() uses "correct URL format" | **False.** Frontend posts to `/briefs/generate`; backend only serves `/briefs/generate/{client_id}`. 404. |
| approval endpoint payload "fixed" | **False.** Frontend posts JSON to `/briefs/approve`; backend only serves `/briefs/approve/{brief_id}?approver=`. 404 (and 422 if the path were corrected without the query parameter). |
| workflow/start "updated" | **False.** Frontend still sends a JSON body; backend declares two required **query** parameters. The wrapper was never changed, so a future call would 422. |
| "without 422 errors" | **False, and vacuous.** No *live* call site produces 422 today only because the two workflow methods are never invoked and the two brief calls 404 first. The 422 defect is unfixed, not eliminated. Of the 5 live call sites: 2 × 404, 3 × contract-OK but unreachable (process down). **Zero succeed.** |
| Frontend was modified to match | **False.** No frontend file was modified after 12:42. |

---

## 1. Preconditions — nothing on this stack can be exercised

### 1.1 The backend does not boot (blocking all HTTP verdicts)

`backend/app/services/market/market_service.py:13`

```python
from app.models.models import MarketTick, SourceKind
```

`backend/app/models/models.py` is 99 lines and defines only `Client`, `Holding`, `Interaction`, `Brief`, `AuditLog`. There is no `MarketTick` and no `SourceKind` (verified by reading the whole file and by `grep -rn "MarketTick" backend/app` → only the import sites).

Because `backend/app/api/v1/__init__.py:5` imports `market` at package-import time, FastAPI cannot load:

```
backend.log (written 16:30):
  File ".../app/api/v1/endpoints/market.py", line 6, in <module>
    from app.services.market.market_service import market_data_service
  File ".../app/services/market/market_service.py", line 13, in <module>
    from app.models.models import MarketTick, SourceKind
ImportError: cannot import name 'MarketTick' from 'app.models.models'
```

`backend/app/scripts/init_db.py:7` imports `MarketTick` too, so the seed path is equally broken.

Process check: `backend.pid` = `14829`; `ps -p 14829` returns nothing; nothing listens on `:8000`.

**Consequence for this audit:** every frontend verdict below is a *static contract* verdict derived from route declarations. At runtime today the answer for 100% of calls is `net::ERR_CONNECTION_REFUSED`, i.e. the failure mode is strictly worse than the 404/422 analysis. (Backend ownership: reported to `backend-auditor`; not claimed as a frontend defect.)

### 1.2 The frontend does not typecheck

`frontend/tsconfig.json:5` sets `"strict": true`; `next.config.js` does not set `typescript.ignoreBuildErrors`.

```
$ ./node_modules/.bin/tsc --noEmit
components/FamilyGraphModal.tsx(125,9): error TS2322: Type '{ type: "graph"; ... }' is not assignable to type 'SeriesOption$1 | SeriesOption$1[] | undefined'.
  Types of property 'links' are incompatible.
    Type '{ source: string; target: string; value: string; }' is not assignable to type 'GraphEdgeItemOption[]'.
      Types of property 'value' are incompatible.
        Type 'string' is not assignable to type 'number'.
TSC_EXIT=1
```

Root cause: `FamilyGraphModal.tsx:82-87` declares `value: 'full' | 'education-only' | 'restricted'` (strings) on graph links, which ECharts types as `number`. `next build` in Next 14 runs "Linting and checking validity of types", so the production build fails.

There is also no ESLint config file (`.eslintrc*` absent) while `package.json:9` defines `"lint": "next lint"`, so `npm run lint` is interactive-only and unusable in CI.

### 1.3 Frontend has not changed since the backend rewrite

| File | mtime |
|---|---|
| `frontend/lib/api.ts` | 2026-11-07 **00:02** |
| `frontend/app/brief/[clientId]/page.tsx` | 2026-11-07 **12:07** |
| `frontend/components/BriefModal.tsx` | 2026-11-07 **12:16** |
| `frontend/app/page.tsx` | 2026-11-07 **12:42** |
| `backend/app/api/v1/endpoints/briefs.py` | 2026-11-07 **15:33** |
| `backend/app/services/brief/brief_service.py` | 2026-11-07 **15:32** |

The backend moved ~3 hours after the last frontend edit. No frontend adaptation exists.

---

## 2. A — Contract matrix

`frontend/lib/api.ts` exports **21 methods across 5 objects**. There is no `crmApi` (CRM endpoints are 100% uncalled). Base URL is `http://localhost:8000/api/v1` (`api.ts:3-6`), so all paths below are relative to `/api/v1`.

Legend: **WORKS** = path + parameter location + payload shape all agree. "Contract only" means static agreement; the server is currently down (§1.1).

| # | Frontend call (`lib/api.ts`) | Backend route / signature | Contract verdict |
|---|---|---|---|
| 1 | `GET /dashboard/my-day?rm_id=RM001` (:14-15) | `GET /dashboard/my-day`, `rm_id: str = "RM001"` — `dashboard.py:18-22` | **WORKS** (contract only) |
| 2 | `GET /dashboard/kpis?rm_id=...` (:17-18) | `GET /dashboard/kpis` — `dashboard.py:90-94` | WORKS, but backend body is hardcoded (`:99-109`) |
| 3 | `GET /dashboard/book-stats?rm_id=...` (:20-21) | `GET /dashboard/book-stats` — `dashboard.py:114-118` | WORKS, backend hardcoded (`:123-129`) |
| 4 | `GET /dashboard/allocation?rm_id=...` (:23-24) | `GET /dashboard/allocation` — `dashboard.py:134-137` | **WORKS** (contract only) |
| 5 | `GET /dashboard/performance-trend?rm_id=..&period=ytd` (:26-27) | `GET /dashboard/performance-trend` — `dashboard.py:156-160` | **WORKS**; backend data is mock (`:165-168`) |
| 6 | `GET /market/quotes?symbols=a,b` (:32-33) | `GET /market/quotes`, `symbols: str = Query(...)` — `market.py:12-15` | WORKS |
| 7 | `GET /market/news?symbols=a,b?limit=20` (:35-36) | `GET /market/news`, `symbols: Optional[str]`, `limit: int` — `market.py:25-28` | **MALFORMED URL** — double `?` when `symbols` is passed. Backend receives `symbols="a,b?limit=20"`, `limit` falls back to 20. (No caller, so dormant.) |
| 8 | `GET /market/signals?symbols=..&threshold=2` (:38-39) | `GET /market/signals` — `market.py:39-43` | WORKS |
| 9 | `GET /market/historical/{symbol}?period&limit` (:41-42) | `GET /market/historical/{symbol}` — `market.py:57-62` | WORKS |
| 10 | `GET /clients?skip=0&limit=50` (:47-48) | `GET /clients/` (`"/"` route under `prefix="/clients"`) — `clients.py:27-31` | WORKS **via 307 trailing-slash redirect**; no caller, untested |
| 11 | `GET /clients/{id}` (:50-51) | `GET /clients/{client_id}` — `clients.py:44-48` | WORKS |
| 12 | `GET /clients/{id}/portfolio` (:53-54) | `GET /clients/{client_id}/portfolio` — `clients.py:64-68` | WORKS |
| 13 | `GET /clients/{id}/shariah-report` (:56-57) | `GET /clients/{client_id}/shariah-report` — `clients.py:85-89` | WORKS |
| 14 | `POST /briefs/generate` body `{client_id, force_regenerate}` (:62-63) | `POST /briefs/generate/{client_id}` — `briefs.py:14-18` | **404** — no route matches a bare `/generate` |
| 15 | `POST /briefs/approve` body `{brief_id, approved_by, edited_agenda}` (:65-66) | `POST /briefs/approve/{brief_id}`, `approver: str` **required query param** — `briefs.py:36-41` | **404**. Would be **422** even after path correction unless `approver` is sent as a query param; `approved_by` is not a recognised name |
| 16 | `GET /briefs/{id}` (:68-69) | *(no route)* — `briefs.py` declares only `POST /generate/{id}` and `POST /approve/{id}` | **404** — route deleted |
| 17 | `POST /workflow/start` body `{workflow_type, client_id, trigger}` (:74-75) | `POST /workflow/start`, `workflow_type: str`, `client_id: str` (both **query**), `trigger: Dict` (body) — `workflow.py:25-31` | **422** — required query params absent. Only `trigger` is read from the body |
| 18 | `POST /workflow/consent` body (:77-78) | `POST /workflow/consent`, `ConsentRequest` body — `workflow.py:15-18, 42-46` | WORKS |
| 19 | `POST /workflow/review/approve` body (:80-81) | `POST /workflow/review/approve`, `ReviewApprovalRequest` body — `workflow.py:20-23, 62-66` | WORKS |
| 20 | `GET /workflow/{id}` (:83-84) | `GET /workflow/{workflow_id}` — `workflow.py:91-95` | WORKS |
| 21 | `POST /workflow/extract-insights` body `{transcript, client_id}` (:86-87) | `POST /workflow/extract-insights`, `transcript: str`, `client_id: str` (both **query**) — `workflow.py:108-113` | **422** |

**Tally: 15 contract-compatible, 1 malformed URL, 3 hard 404, 2 hard 422, 1 deleted route.** Of the 5 methods that are actually invoked, **0 can succeed**: `generate` and `approve` are 404; `getMyDay`, `getAllocation`, `getPerformanceTrend` are contract-OK but unreachable because the process is down. The two 422 methods (`workflowApi.start`, `workflowApi.extractInsights`) have no caller at all, so their 422 is latent rather than observed.

### 2.1 Second-order contract break the G-26 claim ignores: response shape

Even if every URL were fixed, `briefApi.generate` response is read wrong.

Backend (`backend/app/services/brief/brief_service.py:62-75`):

```python
brief = {
    "brief_id": ..., "client_id": ..., "client_name": ...,
    "sections": {
        "portfolio_overview": portfolio_section,
        "material_changes": changes_section,
        "recent_interactions": interactions_section,
        "market_news": news_section,
        "proposed_agenda": agenda_section,
    },
}
```

Frontend (`BriefModal.tsx:122,126,135,148,156`; `app/brief/[clientId]/page.tsx:75,78,86,99,107`):

```tsx
{brief?.portfolio_overview?.content || 'Portfolio data temporarily unavailable.'}
```

It reads `brief.portfolio_overview`, not `brief.sections.portfolio_overview`. Every section would be `undefined` and render the placeholder string. The `||` fallbacks are exactly why this failure is invisible in the UI (§5).

**Root cause of the divergence (verified):** the repo contains *two* brief generators with different envelopes. `copilot_service._generate_fallback_brief()` returns a **flat** map `{"portfolio_overview": {...}, "material_changes": {...}, ...}` (`copilot_service.py:157-175`), which is the shape this frontend was written against. The live endpoint, however, calls `brief_service.generate_brief` (`briefs.py:7,28`), which wraps everything in `{"sections": {...}}` (`brief_service.py:68-74`). The endpoint was switched to the nested generator without touching the client. Note also that the flat `copilot_service` path is dead code — nothing in `briefs.py` calls it.

**Which shape should win (decision, not preference):** the nested shape is the canonical one. `Brief.sections` is a required JSON column (`models.py:82`), so nested is what persistence and the live endpoint already agree on; the flat generator is unused and should be deleted rather than kept as a second contract. Normalising at the API boundary to `{...sections, brief_id}` is an acceptable alternative, but leaving two shapes in the repo is what produced this defect, so pick exactly one.

### 2.2 `brief_id` is discarded; approve always targets a fake id

`briefApi.generate` never captures `response.data.brief.brief_id`. Approve is hardcoded (`BriefModal.tsx:77`, `app/brief/[clientId]/page.tsx:33`):

```tsx
await briefApi.approve('brief-123', 'Sarah Chen', editing ? editedAgenda : undefined);
```

`'brief-123'` appears twice and nowhere else in the repo — it is not a real brief id. The backend generates `str(uuid.uuid4())` per brief (`brief_service.py:32`). So approval is structurally incapable of addressing the brief that was generated.

### 2.3 KPI field mismatch

`dashboard.py:59-66` (`/dashboard/my-day`) returns `total_aum`, `total_clients`, `meetings_today`, `open_actions`, `ytd_performance`. The page also reads `kpis.actions_overdue` (`page.tsx:166`) — only `/dashboard/kpis` returns that key (`dashboard.py:106`). Result: "0 overdue" is always displayed from the my-day path, while the static Priority Actions block claims "2 overdue" (`page.tsx:338`).

---

## 3. B — Call-site reality

Only **three files** import the API module:

```
app/page.tsx:4              import { dashboardApi, marketApi } from '@/lib/api';
components/BriefModal.tsx:4 import { briefApi } from '@/lib/api';
app/brief/[clientId]/page.tsx:5 import { briefApi } from '@/lib/api';
```

`marketApi` is imported at `app/page.tsx:4` and **never used** in that file.

### 3.1 Method → caller map

| Method | Callers | Status |
|---|---|---|
| `dashboardApi.getMyDay` | `page.tsx:33` | live |
| `dashboardApi.getAllocation` | `page.tsx:34` | live |
| `dashboardApi.getPerformanceTrend` | `page.tsx:35` | live |
| `briefApi.generate` | `BriefModal.tsx:28`, `brief/[clientId]/page.tsx:21` | live (404) |
| `briefApi.approve` | `BriefModal.tsx:77`, `brief/[clientId]/page.tsx:33` | live (404) |
| `dashboardApi.getKPIs` | — | **orphan** |
| `dashboardApi.getBookStats` | — | **orphan** |
| `marketApi.getQuotes` | — | **orphan** |
| `marketApi.getNews` | — | **orphan** (also malformed) |
| `marketApi.getSignals` | — | **orphan** |
| `marketApi.getHistorical` | — | **orphan** |
| `clientApi.getClients` | — | **orphan** |
| `clientApi.getClient` | — | **orphan** |
| `clientApi.getPortfolio` | — | **orphan** |
| `clientApi.getShariahReport` | — | **orphan** |
| `briefApi.getBrief` | — | **orphan** (route no longer exists) |
| `workflowApi.start` | — | **orphan** |
| `workflowApi.recordConsent` | — | **orphan** |
| `workflowApi.approveReview` | — | **orphan** |
| `workflowApi.getWorkflow` | — | **orphan** |
| `workflowApi.extractInsights` | — | **orphan** |

**16 of 21 methods (76%) have zero call sites.** Whole API clients (`clientApi`, `workflowApi`, `marketApi`) are dead code. The entire post-meeting workflow — consent gate, review approval, insight extraction — has no UI at all, yet the header advertises those stages (`page.tsx:106-114`).

### 3.2 Backend routes with no frontend caller

24 routes are registered (`backend/app/api/v1/__init__.py:10-15`). Only 3 have a correctly-shaped caller:

| Route | Declared at | Frontend caller |
|---|---|---|
| `GET /dashboard/my-day` | `dashboard.py:18` | `page.tsx:33` |
| `GET /dashboard/allocation` | `dashboard.py:134` | `page.tsx:34` |
| `GET /dashboard/performance-trend` | `dashboard.py:156` | `page.tsx:35` |
| `GET /dashboard/kpis` | `dashboard.py:90` | none |
| `GET /dashboard/book-stats` | `dashboard.py:114` | none |
| `GET /market/quotes` | `market.py:12` | none |
| `GET /market/news` | `market.py:25` | none |
| `GET /market/signals` | `market.py:39` | none |
| `GET /market/historical/{symbol}` | `market.py:57` | none |
| `POST /market/mode` | `market.py:71` | none |
| `GET /clients/` | `clients.py:27` | none |
| `GET /clients/{id}` | `clients.py:44` | none |
| `GET /clients/{id}/portfolio` | `clients.py:64` | none |
| `GET /clients/{id}/shariah-report` | `clients.py:85` | none |
| `POST /briefs/generate/{client_id}` | `briefs.py:14` | **mismatched** (`/generate`) |
| `POST /briefs/approve/{brief_id}` | `briefs.py:36` | **mismatched** (`/approve`) |
| `POST /workflow/start` | `workflow.py:25` | **mismatched** (would 422) — but `workflowApi` is never imported (§3.1), so no live caller: latent |
| `POST /workflow/consent` | `workflow.py:42` | none |
| `POST /workflow/review/approve` | `workflow.py:62` | none |
| `GET /workflow/{id}` | `workflow.py:91` | none |
| `POST /workflow/extract-insights` | `workflow.py:108` | **mismatched** (would 422) — `workflowApi` never imported: latent |
| `POST /crm/sync` | `crm.py:16` | none |
| `POST /crm/sync/{client_id}` | `crm.py:90` | none |
| `GET /crm/status` | `crm.py:143` | none |

**Counting conventions (both are correct, they answer different questions):** **19 of 24** routes have *no call site anywhere* (17 never had a wrapper; 2 more — `workflow/start`, `workflow/extract-insights` — have a wrapper that is never imported). **21 of 24** have *no valid call site* (19 uncalled + 2 brief routes invoked at non-existent URLs). Only **3 of 24** are invoked correctly.

Notable consequences:

- `/dashboard/book-stats` exists but `page.tsx:354-375` hardcodes the same five numbers.
- `/crm/*` (the entire HubSpot feature that `PROGRESS.md` calls "G-11 ✓") has no UI.
- `/clients/*` — including `shariah-report`, the flagship Islamic-finance feature — has no UI, while the dashboard offers an "Open Brief & Shariah Report" button (`page.tsx:258`) that opens the generic brief modal and shows no Shariah data.
- `/market/mode` (LIVE/REPLAY switch) has no UI, while the header claims LIVE.

### 3.3 Orphaned page

`app/brief/[clientId]/page.tsx` is a complete second brief implementation, but **nothing navigates to it**. No `<Link>` and no `router.push` to `/brief/...` exists anywhere in `app/` or `components/` (`router.push('/')` at `brief/[clientId]/page.tsx:34,54,145` is the only navigation, always *away*). The route is reachable only by typing the URL.

---

## 4. C — Fabricated content re-verification

All items below are **still present**. Line numbers current as of this audit.

| # | Item | Status | Evidence |
|---|---|---|---|
| C1 | `// Enrich with real data if missing` block inventing interactions | **PRESENT** | `BriefModal.tsx:31-45` |
| C2 | Invented "Last meeting (15 days ago)" narrative | **PRESENT** | `BriefModal.tsx:34-38` |
| C3 | Invented confidence `0.92` on fabricated CRM content | **PRESENT** | `BriefModal.tsx:42` |
| C4 | Invented market news ("HSBC +2.3%", "HK Tech Rally") | **PRESENT** | `BriefModal.tsx:47-60` (content `:49-53`) |
| C5 | Hardcoded `'TigerBroker News · LIVE'` provenance | **PRESENT** | `BriefModal.tsx:55` (and backend `brief_service.py:196`, so the string is duplicated in two layers) |
| C6 | Invented confidence `1.0` on fabricated news | **PRESENT** | `BriefModal.tsx:57` |
| C7 | Hardcoded fallback agenda (5 bullets, "daughter attending") | **PRESENT** | `BriefModal.tsx:63-67` |
| C8 | `briefApi.approve('brief-123', 'Sarah Chen', …)` | **PRESENT ×2** | `BriefModal.tsx:77`, `brief/[clientId]/page.tsx:33` |
| C9 | Brief page header hardcodes "Kenneth Wong" | **PRESENT** | `app/brief/[clientId]/page.tsx:59` |
| C10 | Header LIVE chip driven by `setInterval` browser clock | **PRESENT** | `page.tsx:22-24` (1 s interval) → `:92-93` |
| C11 | Inconsistent source names: Reuters / TigerBroker / TigerBroker News | **PRESENT** | Reuters `page.tsx:306`; TigerBroker `BriefModal.tsx:139`, `brief/[clientId]/page.tsx:90`; "TigerBroker News · LIVE" `BriefModal.tsx:55`; backend "TigerBroker News" `market_service.py:88` |
| C12 | "Open Brief" passes `clientId='demo'` when `rankedClients` empty | **PRESENT ×3** | `page.tsx:238`, `:255`, `:272` |

### 4.1 Detail: the enrichment block is unconditional once the URL is fixed

`BriefModal.tsx:28` awaits `briefApi.generate(clientId)`, which throws on 404 before line 31 runs, so today the fabricated strings are dormant — but the fallbacks at `:122/:135/:148/:156` produce an equally fabricated-looking brief (§5.2).

Crucially, the guards at `:32` and `:47` test keys that can **never** exist while the envelope is wrong:

```tsx
const briefData = response.data.brief;          // :29
if (!briefData.recent_interactions?.content) {   // :32 — real path is briefData.sections.recent_interactions
```

`briefData.recent_interactions` is `undefined` on every successful response (§2.1), so `?.content` is `undefined`, `!undefined` is `true`, and **both branches execute on every load** — not conditionally, unconditionally. The result is a brief that always contains:

- invented CRM history stamped `source: 'CRM & D5 Memory'`, `confidence: 0.92`, `timestamp: new Date()` (`:34-43`);
- invented market news stamped `source: 'TigerBroker News · LIVE'`, `confidence: 1.0` (`:47-60`, guard at `:47`);
- the literal 5-item agenda (`:63-67`);
- four panels of placeholder prose that happen to read almost exactly like the backend's own fallback strings (`:122,135,148,156`).

That is the worst possible combination: a wiring bug is presented as a successfully generated brief with a fresh timestamp and a green LIVE badge. The same reasoning applies without any URL change if the response ever arrives flat but partially populated.

### 4.2 Detail: the "Market News" card ignores every news item

`page.tsx:294-311` maps over `marketNews` but renders **constant** title/body for every row:

```tsx
{marketNews.slice(0, 4).map((news: any, idx: number) => (
  ...
  <div className="font-semibold text-sm mb-1 flex items-center gap-2">
    {idx === 0 && <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse"></span>}
    HSBC Holdings +2.3%
  </div>
  <div className="text-xs text-gray-500">
    Strong Q3 earnings, guidance upgraded
  </div>
```

The API payload (`news.title`, `news.source`, `news.timestamp`) is used only as a *count*. With the backend's 3 mock items (`market_service.py:82-107`) the panel shows the same headline three times. The "● LIVE · Reuters · {clock}" chip (`:303-308`) re-stamps itself every second from `currentTime`, so a static string appears to be a live updating feed.

### 4.3 Detail: static blocks that survive a total backend outage

`page.tsx` renders these without any API dependency, so a dead backend looks like a working product:

- Greeting "Good Morning, Sarah" (`:129`) — wrong at any hour after noon.
- Date "Tuesday, 16 March 2026" (`:131`) — hardcoded and already in the past relative to the audit date (7 Nov 2026, a Saturday).
- "Workflow ID: 8f21a4b2" (`:115`) — matches the backend's own hardcoded id (`dashboard.py:80`), i.e. a fake correlation id agreeing with a fake correlation id.
- Today's Schedule: three meetings with names, AUM and talking points (`:229-285`).
- Priority Actions: four items (`:322-350`).
- Book stats: 45 / 8 / $9.5M / 18 / +$38M (`:357-373`).
- KPI deltas: "↑ $12.3M this month (+2.9%)" (`:146`), "Next at 10:00 AM" (`:155`), "↑ Benchmark +1.2%" (`:177`).
- Family graph: 7 hardcoded nodes with SGD 120.5M (`FamilyGraphModal.tsx:22-95`, `:233`).

There are **6 occurrences of "Kenneth Wong", 3 of "Sarah Chen", 3 of "Ahmad Rahman", 5 of "Tan Family"** across `app/` + `components/`. The footer does disclose "SYNTHETIC DEMO DATA" (`page.tsx:384-388`), which mitigates but does not remove the fact that per-request data is presented as if it were a brief for the selected client.

---

## 5. D — State handling

### 5.1 Dashboard failure renders `$NaNM` next to fully-populated fake cards

`page.tsx:29-48`:

```tsx
const loadDashboard = async () => {
  try {
    setLoading(true);
    const [myDayRes, allocationRes, performanceRes] = await Promise.all([...]);
    setDashboardData({...});
  } catch (error) {
    console.error('Error loading dashboard:', error);
  } finally {
    setLoading(false);
  }
};
```

Observations, all static and certain:

1. **No error state exists.** There is no `error` variable, no banner, no retry. The only consumer of the failure is `console.error`.
2. **`Promise.all` is all-or-nothing.** A failing `/dashboard/my-day` discards the successful allocation and performance responses. Conversely, an outage of the *chart* endpoints discards good KPI data. No `Promise.allSettled`, no per-section error.
3. **`dashboardData` stays `null`**, so `:73-77` yields `kpis = {}`, `allocation = {}`, `performance = {}`.
4. **Arithmetic on `undefined` displays `NaN`.** `:142`:

   ```tsx
   ${(kpis.total_aum / 1e6).toFixed(1)}M
   ```

   `undefined / 1e6 → NaN`, `NaN.toFixed(1) → "NaN"`, so the hero card reads **"$NaNM"**. `:144` reads "Across **undefined** clients". `:154` renders an empty meetings count. `:163` an empty actions count. `:174` reads "+**undefined**%".
5. **The page cannot distinguish failure from emptiness.** A 500, an empty book, and a slow network all produce the same screen: `$NaNM` for the four KPI cards, an empty donut, an empty line chart, and **five fully populated hardcoded sections**. There is no `role="alert"`, no `aria-live`, no retry button.
6. **`AllocationChart` has no empty guard** (`AllocationChart.tsx:14-62` builds a pie from `data.equities/fixed_income/cash`, all `undefined`). `PerformanceChart` *does* guard (`PerformanceChart.tsx:18-24`) — inconsistent handling of the same class of failure within one screen.

The `/dashboard/my-day` history of HTTP 500 matters here: backend `dashboard.py:86-88` converts *any* exception into a 500, so the most likely real-world state (500) lands exactly on this path.

### 5.2 BriefModal leaks the previous client's data and fail-opens

`BriefModal.tsx:14-23, 25-73`:

- `brief` and `editedAgenda` are component state that is **never reset** when the modal opens or `clientId` changes. Failure path (`:68-72`) does `console.error` only.
- Therefore: open brief for Client A (succeeds or partially populates) → close → open for Client B → request 404s → `setBrief` is never called → **Client B's modal displays Client A's agenda and sections under Client B's name** (`:100` renders `clientName`, `:180` renders the stale `editedAgenda`).
- All five sections render placeholder prose on failure (`:122`, `:135`, `:148`, `:156`) and the agenda renders empty (`:180`), so the failure looks like a brief with missing fields rather than an error. Aggravating factor: three of these four strings are byte-identical to the backend's own fallback brief ("No significant changes detected.", "Interaction history available in client record.", "Market news feed temporarily unavailable." — `copilot_service.py:164-172`), and the fourth is a prefix of it. The frontend's "missing data" state is therefore indistinguishable from a legitimate backend fallback, which is exactly why this class of bug survives demos.
- `handleApprove` is **not disabled on failure** — `disabled={loading}` only (`:202`). After a failed generation the user can press "Approve & Continue to Meeting"; it posts the fake id, 404s, and `:81-83` swallows the error. The modal stays open with no message. `alert()` at `:80` fires only on success, which cannot currently happen.
- The modal is rendered unconditionally (`page.tsx:394-399`) with `clientId={selectedClient?.id || ''}`; before any selection `clientId` is `''`, but `isOpen` is false so no request is made. Fine — but the empty-string default means a stray `isOpen` would POST `/briefs/generate` with an empty id.

### 5.3 Duplicate requests and races

- `next.config.js:4` sets `reactStrictMode: true`. In dev, `useEffect` runs twice, so `BriefModal.tsx:19-23` and `brief/[clientId]/page.tsx:14-16` fire **two** `generate` POSTs per open. Each is a 404 today; once fixed, each is an expensive LLM-backed brief generated twice.
- No `AbortController`, no request-generation counter. Clicking "Open Brief" for client A then switching to B before A resolves lets the slower A response overwrite B's state (`BriefModal.tsx:25-28` → `setBrief` at `:62`). There is no guard that the response still belongs to the current `clientId`.
- `loadBrief` is referenced in `useEffect` but omitted from the dependency array (`BriefModal.tsx:23`), so the effect captures a stale closure; ESLint `react-hooks/exhaustive-deps` would flag it (lint is currently unrunnable, §1.2).
- `FamilyGraphModal.tsx:16-188` returns a cleanup function **only** when `isOpen` is true. When closed, the effect returns `undefined`, which is legal, but the guard means the chart is initialised in the same tick as first paint of the node — it relies on the ref being populated by the conditionally-rendered `<div>` at `:216`. No `ResizeObserver`, only a `window` resize listener (`:178-185`), so the graph does not reflow when the modal container changes size.

### 5.4 No error boundaries

`app/` contains only `layout.tsx`, `page.tsx`, `brief/[clientId]/page.tsx`, `globals.css` — **no `error.tsx`, no `global-error.tsx`, no `not-found.tsx`, no `loading.tsx`**. Any render-time exception (e.g. an ECharts option mutation, or a future typo) produces Next's default 500 overlay/page rather than a recoverable state.

### 5.5 Loading states

Loading is a single boolean per screen. `page.tsx:65-71` blocks the whole dashboard on the slowest of three requests ("Loading dashboard..."). `BriefModal.tsx:112-115` shows "Generating brief..." for a request that returns 404 in ~ms, so the UI flashes loading and then silently shows placeholders. There are no skeletons, no per-section spinners, and no timeout — with the backend down, `axios` waits on the OS connect timeout before failing, so the dashboard can sit on "Loading dashboard..." indefinitely.

---

## 6. E — Uncovered dimensions

### 6.1 Accessibility — effectively absent

A repo-wide search over `app/` and `components/` found **zero** occurrences of `role=`, `aria-*`, `tabIndex`, `htmlFor`, `<label>`, `onKeyDown`, or `Escape`. The only a11y-adjacent attribute in the entire frontend is `<html lang="en">` (`layout.tsx:18`).

Concretely:

- Both modals (`BriefModal.tsx:89-212`, `FamilyGraphModal.tsx:193-258`) are plain `<div>`s with no `role="dialog"`, no `aria-modal="true"`, no `aria-labelledby`.
- No focus trap, no initial focus, no focus restoration. `Tab` walks into the dashboard behind the overlay. `Escape` does nothing — the only close affordances are the backdrop `<div onClick>` (`BriefModal.tsx:91`, `FamilyGraphModal.tsx:195`) and a bare `×` button (`BriefModal.tsx:102-107`, `FamilyGraphModal.tsx:206-211`) with **no `aria-label`** (screen reader announces "×").
- The backdrop is a `<div>` with `onClick` and no keyboard equivalent, so keyboard users cannot dismiss by clicking outside.
- Every icon-only or symbol-only control ("×", "← Back to Dashboard" is text so OK) lacks an accessible name.
- No `aria-live` region anywhere, so async success/failure ("Brief approved!") is announced only by `window.alert` (`BriefModal.tsx:80`).
- Status is conveyed by colour alone: green/orange/red backgrounds (`page.tsx:323-349`) and the `● LIVE` green chip, with no text or icon fallback for colour-blind users.
- Contrast risk: `text-gray-500` on `bg-gray-50`/white for large amounts of secondary copy (`page.tsx:130, 155, 164, 300`), and `text-gray-400` on `bg-black` for the inactive workflow steps (`:102-113`). Not measured here; flagged as unverified rather than failed.
- The `animate-pulse` dot (`page.tsx:297`) has no `prefers-reduced-motion` guard.

### 6.2 i18n — none

No `next-intl`, `react-i18next`, `useTranslation`, or message catalogue. Every string is an English literal inline in JSX (~200+). Locale is hardcoded by call site rather than configuration:

- `toLocaleTimeString('en-SG', … 'Asia/Singapore')` (`page.tsx:51-57`) — locale and timezone are literals, not user settings.
- The date is not formatted at all; it is a constant `"Tuesday, 16 March 2026"` (`page.tsx:131`).
- `.toFixed(1)` currency rendering hardcodes `$` and millions (`page.tsx:142`, `:365`), ignoring the `currency` field the backend returns (`clients.py:39`, `dashboard.py:102`).
- Business names, greetings, and salutations ("Good Morning, Sarah") are literals.

### 6.3 Responsive / mobile — none

Zero responsive utility prefixes across all `.tsx` files: a search for `\b(sm|md|lg|xl|2xl):` returned **no matches**.

Layout is desktop-only and will overflow on narrow viewports:

- `grid-cols-4` KPI row (`page.tsx:136`), `grid-cols-2` charts (`:183`), `grid-cols-[2fr_1fr]` schedule/news (`:223`), `grid-cols-5` book stats (`:354`), `grid-cols-4` modal legend (`FamilyGraphModal.tsx:221`) — all fixed column counts with no breakpoint.
- Fixed 64 px header containing the app name, a live chip, a 4-step workflow stepper and the user block (`page.tsx:82-124`); on a phone this clips.
- Fixed 48 px footer with two blocks (`:379-391`).
- `max-w-[1920px] px-8` (`:83, 127`) — 32 px gutters on mobile, no `px-4` fallback.
- Modals: `max-w-5xl`/`max-w-7xl` with `max-h-[90vh]` and `min-h-[600px]` for the chart (`FamilyGraphModal.tsx:216`), which exceeds many viewports and relies on `overflow-hidden` (`:215`) — the chart is clipped with no scroll.
- ECharts instances are fixed at `height: '250px'` (`AllocationChart.tsx:67`, `PerformanceChart.tsx:104`).

### 6.4 XSS — no `dangerouslySetInnerHTML`, but two HTML-string sinks

There is **no** `dangerouslySetInnerHTML` or `innerHTML` assignment anywhere in `app/`, `components/`, or `lib/`. The brief body is rendered as text (`BriefModal.tsx:121-123` uses `whitespace-pre-wrap`), so LLM output cannot inject markup there. That part is correct.

Two latent sinks remain because ECharts renders tooltip strings as HTML:

- `PerformanceChart.tsx:32-38`:

  ```tsx
  formatter: (params: any) => {
    let result = `${params[0].axisValue}<br/>`;
    params.forEach((item: any) => {
      result += `${item.marker} ${item.seriesName}: +${item.value}%<br/>`;
    });
  ```

  `seriesName` comes from `data.datasets[].name`, i.e. from `GET /dashboard/performance-trend`. Backend values are currently literals (`dashboard.py:175-180`), so this is not exploitable today; it becomes a stored-XSS vector the moment dataset names derive from user or LLM content.

- `FamilyGraphModal.tsx:109-115`:

  ```tsx
  return `<strong>${params.data.name}</strong><br/>AUM: SGD ${params.data.value}M<br/>Click for details`;
  ```

  `params.data.name` is currently hardcoded (`:22-79`), so no live risk; same latent pattern.

No CSP is configured (`next.config.js` has only `env`), and no `X-Content-Type-Options`/`Referrer-Policy` headers. There is no auth token anywhere in `lib/api.ts` (`:5-10`), so the API is called anonymously and CORS is limited to `localhost:3000/8000` (`config.py:13-16`).

### 6.5 Build / bundle

- `tsc --noEmit` → **1 error**, `FamilyGraphModal.tsx:125` (§1.2). `next build` type-checks by default and has not been configured to skip, so the production build fails.
- `npm run lint` cannot run non-interactively (no ESLint config).
- **No test gate of any kind.** `package.json:5-10` defines `dev`/`build`/`start`/`lint` and **no `test`**; `node_modules/.bin` contains no jest/vitest/playwright/cypress. There is no CI config in the repo (no `.github/`, no `.gitlab-ci.yml`), so nothing automated can regress-guard this frontend. Cross-ref: `REAUDIT_01_Backend.md` §12.3 proposes `tsc --noEmit` as the minimal gate; it can only go green after the line above is fixed.
- Dead dependencies: `swr`, `lightweight-charts`, `date-fns`, `clsx` are declared in `package.json:14-19` and imported **nowhere** in `app/`, `components/`, or `lib/`.
- Bundle weight: `FamilyGraphModal.tsx:4` does `import * as echarts from 'echarts'` (full ECharts namespace) instead of tree-shaken imports, pulling the whole library into the client bundle for one modal. `AllocationChart`/`PerformanceChart` use `echarts-for-react`, which pulls ECharts again.
- Tailwind: `tailwind.config.js` defines a `capco-*` palette (`:10-24`) that no component uses (components use stock `gray-*`/`black`), and `plugins: []` means the `prose` class used at `brief/[clientId]/page.tsx:74,85,98,106,129` is a **no-op** (no `@tailwindcss/typography`).
- No `output: 'export'`/standalone config, no `images` config; `next/font/google` (`layout.tsx:2-5`) fetches Inter at build time, so offline builds fail.

### 6.6 Duplicate page implementation

Two independent implementations of the same Gate-1 screen, already diverged:

| Aspect | `components/BriefModal.tsx` | `app/brief/[clientId]/page.tsx` |
|---|---|---|
| Data call | `briefApi.generate` `:28` | `briefApi.generate` `:21` |
| Fabricated enrichment | **yes** `:31-67` | no |
| Section fallback copy | "…temporarily unavailable." `:122,135,148,156` | "Loading…/No material changes/No recent interactions/No relevant news" `:75,86,99,107` |
| Provenance shown | source only `:126` | source **and** timestamp `:78` |
| LIVE chip | `● LIVE · TigerBroker` `:139` | `● LIVE · TigerBroker` `:90` |
| Approve | `brief-123` + `alert()` `:77-80` | `brief-123` + `router.push('/')` `:33-34` |
| Reachable | via 3 dashboard buttons | **only by typing the URL** (§3.3) |

This is duplicated logic that must be maintained twice, with different failure behaviour for the same endpoint. The page variant is dead code in practice.

### 6.7 Dead code inventory

| Item | Evidence |
|---|---|
| `marketApi` import in dashboard | `page.tsx:4` (never used) |
| `clientApi` (4 methods) | `api.ts:46-58`, no callers |
| `workflowApi` (5 methods) | `api.ts:73-88`, no callers |
| `briefApi.getBrief` | `api.ts:68-69`, no callers, route deleted |
| `marketApi.getNews` | malformed and uncalled |
| `app/brief/[clientId]/page.tsx` | unreachable route |
| `useState`/`useRouter` imports in page | used, but `router` only to go home |
| `swr`, `lightweight-charts`, `date-fns`, `clsx` | `package.json:14-19`, zero imports |
| `capco-*` Tailwind palette | `tailwind.config.js:10-24`, zero usage |
| `prose` class | `brief/[clientId]/page.tsx:74` etc., plugin absent → no-op |

No component is entirely unused: `AllocationChart`, `PerformanceChart`, `BriefModal`, `FamilyGraphModal` are all mounted from `page.tsx:188, 218, 394, 402`.

---

## 7. Severity-ranked findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| F1 | **Blocker** | Backend does not import; every frontend call is connection-refused | `market_service.py:13`, `models.py`, `backend.log` |
| F2 | **Blocker** | Production build fails typecheck | `FamilyGraphModal.tsx:82-87, 125`; tsc exit 1 |
| F3 | **Critical** | All 3 brief methods resolve to 404 (2 of them live); G-26 is regressive, not a fix | `api.ts:62-69` vs `briefs.py:14,36` |
| F4 | **Critical** | Brief response shape mismatch (`sections.*`); the `:32/:47` guards then evaluate true on every load, so placeholders + fabrication are unconditional after any URL fix | `brief_service.py:68-74` vs `BriefModal.tsx:29-60,122` |
| F5 | **Critical** | Fabricated brief content with confidence 0.92/1.0 and fresh `new Date()` timestamps, executing on every successful generate | `BriefModal.tsx:32-60` |
| F6 | **Critical** | Dashboard failure renders `$NaNM` with 5 fully-populated fake sections; no error state | `page.tsx:29-48, 142` |
| F7 | **High** | Approve always targets fake `'brief-123'`; generate's `brief_id` discarded; approve button enabled after failure | `BriefModal.tsx:28,77,202` |
| F8 | **High** | Cross-client data leakage in modal (stale `brief`/`editedAgenda` not reset) | `BriefModal.tsx:14-17, 68-72` |
| F9 | **High** | 19/24 routes uncalled, 21/24 with no valid caller; whole CRM + Shariah + workflow have no UI | §3.2 |
| F10 | **High** | Market News card ignores API content and re-stamps "Reuters LIVE" from a 1 s browser clock | `page.tsx:294-311`, `:22-24` |
| F11 | **High** | `workflow/start` and `extract-insights` still 422 (body vs query) — latent, since `workflowApi` is never imported | `api.ts:74-75,86-87` vs `workflow.py:25-31,108-113` |
| F12 | **Medium** | Zero accessibility: no roles, ARIA, focus trap, Escape, labels | §6.1 |
| F13 | **Medium** | Zero responsive breakpoints; desktop-only grids and fixed header/footer | §6.3 |
| F14 | **Medium** | Hardcoded identity/date/workflow id; 6× "Kenneth Wong"; wrong greeting; past date | `page.tsx:115,120,129,131,156` |
| F15 | **Medium** | `demo` clientId fallback silently queries a non-existent client | `page.tsx:238,255,272` |
| F16 | **Medium** | `Promise.all` all-or-nothing; no partial rendering | `page.tsx:32-36` |
| F17 | **Medium** | StrictMode dev double-POST; no abort on client switch | `next.config.js:4`, `BriefModal.tsx:19-28` |
| F18 | **Low** | Double-`?` URL in `getNews` | `api.ts:36` |
| F19 | **Low** | KPI key mismatch `actions_overdue` | `page.tsx:166` vs `dashboard.py:59-66` |
| F20 | **Low** | Dead deps, dead API clients, unreachable brief page, no-op `prose`, unused palette | §6.6-6.7 |
| F21 | **Low** | Latent HTML string sinks in ECharts tooltips | `PerformanceChart.tsx:32-38`, `FamilyGraphModal.tsx:109-115` |
| F22 | **Low** | No error/not-found/loading boundaries; lint config absent | `app/` listing; `.eslintrc*` absent |

---

## 8. Remediation plan (frontend-only, minimal)

Ordered so that each step is independently verifiable. None of this compensates for F1, which is a backend fix.

1. **Make failure visible before anything else.** Add `error` state to `page.tsx:29-48`; render a banner with retry on failure; use `Promise.allSettled` so KPI/chart sections fail independently; guard `:142` (`kpis.total_aum == null ? '—' : …`) and the same pattern at `:144,154,163,174,195-209`. Acceptance: with the API down, no `NaN`/`undefined` string appears, and a retry control exists.
2. **Fix the three live URLs** (`api.ts:62-69`) to `POST /briefs/generate/${clientId}`, `POST /briefs/approve/${briefId}?approver=${encodeURIComponent(approvedBy)}` (+ optional `edited_agenda`), and delete `getBrief` (route gone). Acceptance: 200 against a running backend, and a 404 produces a visible error rather than placeholder text.
3. **Fix the response shape — and pick one shape for good.** Adopt the nested `sections` envelope (justification: `Brief.sections` is a required column, `models.py:82`) and read `response.data.brief.sections.*` at `BriefModal.tsx:122,135,148,156,180` and `brief/[clientId]/page.tsx:75,86,99,107,130`. Delete the dead flat generator `CopilotService.generate_brief` / `_generate_fallback_brief` (`copilot_service.py:27,157-175`) so a second contract cannot reappear. Acceptance: the real `content` from `brief_service._build_*` appears in all five sections; `grep -rn "_generate_fallback_brief" backend/app` returns only the definition and no caller claims.
4. **Delete the fabrication block** `BriefModal.tsx:31-67`. Replace with a distinct "section unavailable" state that does not carry a confidence or timestamp. Acceptance: `grep -n "Enrich with real data"` empty; no invented provenance.
5. **Capture and use the real `brief_id`** — store `response.data.brief.brief_id` in state and pass it to `approve`; remove `'brief-123'`. Disable Approve when `brief === null` or `error`. Acceptance: approved id equals the generated id; button disabled on failure.
6. **Reset modal state on open** — clear `brief`, `editedAgenda`, `editing`, `error` in the `isOpen`/`clientId` effect; guard against out-of-order responses with a request id or `AbortController`. Acceptance: opening client B after a failed A shows B's error, never A's agenda.
7. **Remove the fake LIVE affordances** — replace `page.tsx:92-94` with the actual data source and, if nothing is live, say so; drive the news chip from `news.source`/`news.timestamp`; render `news.title`/`news.content` instead of the constant block at `:298-301`; delete the hardcoded date/greeting (`:129-131`) or derive them from `Date`; delete `8f21a4b2` (`:115`) or use the backend's value.
8. **Wire the data that already exists** — `getBookStats` for `:354-375`, `priority_actions` from `my-day` for `:322-350`, `getKPIs` for `actions_overdue`. This removes the largest static blocks without new backend work.
9. **Remove the `'demo'` fallback** (`:238,255,272`) and disable the button when no ranked client exists; otherwise show "select a client".
10. **Fix the build** — the link `value` strings (`FamilyGraphModal.tsx:82-87`) are *labels* ('full'/'education-only'/'restricted') consumed by `edgeLabel.formatter` (`:157-161`) and the edge tooltip (`:113`). Do not `as any`: add a separate `entitlement` field to each link, keep `value` numeric, and repoint the two consumers at `params.data.entitlement`. Then add an ESLint config, a `test` script, and delete unused deps. Acceptance: `tsc --noEmit` exit 0; `next build` succeeds; the entitlement labels still render.
11. **Accessibility minimum** — `role="dialog"`, `aria-modal`, `aria-labelledby`, Escape handler, focus trap + restore, `aria-label="Close"` on the `×` buttons. Acceptance: keyboard-only open/close of both modals.
12. **Responsive minimum** — add `sm:`/`lg:` breakpoints to the five grids and the header, and `px-4 sm:px-8`.

---

## 9. How to reproduce this audit

```bash
# 1. Backend cannot start
grep -n "MarketTick" backend/app/services/market/market_service.py backend/app/models/models.py   # import site only
tail -1 backend.log                                                                                # ImportError
ps -p "$(cat backend.pid)"                                                                         # empty

# 2. Frontend cannot build
cd frontend && ./node_modules/.bin/tsc --noEmit; echo $?                                           # 1

# 3. Contract mismatch
sed -n '61,70p' frontend/lib/api.ts
sed -n '14,41p' backend/app/api/v1/endpoints/briefs.py
sed -n '25,31p;108,113p' backend/app/api/v1/endpoints/workflow.py

# 4. Call-site coverage (16/21 orphaned)
grep -rn "dashboardApi\.\|marketApi\.\|clientApi\.\|briefApi\.\|workflowApi\." frontend/app frontend/components

# 5. Route coverage (21/24 uncalled)
grep -rn "@router\." backend/app/api/v1/endpoints/

# 6. Fabrication markers
grep -rn "Enrich with real data\|brief-123\|8f21a4b2\|TigerBroker News · LIVE\|confidence: 0.92\|confidence: 1.0" frontend

# 7. Accessibility / responsive
grep -rn "aria-\|role=\|tabIndex\|onKeyDown" frontend/app frontend/components    # no matches
grep -rnE "\b(sm|md|lg|xl|2xl):" frontend --include=*.tsx                         # no matches
```

**Acceptance criteria for closing G-26:** (a) backend boots; (b) `tsc --noEmit` exits 0; (c) all 5 live call sites return 2xx against a seeded backend; (d) a deliberately-down backend produces visible, non-fabricated error UI with no `NaN`, no invented confidence, and no fresh timestamps; (e) static analysis shows zero fabricated-brief markers `brief-123`, `Enrich with real data`, `TigerBroker News · LIVE` in `frontend/`.

---

## Appendix A — Route inventory (24 routes)

```
GET  /api/v1/clients/                          clients.py:27
GET  /api/v1/clients/{client_id}               clients.py:44
GET  /api/v1/clients/{client_id}/portfolio     clients.py:64
GET  /api/v1/clients/{client_id}/shariah-report clients.py:85
GET  /api/v1/market/quotes                     market.py:12
GET  /api/v1/market/news                       market.py:25
GET  /api/v1/market/signals                    market.py:39
GET  /api/v1/market/historical/{symbol}        market.py:57
POST /api/v1/market/mode                       market.py:71
POST /api/v1/briefs/generate/{client_id}       briefs.py:14
POST /api/v1/briefs/approve/{brief_id}         briefs.py:36
POST /api/v1/workflow/start                    workflow.py:25
POST /api/v1/workflow/consent                  workflow.py:42
POST /api/v1/workflow/review/approve           workflow.py:62
GET  /api/v1/workflow/{workflow_id}            workflow.py:91
POST /api/v1/workflow/extract-insights         workflow.py:108
GET  /api/v1/dashboard/my-day                  dashboard.py:18
GET  /api/v1/dashboard/kpis                    dashboard.py:90
GET  /api/v1/dashboard/book-stats              dashboard.py:114
GET  /api/v1/dashboard/allocation              dashboard.py:134
GET  /api/v1/dashboard/performance-trend       dashboard.py:156
POST /api/v1/crm/sync                          crm.py:16
POST /api/v1/crm/sync/{client_id}              crm.py:90
GET  /api/v1/crm/status                        crm.py:143
```

## Appendix B — Frontend file inventory (7 source files, ~1,315 LOC)

| File | LOC | Role | Reachable |
|---|---|---|---|
| `app/page.tsx` | 409 | Dashboard | yes |
| `app/brief/[clientId]/page.tsx` | 155 | Standalone brief | **no** (URL only) |
| `components/FamilyGraphModal.tsx` | 259 | Family graph | yes (dashboard) |
| `components/BriefModal.tsx` | 213 | Brief modal | yes (dashboard) |
| `components/PerformanceChart.tsx` | 108 | Line chart | yes |
| `components/AllocationChart.tsx` | 71 | Donut chart | yes |
| `lib/api.ts` | 89 | API client (21 methods) | — |

## Appendix C — Backend data proven to be mock (relevant to frontend truthfulness)

- `/dashboard/kpis`: literals `428.5e6`, `45`, `5.8` — `dashboard.py:100-109`
- `/dashboard/book-stats`: literals `45`, `8`, `9.5e6`, `18`, `38e6` — `dashboard.py:123-129`
- `/dashboard/allocation`: literals `62.0/28.0/10.0` — `dashboard.py:142-150`
- `/dashboard/performance-trend`: hand-written month arrays — `dashboard.py:165-183`
- `/market/news`: three hardcoded items — `market_service.py:82-107`
- "Proposed Agenda" is labelled `source: "AI Generated"`, `confidence: 0.85`, `source_kind: "ai_generated"` but is produced by an `if`/`extend` template with **no LLM call** — `brief_service.py:203-237`; this contradicts the endpoint docstring "Proposed Agenda: AI-generated" (`briefs.py:25`) and `PROGRESS.md` G-01
- brief approve: no persistence, hardcoded `approved_at: "2024-11-07T12:00:00Z"` — `briefs.py:48-55`
- workflow consent / review approve / get: hardcoded response dicts, `TODO` comments — `workflow.py:49, 69-86, 98-103`
- brief generation can 500 before producing any payload: `brief_service.py:96` formats nullable `client.aum` and `:104` formats nullable `holding.current_value` with `:,.0f`, so a single NULL row raises `TypeError`, caught by `briefs.py:32-34` and returned as 500. The UI's only reaction is the placeholder brief (§5.2).

The frontend therefore cannot be "made truthful" by contract repair alone: several endpoints return manufactured data with real-looking provenance (`confidence: 1.0`, `source_kind: LIVE_FEED` in `brief_service.py:108-116, 141-147, 170-177, 194-200`).

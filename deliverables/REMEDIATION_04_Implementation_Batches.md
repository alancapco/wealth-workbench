# Implementation Batches · RM Workbench Remediation

**Status:** Dispatch plan derived from frozen `REMEDIATION_03_Architecture_Contracts.md` revision 2 and `REMEDIATION_03A_Additive_Schema.sql`; requirements `REMEDIATION_01_Requirements.md`; product design `REMEDIATION_02_Product_Design.md`; plus current repository layout. This is an implementation dispatch plan, not permission to apply migrations to any existing database, call external providers, enable pilots, deploy, or create live business effects. Current repository evidence is not re-audited by this plan; acceptance is based on tests/evidence, not prior source-exists claims.

**Frozen global rules for every unit:** use contracts by API-ID only; base `/api/v1`; success envelope `data` plus `meta`; common errors/statuses, Pydantic `extra=forbid`, mutation `Idempotency-Key`, required `If-Match`, session+CSRF, current server-side tenant/book/client/permission recheck, exact revision references and truthful capability/provenance states. Fixtures are synthetic and isolated. Never claim external `LIVE` or action success without authoritative receipt/readback. Preserve legacy IDs/data; no automatic tenant ownership mapping/backfill; no destructive migration, stamping, reset, or historical Alembic graph rewrite. Unknown institution/provider policies remain `UNCONFIGURED`. No auto-send/trade/execution, autonomous advice, fatwa, or approval bypass. Pilot feature controls remain absent/default OFF; only named synthetic fixtures may exercise ON paths.

## 1. Batch overview

| Batch | Purpose | Units | Parallel? | Prerequisite |
|---|---|---:|---|---|
| 0A | Restore importable runnable baseline and remove false-success boot paths | 1 | Parallel with 0B, 0C, 0D only in disjoint file ownership | None |
| 0B | Repair Alembic discovery and establish safe migration graph/testing harness | 1 | Parallel with 0A, 0C, 0D | None; real applied-history remains an explicit hold |
| 0C | Freeze shared backend DTO/error/auth/scope contract primitives | 1 | Parallel with 0A, 0B, 0D; serial owner of shared core/schema paths | None |
| 0D | Frontend contract/typecheck baseline, shared API envelope and shared state primitives | 1 | Parallel with 0A–0C; serial owner of `frontend/lib/api.ts` and shared UI components | None |
| 0E | Additive persistence models/repositories, audit/idempotency/lineage and SQL-to-Alembic parity | 1 | Starts after 0B+0C; exclusive owner of models/migration integration | 0B, 0C |
| 1A | Client/session/calendar context and durable workflow/orchestrator | 1 | Parallel with 1B only after Batch 0 | 0A–0E |
| 1B | Canonical brief lifecycle, sources, review and single brief UI | 1 | Parallel with 1A; shared UI/API primitives already owned | 0A–0E |
| 2A | Meeting consent/capture/manual notes/transcript/extraction recovery | 1 | Parallel with 2B after Batch 1 common services | 1A, 1B |
| 2B | Artifact review, action preview/authorization/outbox and follow-up/ticket | 1 | Parallel with 2A; exclusive action-core owner | 1A, 1B |
| 3A | Book priorities, reason evidence, controls and contact outcomes | 1 | Parallel with 3B after Batch 1; no ranking-service overlap with outreach | 1A, 1B |
| 3B | Grounded outreach draft and explicit approved send | 1 | Parallel with 3A; consumes shared action core | 2B |
| 4A | Tier B product discovery, comparison and suitability | 1 | Parallel with 4B after core action/context foundations; P1 does not delay P0 | 1A, 2B |
| 4B | Runtime config, flags, readiness, audit, telemetry and measurement surfaces | 1 | Parallel with 4A; shared measurement code owned here, features emit via contract | 0E, 1A |
| 5A | FR-21 scoped mobile parity and device gating | 1 | Parallel with 5B after desktop core UIs land | 1B, 2B, 3A, 3B, 4B |
| 5B | Default-OFF Shariah pilot (three FRs) | 1 | Parallel with 5A and 5C; isolated pilot paths | 4A, 4B |
| 5C | Default-OFF family/household pilot (three FRs) | 1 | Parallel with 5A and 5B; isolated pilot paths | 4B, 2B |
| 6 | Independent integration QA, code review, release evidence and gate decision | 1 | Independent reviewers; no feature author self-acceptance | All implementation batches |

Each row denotes an independently mergeable vertical delivery unit, not a promise that all external acceptance gates are locally satisfiable. **Implementation complete with isolated tests** is distinct from **LIVE/provider/institution acceptance** and **production certification**; the latter remain externally blocked until named approvals/credentials/data ownership/operations evidence exist.

## 2. Dependency diagram

```text
Batch 0 (parallel disjoint foundations)
  0A Boot ───────┐
  0B Alembic ────┼──> 0E Persistence + auth-safe transaction/audit/lineage
  0C DTO/auth ───┤                    │
  0D FE baseline ┘                    ├──> 1A Context/workflows ──┐
                                      └──> 1B Brief lifecycle ───┤
                                                                  ├──> 2A Meeting
                                                                  ├──> 2B Actions ──> 3B Outreach
                                                                  ├──> 3A Priorities ─┘
                                                                  └──> 4B Admin/metrics
                                                    2B + 1A ──────> 4A Products
                                               1B+2B+3A+3B+4B ───> 5A Mobile
                                               4A+4B ─────────────> 5B Shariah pilot
                                               4B+2B ─────────────> 5C Family pilot
All units ───────────────────────────────────────────────────────> 6 Independent QA/release gates
```

**Collision rule:** only the named owner of 0C edits shared DTO/error/identity modules; only 0D edits shared frontend API client and primitives; only 0E edits model registry, migration graph and common repositories; only 2B owns action preview/outbox. Domain cards may add their own schema/service/router/test modules and must use these interfaces, not fork them. Contract edits require architecture-owner approval and synchronized contract/SQL change notice.

## 3. Task cards

### 【U-001】Restore deterministic backend boot and honest readiness
- **Batch / owner role:** 0A / Backend runtime owner (one developer owns `main.py`, config/database bootstrap and health wiring).
- **Purpose / scope:** Make `app.main` and every registered router import without external credentials/network, remove stale imports/placeholder success, make health/readiness reflect actual process/database/schema/identity configuration. This is a runnable baseline, not feature completion.
- **Inputs / outputs:** Inputs: pinned `uv.lock`, current backend modules. Output: importable FastAPI app; stable startup/shutdown and no provider construction at import; `/health/live` process-only response and `/health/ready` checks truthful readiness, see API-017.
- **Contracts:** API-017; global envelope/error rules where applicable. No new business endpoints or alternate DTO definitions.
- **Files owned:** `backend/app/main.py`; `backend/app/core/config.py`; `backend/app/core/database.py`; `backend/app/api/health.py`; router inclusion in `backend/app/api/v1/__init__.py` and `backend/app/api/v1/endpoints/{market,workflow,clients,briefs,crm,dashboard}.py` only where required to eliminate import failures/false success. Add `backend/tests/test_boot_readiness.py`. Do not edit models/migrations, frontend, or domain service behavior outside stubbing removal.
- **Dependencies:** None. Coordinate 0C before importing shared DTO implementations; use a temporary import boundary only in owned files, then rebase without defining competing contracts.
- **Acceptance evidence / commands:** From `backend`: `uv run python -c 'from app.main import app; print(sorted((r.path, tuple(sorted(r.methods or []))) for r in app.routes))'`; `uv run pytest tests/test_boot_readiness.py`; assert no provider request on import; live returns process UP; ready is 503 if DB unavailable, wrong schema head or required identity config missing; optional provider state is UNCONFIGURED/UNAVAILABLE, not readiness lie. Capture exact registered path-method inventory as test artifact.
- **Negative/security/feature-ON:** Missing credentials and denied outbound network do not prevent import; fixture mode rejected when `APP_ENV=production`; SQL echo is disabled; no hardcoded database connected; no placeholder endpoint returns synthetic success; startup never invokes `create_all`, seeds, migration, or provider operation.
- **No-go:** No read/write to configured existing DB; do not inspect `.env` values or print secrets; no migrations, credential validation, live provider call, app deployment.
- **Done:** reproducible import/readiness evidence, tests pass, no false success, reviewer confirms only owned paths changed. Does not satisfy end-to-end product acceptance.

### 【U-002】Repair Alembic discovery and safe graph test harness
- **Batch / owner role:** 0B / Database migration owner (sole migration-graph/config owner).
- **Purpose / scope:** Repair migration configuration/discovery and install executable isolated PostgreSQL test harness. Determine the graph only after read-only applied-history inventory. No existing DB migration is authorized by this card.
- **Inputs / outputs:** Inputs: current Alembic configuration/revisions and frozen additive SQL companion. Output: reproducible async Alembic env/template, safe revision-graph decision record, disposable synthetic DB test harness, migration-readiness test hooks.
- **Contracts:** SQL companion `REMEDIATION_03A_Additive_Schema.sql`; architecture §7 steps 1–6; API-017 schema readiness. No API DTO edits.
- **Files owned:** `backend/alembic.ini`; `backend/alembic/env.py`; `backend/alembic/script.py.mako`; `backend/alembic/versions/**`; migration-only `backend/tests/migrations/**`; `backend/pyproject.toml` only if test extras/config need it. No ORM model/domain edits.
- **Dependencies:** None for static config and test harness; U-005 waits for this. To choose revision ancestry, collect only safe read-only inventory from explicitly disposable/synthetic fixtures and user-approved schema-only inventory. If applied history across environments is unknown, record **HOLD: graph ancestry unresolved** and do not reparent published IDs or invent `000` ancestor.
- **Acceptance evidence / commands:** `cd backend && uv run alembic history --verbose`; `uv run alembic heads`; execute `uv run pytest tests/migrations -q` against throwaway PostgreSQL 15 containers/DBs: empty DB full upgrade/head and second no-op; synthetic legacy JSON/naive timestamp; synthetic JSONB/timestamptz no alembic table; applied 001/002 fixture only if safely established; incompatible PK/type/schema collision aborts with no changed schema/data. Save head list, schema assertions and before/after synthetic IDs/checksums. `alembic check` only after metadata imports are complete (U-005 integration).
- **Negative/security/feature-ON:** Never `stamp head` by schema presence; no `DROP`, `TRUNCATE`, type cast, `IF NOT EXISTS` drift masking, tenant backfill, app-start migrations/seeds, or edits/reparenting of applied history. Test fails closed on mismatched PK or partial legacy baseline. Use synthetic records only.
- **No-go:** Do not run against `.env` configured database, docker-compose app DB or any named/existing institution DB. No real DB history probing without approval; SQL script itself is not Alembic proof.
- **Done:** Safe graph decision documented with evidence or explicit hold; async run_sync setup/templates discovered; disposable migration matrix passes; no destructive action observed.

### 【U-003】Establish shared DTO, error, identity and scope primitives
- **Batch / owner role:** 0C / Backend platform-security owner (unique owner of common contracts and authorization primitives).
- **Purpose / scope:** Implement the single typed common boundary consumed by every route: envelopes/errors, common scalar/ref types, verified principal, tenant/book/client authorization and context revision recheck. Do not create login UI or domain flows here.
- **Inputs / outputs:** Input: frozen architecture §§3, 5, 6. Output: shared Pydantic 2 `extra=forbid` DTO and dependencies; typed test principal strictly restricted to isolated `APP_ENV=local|test` fixture DB/network-deny mode; server authorization utility usable by routers/workers.
- **Contracts:** API-001, AUTH-01…03, API-017 common contract/error rules; named DTO types in architecture §§3/5. Later unit cards cite domain APIs without redefining field-level schema.
- **Files owned:** New `backend/app/schemas/{common.py,identity.py}`; new `backend/app/core/{errors.py,identity.py,authorization.py}`; `backend/app/api/dependencies.py` (new or current dependency module); `backend/tests/test_contract_common.py`; `backend/tests/test_authorization_scope.py`. No domain schema files, models or router files.
- **Dependencies:** None. 0A can consume shared types after integration. 0E depends on principal/scope and transaction boundary.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/test_contract_common.py tests/test_authorization_scope.py -q`; `uv run python -c 'from app.main import app; app.openapi()'` after U-001 integration. Assert OpenAPI schemas reject additional keys, common validation maps to 400 VALIDATION_ERROR, unknown ref path/context mismatch to 400, unauthorized/nonexistent resource indistinguishable 404, capability denial 403; all protected routes obtain authenticated principal+CSRF, each query/use case checks current entitlement revision, cursor/context bound to principal/scope.
- **Negative/security/feature-ON:** unauthenticated, wrong tenant/book, missing capability, revoked entitlement, stale context, fixture principal in production, user-supplied tenant/approver headers, unsafe `return_to`, bad OIDC state/nonce/issuer/audience all deny. With absent OIDC config return UNCONFIGURED; no self-registration or password path. No UI-only authorization.
- **No-go:** No production IdP call/credentials, no role/ownership guessing, no tenant auto-assignment, no broad auth bypass to make tests pass.
- **Done:** Common schemas/errors and test principal exported for downstream cards; negative tests prove fail-closed boundaries; sole owner review of dependent module usage.

### 【U-004】Repair frontend API boundary and typecheck baseline
- **Batch / owner role:** 0D / Frontend platform/accessibility owner (sole owner of `lib/api.ts`, common components, shell/session access).
- **Purpose / scope:** Make frontend reproducibly typecheck/build on existing Next/React lock; replace envelope mismatch with one typed API client contract; deliver reusable error/loading/unavailable state and safe session-scope reset primitives. No domain redesign.
- **Inputs / outputs:** Input: existing `package-lock.json`, frozen common HTTP rules and Design P-020/P-001/P-002. Output: `npm ci`, clean `tsc --noEmit`, production build; shared typed API call/error parser and AsyncRegion/PolicyCheckPanel/ClientContextHeader foundations.
- **Contracts:** Common envelope/error schema, AUTH-01…03, API-001/017; use frozen API IDs only when binding feature methods. All success payload is `response.data.brief.sections` for brief path as normalized by API contract; do not invent alternate nesting.
- **Files owned:** `frontend/lib/api.ts`; new `frontend/lib/contracts/common.ts`; shared `frontend/components/{AsyncRegion.tsx,PolicyCheckPanel.tsx,ClientContextHeader.tsx,AccessibleDialog.tsx}`; shell/session wiring `frontend/app/layout.tsx`, `frontend/app/page.tsx` only for shell navigation/auth; `frontend/tests/contracts/**` (or repository's established test location). Other domain page paths reserved to later cards.
- **Dependencies:** None. Disjoint with 0A–0C. Coordinate typed DTO export with 0C, use architecture contract generator/fixture rather than handwritten diverging API definitions.
- **Acceptance evidence / commands:** `cd frontend && npm ci && npx tsc --noEmit && npm run build`; contract fixture tests assert exact envelope, null fields, union exhaustiveness and normalized error status. Exercise abort/reset on tenant/book/client change and late old-context response rejection. A route open/GET never invokes POST generation/action.
- **Negative/security/feature-ON:** No sensitive localStorage/sessionStorage/service-worker cache; no hardcoded client/approver/brief ID/AUM; no `any`, TS suppression or optimistic success; environment/capability status includes visible text not color only; inaccessible/unauthenticated state does not render stale protected payload.
- **No-go:** Do not edit feature pages owned by later units except routing/shell compile repairs; no new package outside frozen lock without architecture approval; no production deploy.
- **Done:** typecheck and build pass, common API tests pass, current scope-switch/late response tests pass, files are within ownership boundary.

### 【U-005】Build additive persistence and transactional platform primitives
- **Batch / owner role:** 0E / Backend persistence/platform owner (one owner of model registry, repositories, shared transaction/audit/idempotency/lineage).
- **Purpose / scope:** Deliver SQLAlchemy async metadata/models and narrowly factored repository services matching the additive SQL contract: tenant scope, config/evidence, workflow/stage/catalog, artifact lineage/revision/item/source, review, idempotency, outbox/action tables, audit/telemetry and priority/product/pilot persistence. Include no business workflow behavior beyond tested generic primitives.
- **Inputs / outputs:** Frozen SQL companion is schema authority; preserve existing UUID PKs, `Brief.version` string/`sections` JSON. Output: metadata imports, transaction-local audit/idempotency helper, canonical hash/ref/revision repository, readiness schema check; migration parity with U-002 graph decision.
- **Contracts:** Architecture §§4, 7; API common mutation/If-Match/idempotency; API-045/010/048–051 base persistence semantics; SQL table names/constraints. Domain API contracts remain downstream.
- **Files owned:** `backend/app/models/**` including `models/__init__.py`; new `backend/app/models/{platform,workflow,artifact,action,priority,product,pilot,admin}.py` as needed; new `backend/app/repositories/{base,artifacts,transactions,audit,idempotency}.py`; `backend/app/services/{audit,provenance}/**` shared generic rewrites; `backend/alembic/env.py` metadata import integration and selected new migration files only under U-002 sole graph owner review; `backend/tests/persistence/**`.
- **Dependencies:** U-002 and U-003. U-001 DB session lifecycle boundary. U-002 migration owner remains sole editor of graph ancestry; model author submits migration revision branch/patch to that owner.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/persistence tests/migrations -q`; `uv run alembic check`; disposable PostgreSQL 15 integration tests assert SQL/model parity including same-tenant different-client composite FK denial, current revision same-lineage pointer/uniqueness, config scope isolation, atomic canonical write+audit+idempotency, append-only audit mutation denied, unique authorization/outbox key and attempt uniqueness, optimistic ETag conflicts. Restart app + worker fixture and read back revisions/actions; preserve existing synthetic IDs/count/checksums. No SQLite substitute.
- **Negative/security/feature-ON:** transaction failure rolls back business row/audit/idempotency; cross-tenant and same-tenant cross-client references rejected; legacy approval text cannot authorize actions; new-tenant mapping absent means inaccessible. No schema `create_all` in app runtime.
- **No-go:** Never migrate existing configured DB; never make/remediate ownership backfill; no destructive historical import/data conversion; no public `stamp` helper. Only disposable DB and synthetic fixtures.
- **Done:** all ORM/SQL/migration parity checks, restart/readback and constraint negatives pass; migration integration approved by U-002 owner; API core meets contract.

### 【U-006】Deliver client context, calendar resolution and durable workflow orchestration
- **Batch / owner role:** 1A / Backend copilot/context owner (exclusive ownership of workflow orchestrator, registry, client/calendar workflow routes).
- **Purpose / scope:** Implement entitled client lookup/detail/context and portfolio/calendar source states; explicit ambiguous calendar event resolution; workflow create/list/get, durable versioned skill catalog and stage runs with pause/resume/abandon. No brief generator or action dispatcher duplication.
- **Inputs / outputs:** Incoming principal/book/date/timezone and approved source adapter outputs; outgoing typed `ClientSummary`, `ClientDetail`, `Portfolio`, `CalendarEvent`, `Meeting`, `Workflow`, `StageRun`; persisted context revision and source refs.
- **Contracts:** API-001…003, 020…025, 007…009, 026…030; AUTH-01…03 as session input; source/provenance/common errors; policy/flag rules. Reuse one orchestrator per §6.2.
- **Files owned:** `backend/app/api/v1/endpoints/{clients.py,workflow.py,calendar.py}` (`calendar.py` new); `backend/app/schemas/{client.py,workflow.py,calendar.py}`; `backend/app/services/{context,calendar}/**` (new); `backend/app/services/workflow/{workflow_orchestrator.py,__init__.py,registry.py,stage_runner.py}`; `backend/app/adapters/{identity,calendar,portfolio}/**` (typed FIXTURE + unavailable implementations only); `backend/tests/context/**`, `backend/tests/workflow/**`.
- **Dependencies:** Batch 0 all. Workflow persist uses U-005; common authorization U-003; no dependency on domain cards.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/context tests/workflow -q`; API integration in isolated test DB: eligible/revoked/wrong-book client; ambiguous event requires API-023 explicit client selection and changing event version conflicts; canceled event rejects. Create/start workflow, enqueue registered stage, run/pause/resume/restart and read actual persisted status/version/output refs. GET never starts run; resume reauthorizes without auto-running. Empty results differ from dependency outage.
- **Negative/security/feature-ON:** Filter clients/calendar candidate hints before serialization; context assembled only after tenant/book/node authorization; stale/revoked identity invalidates; fixture adapter rejected in production; missing provider shows UNCONFIGURED/UNAVAILABLE, no mock LIVE; unknown pilot/stage switch disabled. Stage expiry/failure preserves prior output and does not count completed.
- **No-go:** No provider keys/calls; no client creation/merge endpoint; no inferred profile defaults; no parallel orchestrator; no pilot activation.
- **Done:** API and persistence tests pass including restart, exact workflow transitions/OpenAPI match, safety negatives pass; external adapters remain clearly UNAVAILABLE until approved.

### 【U-007】Deliver canonical persisted sourced brief and one reviewable view
- **Batch / owner role:** 1B / Brief domain owner (backend) paired with one frontend brief owner under single U-004 shared component owner; backend/frontend same unit acceptance, no duplicate brief implementers.
- **Purpose / scope:** Resolve client/meeting context via existing workflow, explicit brief generate/regenerate/edit, persist existing `briefs.sections` as canonical content linked to artifact revision/items/source manifests; GET/history/section review/feedback; one renderer used by full page and modal/mobile surfaces. Maintain section independence and truthful provenance.
- **Inputs / outputs:** Inputs `workflow_id`, optional meeting, prior `ArtifactRef`, selected section keys; entitled source adapters and context revision. Output real persisted brief ID/version with five sections, each states/sources/as-of/origin/evidence/item hash/review state; canonical response projection `data.brief.sections` only.
- **Contracts:** API-004…006, 031…033, API-069; `Brief`, `ArtifactRef`, `ReviewItem`, Source/Region types per architecture §6.3. API-004 generation only; GET never generates. Each section review names current exact item hash. `briefs.sections` is sole canonical content source; no second generic JSON copy.
- **Files owned:** Backend `backend/app/api/v1/endpoints/briefs.py`; `backend/app/schemas/brief.py`; `backend/app/services/brief/{brief_service.py,source_assembly.py}`; `backend/tests/brief/**`. Frontend `frontend/app/brief/[clientId]/page.tsx`, `frontend/app/workflows/[workflowId]/briefs/[briefId]/page.tsx` (new as exact route requires), `frontend/components/{CanonicalBriefView.tsx,ReviewableArtifact.tsx,ProvenanceChip.tsx,SourceDetail.tsx,BriefModal.tsx}`; `frontend/tests/brief/**`. Do not edit shared API client/primitives (U-004) or common action approvals (U-010).
- **Dependencies:** Batch 0; U-006 workflow/context; U-005 lineage repository. Use current section reviews from U-005.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/brief -q`; `cd frontend && npx tsc --noEmit && npm test -- --runInBand tests/brief` (adapt only test-runner syntax to repository script, report exact command). Browser/test evidence for explicit generate→durable write/readback→render→edit append revision→section review→regenerate unaffected sections preserved but approvals not inherited→stale preview invalidated. Assert GET/reload/modal opening makes no POST. Every displayed material claim links to entitled real source and timestamp/or explicit unknown; partial unavailable section leaves unaffected content.
- **Negative/security/feature-ON:** Synthetic mock source marked FIXTURE and no LIVE; missing sources/conflicts/stale states visible; no fabricated facts/as-of/AI provenance; changed content/hash rejects stale review; failing one source does not erase previous/current unaffected sections; unauthorized client source hidden.
- **No-go:** Do not change legacy brief PK/version type or migrate existing rows; no external market/news credentials; do not expose fixture content as client-ready; no second brief API/component path; no auto-approve.
- **Done:** All five section contract fixtures pass with full persistence/readback and same component at each entry point; negative stale/provenance/access tests pass; production source integration remains external gate.

### 【U-008】Implement meeting consent, capture controls, manual notes and extraction recovery
- **Batch / owner role:** 2A / Meeting workflow owner (exclusive meeting/capture/transcript/extraction service and UI paths).
- **Purpose / scope:** Record only approved consent; capture lifecycle/lease and withdrawal stop behavior; transcript evidence/corrections/suppression; manual notes fallback; extraction with evidence-linked items and explicit edit/review; preserve last-confirmed progress across outage/restart.
- **Inputs / outputs:** Meeting + current approved policy/config + participant coverage and explicit consent; recording adapter result. Outputs `Consent`, `Capture`, transcript/notes/extraction artifacts with source refs, owner/date only when evidenced or RM entered, state/last confirmed positions.
- **Contracts:** API-034…044 plus API-010; attachment endpoints described architecture §6.4 only if covered under approved policy; no request shape redefinition. Common audit, lineage, lease and error rules apply.
- **Files owned:** Backend `backend/app/api/v1/endpoints/{meetings.py,captures.py,transcripts.py,notes.py,extractions.py}`; `backend/app/schemas/meeting.py`; `backend/app/services/meeting/**`, `backend/app/adapters/transcription/**`; `backend/tests/meeting/**`. Frontend `frontend/app/workflows/[workflowId]/meeting/page.tsx`, `/transcript/page.tsx`, components `ConsentRecordingPanel.tsx`, `EvidenceLinkedItemEditor.tsx`; meeting tests. Never edit shared components outside these owner files.
- **Dependencies:** U-006 workflow; U-005 persistence/lease/lineage; U-003 identity; U-004 AsyncRegion. U-007 shared review/provenance components available.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/meeting -q`; frontend typecheck + meeting UI tests. Synthetic no-network adapter covers consent accepted/declined/withdrawn, outage, partial audio, duplicate start, session loss, provider stop unresolved. Verify decline/unknown blocks stream; withdrawal invalidates derived refs and stops client+server stream; manual notes persist; restart retains last confirmed positions; complete transcript only on confirmed provider completion. Test transcript corrections/suppression create new immutable revision and downstream invalidation.
- **Negative/security/feature-ON:** No capture without approved current consent/coverage/device/lease; no RSVP-implies-consent; no audio/transcript in telemetry; no AI fabricated speaker/time/owner/date/confidence; low confidence needs review; suppression respects retention/legal hold; no unsupported format accepted.
- **No-go:** No real recording/transcription service/credential, no audio upload to internet, no policy invention, no device release certification. If policy unavailable UI remains manual notes + explicit UNCONFIGURED, not “integration complete.”
- **Done:** Isolated lifecycle/persistence/restart and negative tests pass, audits prove decline/withdrawal/stop outcomes; any live capture acceptance explicitly external-blocked.

### 【U-009】Deliver typed review and transactional action preview/outbox lifecycle
- **Batch / owner role:** 2B / Backend actions platform owner (sole owner of action preview/authorization/outbox/reconciliation code, shared UI approval/delivery status owner coordinates only UI components).
- **Purpose / scope:** Separate artifact review from action authorization; immutable exact server-side preview; authorization tied to preview hash and actor/class; explicit execute by authorization ID only; transactional idempotent outbox, lease/attempt/reconciliation/readback and safe retry. Generic platform action plumbing only; domain artifacts are downstream producers.
- **Inputs / outputs:** Current reviewed exact artifact ref, class-specific config/source/destination/dependency state. Output preview, authorization, persisted action/attempt statuses with provider receipts/readback; canonical internal notes/memory writes only upon authorized action where relevant.
- **Contracts:** API-010, API-045…051, API-011 body **only `{authorization_id:UUID}`**, API-012 GET read only, API-050 readback only, API-051 only `FAILED_SAFE` + current approval + idempotency guarantee. Common outbox states and transaction semantics §§4.3–4.4.
- **Files owned:** Backend `backend/app/api/v1/endpoints/{artifacts.py,actions.py}`; `backend/app/schemas/{review.py,action.py}`; `backend/app/services/actions/**`, `backend/app/adapters/{crm,task,message,ticket,memory}/**` interfaces with isolated synthetic adapters only; `backend/tests/actions/**`. Frontend `frontend/components/{ApprovalPreview.tsx,DeliveryStatus.tsx,VersionHistory.tsx,ConflictDialog.tsx}` generic component only; no feature page ownership.
- **Dependencies:** U-005 lineage/audit/idempotency/outbox; U-003 auth; U-006 workflow; U-004 common API; U-007 review types. U-008 for meeting-derived actions is not required for core framework test and can integrate later.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/actions -q`; PostgreSQL synthetic integration + deterministic adapter tests crash before/after dispatch, accepted-then-timeout, expired lease, stale worker, readback outage, not-accepted retry, concurrency with same/different idempotency keys. Verify action rows + attempts + audit survive process restart; only confirmed receipt and required readback yields SUCCEEDED. Internal write+audit+idempotency atomic rollback test. Frontend tests exact preview bytes/hash/class/destination and status uncertainty.
- **Negative/security/feature-ON:** Reject arbitrary request/provider/destination/action-class fields and stale/wrong-class/hash/consent/config/assessment/context/entitlement refs. No dispatch for unapproved preview; no duplicate authorization under concurrent clicks or different keys; UNKNOWN never resend; GET/status/reload never dispatch; fixture preview cannot target live adapter.
- **No-go:** No live CRM/task/email/ticket calls, no send or trade; no speculative retry, no automatic action from artifact review or workflow stage, no action ID pretending provider success.
- **Done:** All isolated fault/concurrency/restart/security cases pass; provider-readback gate separate. This is implementation+isolated acceptance, not LIVE integration acceptance.

### 【U-010】Deliver book-wide priority ranking, source reasons and durable RM controls
- **Batch / owner role:** 3A / Priority domain owner (sole ranking-service and priority API ownership).
- **Purpose / scope:** Book-scoped evaluation up to ten unique entitled eligible clients with reasons/source/time, empty-vs-outage distinction, DST/local day, explicit refresh; persistent snooze/dismiss/pin, contact outcomes; protect DNC and protected-attribute exclusion.
- **Inputs / outputs:** Assigned book, date, IANA timezone, approved ranking config/signal freshness, current authorized source snapshot, trigger. Output evaluation/reasons with source hashes, controls/outcomes and state CURRENT/STALE/FAILED.
- **Contracts:** API-015/016/053/054/055; Priority DTOs and API-002/021 only as reads; architecture §6.6. No redefining weights/limits beyond contract's cap of 10.
- **Files owned:** Backend `backend/app/api/v1/endpoints/priorities.py` (new); `backend/app/schemas/priority.py`; `backend/app/services/ranking/ranking_service.py`; new `backend/app/services/priority/**`; `backend/app/tests/priority/**`. Frontend `frontend/app/priorities/page.tsx`, priority-specific components `PriorityReasonList.tsx`, `PriorityControls.tsx`; tests. Do not edit ranking APIs used by outreach.
- **Dependencies:** U-005 persistence/audit; U-003 authorization; U-006 current client/context; U-004 frontend shared components. 4B config read interface may initially return UNCONFIGURED; use named synthetic config only in tests.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/priority -q`; synthetic PostgreSQL + deterministic source fixtures: <=10 unique currently entitled/non-DNC clients; empty book is successful empty evaluation, outage is 503/stale not fabricated empty; DST boundary/local date; reason links source IDs/as-of and rank change; snooze/dismiss/pin persists and changes next evaluation only per explicit fixture policy; contact outcome cannot infer two-way/attendance and DNC still blocks outreach. Verify unauthorized rows are filtered before response and counts.
- **Negative/security/feature-ON:** Ranking schema rejects protected attribute; no risk/preferences inferred; expired/stale source state represented; controls cannot override eligibility or top-ten cap; no filler clients; exception not 200 empty list; control config unknown blocks change.
- **No-go:** No guessed weights/thresholds/snooze duration; no production customer ranking; no PII/protected attribute; do not edit 3B messaging or shared metric computation.
- **Done:** API, DST, controls, DNC, provenance, access, empty/outage tests pass; institutional ranking tuning remains UNCONFIGURED pending DEC-03.

### 【U-011】Deliver grounded outreach/follow-up drafts and explicitly approved send
- **Batch / owner role:** 3B / Messaging domain owner (backend message/policy/send integration owner; reuse U-009 action core).
- **Purpose / scope:** Shared composer modes for follow-up from accepted meeting items and outreach from current priority reason; editable grounded draft, confirmed recipient, current DNC/channel/disclosure checks; send only explicit preview→authorization→execute; truthful delivery status.
- **Inputs / outputs:** Accepted ItemRefs and/or PriorityReasonRef; selected permitted channel/template/contact. Output typed immutable Message artifact, preview/authorization/action, provider state and readback; no automated send.
- **Contracts:** API-047, API-048…052, API-010; API-015/016/055 basis; MessageGenerate/Message/Action DTOs; API-011 ID-only execution. Exact IDs in architecture §6.5–6.6.
- **Files owned:** Backend `backend/app/api/v1/endpoints/messages.py` (new); `backend/app/schemas/message.py`; `backend/app/services/messaging/**`; `backend/app/adapters/message/**`; `backend/tests/messaging/**`. Frontend `frontend/app/workflows/[workflowId]/message/[draftId]/page.tsx`; `frontend/components/MessageComposer.tsx`; messaging-specific tests. U-009 owns generic ApprovalPreview/DeliveryStatus shared files; submit changes to owner.
- **Dependencies:** U-009 action core; U-006 workflow/context; U-007 briefs/review; U-008 for transcript follow-up basis (meeting manual-notes flow can test before U-008); U-010 priority ref for outreach; 4B approved config reader (until available, state UNCONFIGURED).
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/messaging -q`; ON synthetic test catalog with generated source evidence and fake transport. Validate accepted-only basis, no unsupported claim, missing facts omitted, recipient/body/template/disclosure exact preview hash; content/recipient/DNC/consent/template/policy change invalidates authorization; explicit execution with accepted receipt/readback; provider timeout UNKNOWN reconciles without duplicate; status UI truthful. Send counter is zero on rendering/GET/reload.
- **Negative/security/feature-ON:** DNC, channel opt-out, missing disclosure, unconfirmed recipient, unknown template/policy, no current entitlement or fixture→live mismatch blocks. Manual approval required even when enabled. No scheduling/CC/BCC/auto-send. On fixture evidence visibly says FIXTURE.
- **No-go:** No external email/SMS credential or message; no live recipient; no new channel or nonfrozen message fields; no auto-send.
- **Done:** Isolated full draft-preview-approval-execute-readback plus failure/replay test passes; external recipient/provider/legal approval remains a separate LIVE gate.

### 【U-012】Deliver Tier B product discovery and suitability pre-screen
- **Batch / owner role:** 4A / Product/suitability domain owner (exclusive product catalog/search/assessment code).
- **Purpose / scope:** Natural-language interpretation produces editable confirmed filters; search current entitled synthetic products; source metrics/comparison; assessment with current profile; permitted soft override only; hard stop and missing/stale profile block Green and ticket.
- **Inputs / outputs:** Workflow context/client, query, product/catalog and suitability policy refs, profile/account/amount and explicit accepted filter edits. Output interpretation/search/comparison/assessment/override artifacts and sources.
- **Contracts:** API-056…062, API-010 reviews; API-048/049/011 for downstream ticket action only (actual ticket handoff uses U-009 shared action). ProductRef/ProductFilter/ProductMetric/Assessment/SuitabilityOverride. Architecture §6.7.
- **Files owned:** Backend `backend/app/api/v1/endpoints/products.py` and `assessments.py`; `backend/app/schemas/product.py`; `backend/app/services/products/**`; `backend/app/adapters/{product,suitability}/**` synthetic/unavailable only; `backend/tests/products/**`. Frontend `frontend/app/workflows/[workflowId]/products/page.tsx`, `frontend/app/workflows/[workflowId]/assessment/[assessmentId]/page.tsx`; product-specific components/tests. No config/editor ownership.
- **Dependencies:** U-006 workflows/context; U-005 persistence/artifacts; U-009 review/action core; 4B config catalog interface; U-003 authorization. Parallel with priority/outreach once Batch 1 and U-009 available; this P1 unit may not block FR-01…15 delivery.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/products -q`; synthetic-only product fixture: displayed confirmed filters equal executed filters; hard restrictions immutable; no results gives explanation, soft suggestions do not auto-modify; metric/source/as-of preserved, missing metrics null; current profile can yield pre-screen rating; missing/expired/conflict cannot be GREEN and no ticket; hard stop override denied; permitted soft override requires exact actor/policy/rationale and preserves original rating. UI display `Pre-screen, not compliance approval`.
- **Negative/security/feature-ON:** Cross-tenant/unentitled/stale products excluded; ambiguous interpretation blocks until edited; no automatic hard filter relaxation, unsupported monetary return/ESG value or profile mutation; provider outage not empty success; unknown suitability policy = UNAVAILABLE/UNCONFIGURED.
- **No-go:** No live provider/product data, actual advice/approval, trade execution, price/yield fabrications, inferred institution suitability policy.
- **Done:** Isolated interpretation/search/suitability/override integration and negative tests pass; live licensing/provider and legal suitability gate remains external.

### 【U-013】Deliver admin configuration, capability controls, audit, telemetry and measurement
- **Batch / owner role:** 4B / Governance/measurement platform owner (one owner for configuration lifecycle, gate/metric computations and oversight endpoints).
- **Purpose / scope:** Typed five-class configuration draft→validate→approve→activate/readback; scoped flags/stage switches/readiness; append-only audit and telemetry; metrics/guardrails with denominators/baselines and fixture segregation. No institutional configuration is invented.
- **Inputs / outputs:** Exact scope plus configuration/catalog/evidence refs and permissions; output immutable config/approval/activation/control revisions, readiness blockers, audit/telemetry and metric results with null NOT_MEASURED/UNCONFIGURED state.
- **Contracts:** API-018/019/063…068/070…074, API-017 read-only readiness; `ConfigurationValue`, `CapabilityControl`, `GateEvidence`, `AuditEvent`, `MetricResult`, `GuardrailResult`; architecture §§6.8–6.9. Individual features emit versioned telemetry against API-074 but do not duplicate metric computation.
- **Files owned:** Backend `backend/app/api/v1/endpoints/{admin.py,oversight.py,telemetry.py}`; `backend/app/schemas/{admin.py,telemetry.py}`; `backend/app/services/{configuration,readiness,metrics,telemetry}/**`; `backend/tests/{admin,oversight,telemetry}/**`. Frontend `frontend/app/admin/page.tsx`, `frontend/app/oversight/page.tsx`, `frontend/components/{ConfigEditor.tsx,MetricCard.tsx,GateChecklist.tsx}`. Migration edits via U-002 owner only.
- **Dependencies:** U-003 identity/authorization; U-005 config/audit/telemetry persistence; U-006 registry/stage control; U-004 shared UI. U-009 action readiness integration via read-only summaries.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/admin tests/oversight tests/telemetry -q`; PostgreSQL synthetic tests for five classes, tenant/book/jurisdiction precedence, immutable draft/approval/activation/readback, separate author/approver/activator, activation block without evidence, secrets never echoed; flags absent=OFF, OFF direct endpoints deny; authorized ON only with isolated named fixtures; telemetry cannot self-report approved/sent/completed, event actor/scope/time server derived; metrics include numerator, denominator, baseline state and limitations; unknown denominator -> null NOT_MEASURED, fixtures excluded from live metrics; audit mutation denied and chain concurrency valid.
- **Negative/security/feature-ON:** Cross-scope configuration resolution denied; disabled ancestor beats enabled child; no flag defaults ON; no operator override of hard stop/autonomy; no self-approval; credential secret value never returned/logged; no client/private prompt/audio in telemetry; no fabricated historic gates or causal retention claim.
- **No-go:** No live secrets/provider calls, no actual pilot enablement, no production gate acceptance, no new business thresholds or policies; no audit deletion.
- **Done:** contract and synthetic integration tests pass; all required inventory control groups have owner/evidence binding; operational/security/legal/provider certification remains external.

### 【U-014】Deliver gated FR-21 mobile scoped-task parity
- **Batch / owner role:** 5A / Frontend mobile/accessibility owner; security owner reviews device/session policy integration.
- **Purpose / scope:** At small-screen/zoom support client lookup, brief reading, priorities/reasons/controls and complete outreach review/approval using identical API, authorization, current policy and artifact refs; show desktop-only explanations where approved policy requires.
- **Inputs / outputs:** Existing desktop canonical components/API contracts and approved supported-device/session/cache config. Output responsive layouts with accessible controls and no weak mobile-only approval path.
- **Contracts:** API-002/003, 004/005, 015/016/053/054, 048/049/011 as relevant; API-001 session/device state. No client-side new endpoint or abbreviated approval semantics.
- **Files owned:** `frontend/app/{clients/page.tsx,brief/[clientId]/page.tsx,priorities/page.tsx,workflows/[workflowId]/message/[draftId]/page.tsx}` responsive layouts only; `frontend/components/mobile/**`; `frontend/tests/mobile/**`. No backend contract/auth files.
- **Dependencies:** U-007, U-009, U-010, U-011, U-013; U-004 shell/API. Can run parallel with pilots after those references stable.
- **Acceptance evidence / commands:** `cd frontend && npx tsc --noEmit && npm test -- --runInBand tests/mobile`; browser tests at 320px, 200% zoom and supported desktop widths: no page overflow; semantic/keyboard/focus, dialog behavior, error announcements, text+icon state; full current recipient/content/disclosure/action preview visible before explicit approval; session/scope switch aborts previous request; existing canonical components reused. DEC-08 supported OS/cache/device gates shown as blockers until approved.
- **Negative/security/feature-ON:** No sensitive browser storage/service-worker caching, no stale cross-client late response, no different approval capability on mobile, no unsupported-device sensitive action. No mobile recording/ticket release claim unless DEC-08 explicitly permits.
- **No-go:** Responsive support is not supported-device production certification; no distribution/MDM/device policy decisions or offline sensitive cache.
- **Done:** UI tests and accessibility evidence pass; DEC-08 remains visibly gated unless approved evidence is supplied.

### 【U-015】Deliver default-OFF Shariah evidence and estimate pilot
- **Batch / owner role:** 5B / Pilot domain owner (Shariah workflow backend/frontend, with Compliance/SSB evidence owner external); unique pilot code owner.
- **Purpose / scope:** FR-4.1 preference proposal on shared memory path, evidence-backed screening, method-driven itemized discussion estimate, complete review/evidence pack and internal archive finalization. Never authoritative ruling/advice.
- **Inputs / outputs:** Authorized pilot cohort, explicit synthetic ON-only SSB/method/catalog evidence or externally approved DEC-05 refs; product/holding refs; estimate required input evidence. Output typed artifacts + skill runs, advisor evidence and durable archive readback when isolated service supports it.
- **Contracts:** API-075…080 and API-010; shared MEMORY_WRITE requires separate U-009 authorization; use API-076 screen/077 estimate/078 pack/079 advisor/080 finalization exact request shape. Architecture §6.10.
- **Files owned:** Backend `backend/app/api/v1/endpoints/shariah.py`; `backend/app/schemas/pilot.py` Shariah discriminants only (coordinate sole schema file ownership with U-003/4B; contribute patch if conflict); `backend/app/services/shariah/**`; `backend/app/adapters/shariah/**` fixture/unavailable; `backend/tests/pilot_shariah/**`. Frontend `frontend/app/workflows/[workflowId]/shariah/page.tsx`, `frontend/components/pilot/ShariahReview.tsx`; tests. Do not change shared flag/config service.
- **Dependencies:** U-005 artifacts; U-006 context/registry; U-009 review/action; U-012 product refs; U-013 flags/readiness/config; U-004 UI. Pilot unit does not block core GA.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/pilot_shariah -q`; feature OFF/no row returns 409 FEATURE_DISABLED and no write; isolated synthetic ON tests PASS/FAIL/INSUFFICIENT_EVIDENCE; stale/missing SSB evidence cannot label compliant; unknown nisab/hawl/convention/method/ratio returns unavailable/null, no default; estimate itemized and explicit discussion/advisor caveat; incomplete/stale pack cannot finalize; complete pack requires current reviews/advisor evidence and archive durable readback. Preference propagates through shared context only after approved MEMORY_WRITE.
- **Negative/security/feature-ON:** Wrong cohort/node/tenant denied before prompt construction; no noncompliant candidate recommended as compliant; no inferred protected-demographic preference; no direct memory write, client send, trade, fatwa or SSB-authoritative claim from RM confirmation. Fixture artifacts cannot mix live.
- **No-go:** No real SSB policy inference, production screening/rates, religious ruling or pilot toggle; live gate remains blocked until named SSB/legal/data approvals.
- **Done:** OFF and isolated ON synthetic test suites pass; external governance sign-off is separately recorded as blocked/not supplied, not claimed complete.

### 【U-016】Deliver default-OFF family graph and liquidity pilot
- **Batch / owner role:** 5C / Pilot family-data owner (backend+frontend family pilot; Security/data-governance reviewer external); unique owner for family routes/graph services.
- **Purpose / scope:** FR-5.1 entitled graph/proposal/explicit confirmation/consolidation; FR-5.2 attendee-separated packs and illustrative scenarios; FR-5.3 verified notice, 90-day forecast and forecast-vs-actual. Keep client/node/attendee entitlement checks before every graph read/prompt/output.
- **Inputs / outputs:** Exact authorized household, current per-node entitlement revision, synthetic fixture or approved DEC-06 entity/custodian/FX/tolerance/evidence catalogs; meeting attendees and explicitly confirmed source refs. Output typed immutable artifacts/graph versions, separate attendee packs, reconciliation/forecast/actual comparison.
- **Contracts:** API-081…091; API-010 review; API-048/049 only if action previews needed (pack never sends). Shared scope/context rules and architecture §6.11; precise SQL `households/graph_nodes/graph_edges/node_entitlements` tables.
- **Files owned:** Backend `backend/app/api/v1/endpoints/households.py`; `backend/app/schemas/pilot.py` family discriminants (submit changes to schema-file owner); `backend/app/services/households/**`; `backend/app/adapters/{custodian,document}/**` synthetic/unavailable; `backend/tests/pilot_family/**`. Frontend `frontend/app/workflows/[workflowId]/family/page.tsx`, `frontend/components/pilot/{GraphWithTable,AttendeePack,FamilyScenario,LiquidityForecast}.tsx`; tests. Do not change common authorization or flags.
- **Dependencies:** U-005 persistence; U-006 context/workflow; U-009 review; U-013 feature controls/config/telemetry; U-004 accessible graph/table primitives. Pilot OFF is testable before ON feature dependencies are present.
- **Acceptance evidence / commands:** `cd backend && uv run pytest tests/pilot_family -q`; OFF/absent flag direct route denied and no default row; isolated synthetic ON tests for unauthorized node excluded before prompt and logs, revocation invalidates context/review/previews, only accepted nodes/edges canonicalized, same-tenant cross-client household allowed only through explicit graph FK entitlement, unresolved FX/tolerance partial not false total, unknown attendee blocked before generation, each attendee gets disjoint immutable pack and no hidden counts, scenario assumptions all illustrative, unverified notice excluded, only verified notices forecast, no actual means NOT_YET_OBSERVED not zero error, 90-day forecast compares verified actual evidence. Check audit/telemetry event safe fields only.
- **Negative/security/feature-ON:** No unknown graph types auto-canonical; edges require accepted authorized endpoints; revocation denies old output access; no attendee overexposure; no unsupported capital notice fields guessed; no payment/transfer/marketplace/full planning.
- **No-go:** No live household data/custodian provider, no ownership inference or entitlement backfill; no institutional tolerance/scenario policy invented; no pilot enablement or production claim.
- **Done:** OFF gates and isolated synthetic ON security/data tests pass; DEC-06 data governance and pilot readiness remain separate external blockers.

### 【U-017】Run independent QA, security review and release gate evidence
- **Batch / owner role:** 6 / Independent QA lead + independent security/code reviewer + release integrator (none may be feature author for reviewed path).
- **Purpose / scope:** Verify acceptance end-to-end at integration level and compile reproducible gate evidence. Deliver test/report artifacts and a go/no-go decision; no feature implementation mixed into acceptance.
- **Inputs / outputs:** Merged units and their test evidence, isolated disposable DB/provider fixture environment, authoritative inventory and frozen PRD/design/contracts. Output signed reviewer records, test reports, API/OpenAPI drift report, FR/control coverage evidence, external blocker list, release gate disposition.
- **Contracts:** All API IDs as cited in cards; G0–G4 requirement gates; architecture §§8–9; product design pages P-001…P-020; full control inventory `deliverables/01_PRD_Requirement_Inventory.md` §§2–12.
- **Files owned:** `backend/tests/integration/**`, `frontend/tests/e2e/**`, CI test configuration only with owner approval; `deliverables/REMEDIATION_06_Release_Evidence.md` (create only if release lead requests an evidence artifact; otherwise attach CI artifact). No production source changes without returning to feature owner.
- **Dependencies:** All feature batches. Independent code review and security/QA gates are mandatory.
- **Acceptance evidence / commands:** At minimum run backend full suite and import/OpenAPI contract tests; PostgreSQL 15 disposable empty and synthetic existing-schema migration matrix; `npm ci && npx tsc --noEmit && npm run build`; full browser generate→persist→render→edit→review→revision invalidation; auth/entitlement negative matrix; action concurrency/crash/readback matrix; closed-loop meeting outcome/memory→priority→later brief through same orchestrator; OFF direct-route/API pilot denial and synthetic ON isolation suites. Preserve machine-readable logs, DB assertions/checksums, API diff and defect list. Independently sample audit/telemetry for secret/PII leakage and assertion-only positives.
- **Negative/security/feature-ON:** Fail gate on any cross-tenant/book/node data leak, false LIVE, false success, arbitrary action payload/destination, duplicate write/send, no-consent capture, hard-stop override, auto-send/trade, default-on pilot, source-only evidence, empty DB migration short-circuit or destructive behavior. Cross-cutting NFR targets (p95/1000 concurrent/99.5% uptime), backups/restore, provider/legal/security/residency/licensing and production deployment require separately produced evidence; do not mark passed via local CI.
- **No-go:** No production deploy, existing DB migrations, external credentials/live provider operations, real client data or live business side effects. Do not call fail-closed UNCONFIGURED screen a completed integration.
- **Done:** Reviewers issue gate-by-gate PASS/FAIL/BLOCKED with linked evidence; implementation+isolated tests and externally blocked LIVE/production acceptance are reported as separate columns; no failed/blocked gate is relabeled complete.

## 4. Coverage matrix — all 28 functional requirements

> PRD labels remain distinct from inventory tiers: 15 native P0 labels are FR-01…FR-15. Tier A audit grouping contains 17 IDs by also including FR-20 and FR-22; do not call 17 native P0. Core GA has 22 FRs, includes FR-21 (cross-cutting and not assigned to the inventory §12.2 literal tier lists; mobile release gated by DEC-08), Tier B FR-16…19 is P1 for core GA and cannot delay P0. Six pilot FRs remain default-OFF; FR-5.3 is P2. Tier D exclusions are not feature gaps.

| FR | Implementation unit(s) | Test/evidence anchor | Release/externally blocked boundary |
|---|---|---|---|
| FR-01 | U-006, U-007 | Resolved entitled client/event → explicit generation → persisted brief ID/version; ambiguous resolution path | Core P0; calendar provider external |
| FR-02 | U-007 | Every material claim links source/receipt/as-of and Recorded-vs-Derived; no fabricated LIVE | Core P0; real sources external |
| FR-03 | U-007 | Section failure isolation, revision regeneration, feedback audit, unaffected sections preserved | Core P0 |
| FR-04 | U-008 | Consent/policy before capture, declined/withdrawn/session loss stops client+server capture, audit | Core P0; policy/provider approvals external |
| FR-05 | U-008 | Speaker/time evidence, extraction item refs, null unsupported owner/date, correction/suppression invalidates | Core P0; model/provider external |
| FR-06 | U-008 | Manual note fallback, last confirmed position, outage recovery/restart, no false complete | Core P0; provider external |
| FR-07 | U-007, U-008, U-009 | Per section/item accept/edit/reject with exact old/new basis; review distinct from action authorization | Core P0 |
| FR-08 | U-009 | CRM/task preview→authorization→synthetic effect→readback; concurrency and accepted-timeout reconcile | Core P0; live CRM/task external |
| FR-09 | U-008, U-009, U-011 | Follow-up uses accepted outcomes, exact recipient/disclosure, rejecting basis invalidates draft; no send on draft | Core P0; live message provider external |
| FR-10 | U-009, U-012 | Evidence-backed exact product/account/amount + current assessment; missing field blocks; prefill only | Core P0 handoff guardrail; product discovery Tier B remains no P0 delay; no execution API |
| FR-11 | U-010 | <=10 unique entitled/non-DNC, DST/local day, empty ≠ outage, explicit refresh | Core P0; ranking policy external UNCONFIGURED until DEC-03 |
| FR-12 | U-010 | Inspect reason signals/source/as-of/rank delta; reject protected attributes | Core P0 |
| FR-13 | U-010 | Persistent snooze/dismiss/pin and outcome; policy-defined effects; no inferred client intent | Core P0; DEC-03 policy external |
| FR-14 | U-011 | Reason/available facts/opener grounded editable draft; unsupported facts omitted | Core P0 |
| FR-15 | U-009, U-011 | Current DNC/channel/disclosure and human authorization; confirmed provider state only; no auto-send | Core P0; provider/legal approvals external |
| FR-16 | U-012 | Interpreted editable filters equal actual search; no silent hard-filter relaxation | Tier B/P1 core GA; licensed universe external |
| FR-17 | U-012 | Comparison metrics/source/as-of, missing metric null, no-results rationale | Tier B/P1 core GA; product feed/license external |
| FR-18 | U-012 | Assessment input/policy hash current; missing/expired cannot Green; failure unavailable | Tier B/P1 core GA; approved suitability policy external |
| FR-19 | U-012 | Hard stop override denied; exact allowed soft override actor/rationale/audit; original rating immutable | Tier B/P1 core GA; authority/policy external |
| FR-20 | U-006, U-007, U-009, U-013 | Persistent same orchestrator/registry/context; lineage, version, review and approvals; closed-loop integration in U-017 | Tier A audit grouping cross-cutting, inferred V1-wide, not native P0 label |
| FR-21 | U-004, U-014 | Responsive client/brief/priorities/outreach at 320px/200%, same auth/preview, session safety | Core scope; mobile release DEC-08/NFR-08 externally gated |
| FR-22 | U-013 | Five typed config classes; draft/validate/independent approve/activate/readback/audit, no secret echo | Tier A audit grouping cross-cutting, inferred V1-wide; institutional approvals external |
| FR-4.1 | U-015 | Preference shared memory/context only after separate authorized write; screening current evidence and propagation | Tier C default-OFF; SSB/legal/data approvals external |
| FR-4.2 | U-015 | Itemized method/nisab/hawl/convention/evidence, unknown inputs null/unavailable, advisor caveat | Tier C default-OFF; DEC-05 external |
| FR-4.3 | U-015 | Incomplete/stale evidence blocks finalization; complete evidence archive/readback; not fatwa/client send | Tier C default-OFF; archive/SSB approvals external |
| FR-5.1 | U-016 | Per-node pre-prompt entitlement, accepted-only graph, revocation, reconciliation evidence | Tier C default-OFF; DEC-06 external |
| FR-5.2 | U-016 | Unknown attendee blocks before generation; per-attendee isolated packs; illustrative assumptions | Tier C default-OFF; data/entitlement governance external |
| FR-5.3 | U-016 | Verified-notice-only 90-day forecast; actual absent NOT_YET_OBSERVED; sourced compare; no payment | Tier C default-OFF/P2; DEC-06 external |

## 5. Cross-cutting coverage and controls ownership

Every control is implemented and verified according to the exact frozen `deliverables/01_PRD_Requirement_Inventory.md` criteria and architecture §8.2/§9; the summaries below bind each group to its card(s), not a replacement definition.

| Control inventory | Primary units | Observable evidence / blockers |
|---|---|---|
| D0 identity/authorization/tenant | U-003, U-005, U-006, U-017 | Unauthorized tenant/book/client/session/worker denied before context; external SSO/security approval remains gate |
| D1 client/calendar/portfolio/source authority | U-006, U-007, U-012 | Typed adapter states, explicit ambiguity resolution, source conflicts; provider/rights external |
| D2 consent and capture | U-008 | Consent lease, withdrawal/stop confirmation and audit; legal/security/provider approvals external |
| D3 product/KYC/suitability | U-012 | Current-profile/hard-stop tests; institution-specific catalog external |
| D4 measurement/telemetry | U-013, all features emit events, U-017 | Denominator/baseline/environment tags; no fixtures in live metrics |
| D5 persistent memory/graph/orchestrator | U-005, U-006, U-009, U-015, U-016 | Restart-safe records and same registry/context; cross-skill closed loop by U-017 |
| B-01…B-12 | U-006…U-016 mapped above | Partial/stale/conflict, manual fallback, no duplicates, DNC, suitability, SSB/household denials tested |
| NFR-01…NFR-11 | U-001, U-004, U-005, U-017; domain units | Local measurable perf/a11y/error/secret checks; 1000 concurrency, uptime, backup/restore, privacy/residency/security contractual evidence is external, not locally inferred |
| GOV-01…GOV-08 | U-009, U-012…U-017 | Append-only audit, separate authority, stage kill switch, evaluations/rollback and explicit blockers |
| INT-01…INT-11 | U-006…U-012, U-015/16 | Typed fixtures/outage/rate-limit/conflict tests; live provider contracts/credentials/licensing external |
| M-01…M-10 / TEL-01…TEL-10 | U-013 + feature units | Stable definitions/events/correlation and null when unknown denominator; baseline-first business validation external |
| GRD-01…GRD-10 | U-003, U-008…U-017 | Auth/context isolation; no unapproved send; evidence/rejection/DNC/protected attribute/reason/ticket controls hard fail |
| GATE-01…GATE-X | U-001, U-002, U-004, U-005, U-017 | G0 reproducible boot/build/disposable migration; G1 FR-01…15; G2 FR-16…22/C-01…16; G3 per-pilot evidence; G4 externally owned production evidence |
| C-01…C-16 | U-006, U-007, U-009, U-013, U-017 | Persistent copilot, stage lifecycle, shared context, action review, event/telemetry, no manual stitch in numerator; two-persona/training/support gates evidence-based |
| C-17…C-18 | U-015, U-016, U-017 | Pilot-only synthetic ON and independent governance evidence; cannot block core GA |

## 6. Parallel staffing recommendation / dispatch sequence

| Developer role | Initial units | Notes |
|---|---|---|
| Backend runtime owner | U-001 | First card immediately dispatchable; owns startup/config/database/health boundary only. |
| Migration owner | U-002 | Immediately dispatchable for static repair/harness; applied-history graph choice stays HOLD absent evidence. |
| Platform/security backend owner | U-003 | Immediately dispatchable; sole DTO/auth/scope owner. |
| Frontend platform owner | U-004 | Immediately dispatchable; sole API client/shared component baseline owner. |
| Persistence platform owner | U-005 | Start after U-002/U-003; should not compete for migrations. |
| Copilot/context owner | U-006 | Start when Batch 0 complete; single orchestrator/catalog owner. |
| Brief full-stack owner | U-007 | Start in parallel with U-006 after Batch 0; owns one canonical renderer and brief endpoint path. |
| Meeting full-stack owner | U-008 | After U-006/U-007 shared types; meeting files separate from actions. |
| Action platform owner | U-009 | After U-005/U-006/U-007; must be a distinct owner from feature action consumers. |
| Priority owner | U-010 | Parallel with product only after core platform; do not share ranking code with outreach. |
| Messaging owner | U-011 | Depends on U-009 and priority refs; owns composer variant but not generic approval/status components. |
| Product/suitability owner | U-012 | Parallelizable, Tier B/P1, not a P0 blocker. |
| Governance/analytics owner | U-013 | Unique configuration/metrics/audit UI/backend owner; downstream features emit only. |
| Mobile/accessibility owner | U-014 | Starts once desktop shared components/features are stable; DEC-08 gate explicit. |
| Shariah pilot owner | U-015 | Parallel pilot lane, default OFF; external DEC-05 gate cannot be synthesized as passed. |
| Family pilot owner | U-016 | Parallel pilot lane, default OFF; no overlap with common auth/flags/migrations. |
| Independent QA/security/release integrator | U-017 | Must not be feature author; verifies artifacts and separates implementation from LIVE acceptance. |

**Earliest safe dispatch:** U-001, U-002, U-003 and U-004 can start simultaneously with the file ownership above and isolated test environments. U-005 is the first serial persistence card after U-002/U-003. Once the Batch 0 foundation is accepted, U-006 and U-007 are the first disjoint end-to-end feature lanes. No existing DB migration, external provider use, credential handling, live send/write, deployment, pilot activation or commit is authorized by this plan.

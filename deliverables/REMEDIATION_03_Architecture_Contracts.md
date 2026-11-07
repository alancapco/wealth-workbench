# Technical Architecture and Frozen Contracts — RM Workbench Remediation

**Revision:** 2 · 7 November 2026 · corrective handoff for lead acceptance. Supersedes revision 1 completely. **Not implementation acceptance, production certification, provider selection, pilot activation or authorization for live effects.**

**Authority:** complete `REMEDIATION_01_Requirements.md`; complete 508-line `REMEDIATION_02_Product_Design.md`; inventory §§2–12, particularly exact §12.2 tiers; consolidated and data/backend/frontend re-audits. Read-only code inspection includes actual models, routers, services, database dependency, Alembic files, manifests/locks, frontend API client and brief/graph components. Only architecture deliverables are changed. No credentials read, provider calls, app changes, deployment or commits.

**Normative companions:** `REMEDIATION_03A_Additive_Schema.sql` is the executable schema contract; this document is the normative DTO/behavior contract. SQL plus typed payloads below form the complete persistence definition; JSON is not permission for arbitrary payloads. All API/SQL/model changes must change both affected contracts and notify affected developers. Until lead accepts this revision, task #3 remains in progress.

## 1. Minimal stack and actual repair anchors

| Layer | Frozen choice | Version baseline / reason |
|---|---|---|
| Backend | Python 3.11, FastAPI, Pydantic 2, SQLAlchemy async | Retain project stack. Use existing `uv.lock` as reproducible remediation baseline, not a claim versions are secure/current; inspected lock has FastAPI 0.162.0, Pydantic 2.14.3, SQLAlchemy 2.1.8, Alembic 1.20.1, asyncpg 0.32.0. `uv sync --frozen` in CI/container/local; export any required `requirements.txt` from lock, never independent pins. Dependency security/compatibility review is a release gate. Do not perform unrelated major upgrades. |
| Database/migration | PostgreSQL 15-compatible SQL, asyncpg, async Alembic environment | Keep existing DB major and exact approved image digest in deployment config. Choose async Alembic using `AsyncConnection.run_sync`; remove sync `engine_from_config` path, avoiding an extra psycopg driver. No SQLite migration substitute. |
| Frontend | Existing Next 14.1.0 / React 18 / TypeScript / Axios / Tailwind / ECharts | Reuse `package-lock.json` with `npm ci`; exact installed versions are lock-resolved. No framework replacement. Fix graph typing with real typed ECharts node/category DTOs, not `any` or suppressions; escape text tooltips. |
| Coordination | PostgreSQL durable stage jobs/outbox; Redis optional cache only | No broker, agent framework, vector DB or event-bus addition. Existing unused pgvector/Timescale capability not required. |
| Identity | Institutional OIDC SSO; explicit isolated fixture principal | No self-registration/password feature or production header/user-name bypass. Signed claims and authoritative entitlement revision, not `RM001` prefix matching. |
| Integrations | Typed adapters in existing service boundaries | Provider selection/credentials are external inputs. Actual implementations disabled until approved; deterministic synthetic adapters support isolated contract/ON tests. |

Actual code anchors (observations, not fresh runtime claims): `models.py:14` declares `Client.id` UUID and holding/interaction FKs UUID; `Brief.version` is String, `Brief.sections` JSON. `brief_service.py` returns nested sections without persisting and fabricates provenance. `copilot_service.py` imports deleted `WorkflowStage/SourceKind`; market/init/seed import deleted models. `database.py` currently auto-commits after dependency yield and enables SQL echo in development; explicit use-case transactions must commit before returning success, with echo disabled for protected data in every mode. Alembic points at wrong versions directory, includes inline separator comment, lacks template/baseline and uses synchronous engine. `workflow.py` has query/body mismatch and stub success. No business code is repaired by this handoff.

## 2. Five-layer structure, reuse and owners

```text
Experience: frontend/app routes -> shared components -> lib/api typed Axios boundary
Copilot: services/workflow orchestrator + versioned skill catalog + durable stage runs
Skills: existing brief/copilot/ranking/shariah services, corrected use cases (no duplicate generator)
Context: authorized clients/holdings/interactions + confirmed memory + entitled graph + sources
Integration: adapters + repositories + PostgreSQL/Alembic + telemetry/audit
```

Keep existing directories. Add `backend/app/schemas/{common,brief,meeting,review,priority,product,pilot,admin}.py`, `core/{identity,authorization,policies,errors}.py`, `services/workflow/{orchestrator,registry}.py`, and typed adapter modules only as their consumers land. All metadata models live in `models/` and are imported by its entrypoint. Do not recreate reserved SQLAlchemy attribute `metadata`; map old legacy column via a different attribute if needed.

| Shared module | At least two consumers | First owner / dependency |
|---|---|---|
| DTO/OpenAPI + frontend contract generation + error parser | all APIs/pages | platform backend + frontend contract owners; before parallel features |
| Verified principal, scope and context revocation | every query, skill, worker and source viewer | backend security/platform owner; baseline |
| Artifact lineage/revision/items/review/hash | brief, transcript items, notes, message, recommendation, pilot packs | backend platform owner; before feature approvals |
| Source/availability/origin validation | briefs, rankings, products, memory, pilots | backend data/platform owner; before material claims |
| Policy catalog + flag/cohort/stage checks | capture/send/product/pilots/admin | platform owner; baseline, default fail closed |
| Transaction-local audit/idempotency + durable jobs/outbox | all mutations/stages/actions | backend platform owner; before writes |
| Context assembly/confirmed memory | briefs, extraction, outreach, ranking, pilots | copilot/context owner; Q1 foundation, not a later add-on |
| Registry/stage runner | every workflow/skill | copilot owner; after platform persistence; no second orchestrator |
| CanonicalBriefView / ReviewableArtifact / SourceDetail | all brief entrypoints and reviews | frontend shared-component owner; first brief batch |
| MessageComposer / ApprovalPreview / DeliveryStatus | outreach, follow-up, CRM, task, memory, ticket | frontend shared-component owner; before domain variants |
| AsyncRegion, accessible dialog/table/chart alternatives | all views | frontend foundation owner; baseline |
| Telemetry/metric definitions | every workflow and oversight | platform/analytics owner; emitted alongside each feature, never after release |

Feature planner assigns named developers to these ownership roles; no unassigned shared module may be independently reinvented. UI state reset on tenant/book/client change aborts prior fetches and rejects late responses by scope/context revision. No sensitive local storage, service-worker caching or optimistic action-success state.

## 3. Identity, policy and source contracts

### 3.1 Identity and entitlement

`Principal = {subject:string, tenant_id:string, display_name:string, permissions:string[], books:BookRef[], entitlement_revision:string, session_expires_at:Timestamp, environment:Environment, device_state:APPROVED|UNCONFIGURED|DENIED}`. Tenant/book identifiers are opaque institutional strings, not assumed UUIDs. Client identifiers are UUID in inspected models; **do not convert existing PKs or regenerate IDs**. Before any real migration inspect actual `information_schema`/PK/FK types and values; if non-UUID differs from model evidence, stop for reviewed compatibility mapping, never cast destructively. SQL preflight fails on wrong PK type.

Institutional OIDC authorization-code flow with PKCE, server-side code exchange, state/nonce/issuer/audience/signature/expiry validation, HttpOnly Secure SameSite cookies and CSRF token for mutations. Login provider metadata is explicit config; absent issuer/entitlement provider means `UNCONFIGURED`, not anonymous principal. `/auth/login?return_to=` accepts only allowlisted relative app paths; `/auth/callback` validates state; `/auth/logout` ends local session and clears protected UI without claiming to cancel a sent action. Entitlement provider unreachable or revision not verifiable fails closed for protected context/action. Every protected request and worker dispatch reloads current entitlement revision; no stale authorization cache may grant access after revocation.

`AUTH_MODE=fixture` requires `APP_ENV=local|test`, isolated fixture database, synthetic tenant/book/identity/catalogs and network-deny outbound adapters. Startup rejects fixture mode in production and rejects mixing fixture artifacts with live adapters. No caller-supplied approver, tenant header or `rm_id` parameter grants authority. API resource IDs unauthorized or nonexistent return indistinguishable 404; unauthorized capability for otherwise entitled context returns 403.

### 3.2 Independent provenance dimensions (never one overloaded enum)

```text
Environment = {kind: FIXTURE|INSTITUTION_TEST|PRODUCTION, id:string}
Availability = AVAILABLE|STALE|UNAVAILABLE|CONFLICT
Origin = RECORDED|DERIVED|RM_ENTERED
Source = {
 id:UUID, environment:Environment, availability:Availability, origin:Origin,
 system_key:string|null, record_id:string|null, record_version:string|null,
 as_of:Timestamp|null, retrieved_at:Timestamp|null,
 authoritative_owner:string|null, freshness_policy_ref:ConfigRef|null,
 live_response:boolean, adapter_receipt_id:string|null,
 confidence:Decimal|null, evidence:EvidenceLocation|null, limitation_codes:string[]
}
EvidenceLocation = {kind:RECORD|TRANSCRIPT|DOCUMENT|RM_ENTRY,
 record_uri:string|null, segment_id:UUID|null, document_ref:string|null,
 page:PositiveInt|null, excerpt:string|null, entered_by:string|null}
```

`live_response=true` is server-issued only for a successfully authenticated/entitled non-fixture provider result with receipt, real source record/version and source time where provider supplies it; never infer from running service or fabricate timestamps. STALE and LIVE-response may coexist (a successful read returned old evidence). Derived material cites exact input source IDs/revisions and actual model/prompt or deterministic rule version; it is not a recorded fact. RM-entered data records actor/time and may have no external source. Unknown confidence stays null; low confidence, partial completeness and stale evidence are separate dimensions. A region additionally has `completeness: COMPLETE|PARTIAL|EMPTY` and `capability_state: READY|UNCONFIGURED|UNAVAILABLE|DISABLED`. A successful zero result is EMPTY; dependency failure is UNAVAILABLE, never false empty success. CONFLICT retains both entitled sources and blocks dependent suitability/ticket.

### 3.3 Scope-safe configuration and adapters

`Scope = {tenant_id:string, book_id:string|null, jurisdiction:string|null}`. Tenant never implicit/global. Canonical `scope_key` is server-generated canonical serialization of the three fields; unknown/mismatched scope denied. Explicit effective-config resolution: exact `book+jurisdiction` → same tenant/book with jurisdiction null → same tenant/jurisdiction with book null → tenant-wide; no cross-tenant fallback. Deny/disabled capability controls take precedence over enable. Unresolved ambiguity or missing required active approved config gives UNCONFIGURED.

`ConfigRef={id:UUID,revision:PositiveInt,hash:Hash}`; `CatalogRef={config_ref:ConfigRef,catalog_key:string}`. All dynamic values below are validated against current entitled, approved catalogs, not arbitrary strings/JSON keys. A reason is `{code:string,catalog_ref:CatalogRef,other_text:string|null}`; `other_text` required for catalog's Other code. Unknown required field ranges/precision/provider mandatory fields block final action but allow incomplete draft. Technical pagination limits are not invented business thresholds.

| DEC | Typed policy catalog (required fields; null = UNCONFIGURED) | Gate |
|---|---|---|
| 01 | platforms/languages/jurisdictions; methods/participant coverage; consent text ref; audio/transcript residency, retention/deletion/legal-hold rules; capture lease validity policy; permitted attachments | no capture/transmission or audio upload until approved; manual notes usable |
| 02 | provider capability/authoritative field catalogs; mappings/type rules; credential ref/scopes; write/readback/idempotency/rate-limit guarantees; reconciliation owner | no external write/send/handoff; no secret values in DTO/history |
| 03 | ranking objectives/signal/freshness/eligibility rules, reason codes, weights/control effects/pin conflict resolution; meaningful-touchpoint evidence definition | no guessed scores/weights/durations or active controls without approved rules |
| 04 | entitled product/metric/currency/universe; KYC freshness; suitability factors, hard/soft and override permissions; account/amount/mandatory-ticket rules | no Green on missing/expired profile; no unknown-policy assessment/handoff |
| 05 | SSB/rule-pack/jurisdiction/evidence, ratios/thresholds, nisab/hawl/convention/method/rounding/disclaimer/advisor authority | Shariah pilot OFF; no universal zakat rate or compliant label |
| 06 | entity/edge types, custodians/FX, node/attendee entitlements, extraction evidence/quality/tolerances/scenario methods | Family pilot OFF; unknown node/attendee entitlement excluded before AI |
| 07 | retention measure/window/matched method/baseline sample | no comparative/causal success claim |
| 08 | supported device/OS, session/cache/distribution/approval rules | responsive tests allowed; mobile release blocked |

Every adapter implements a specific typed capability, not a generic `execute(payload)`: `Identity.resolve/recheck`, `Calendar.list/read`, `Portfolio.snapshot`, `CRM.read/apply/readback`, `Task.create/readback`, `Message.send/readback`, `Ticket.prefill/readback` (no execute-trade method), `Transcription.start/stop/readSegments`, `Product.interpret/search/read`, `Suitability.evaluate`, `Shariah.screen/estimate/archive`, `Custodian.snapshot`, `Document.extract`. Input/output DTOs are those in §6; response adds `AdapterReceipt={id,provider_key,environment,request_hash,status:CONFIRMED|NOT_ACCEPTED|UNKNOWN,provider_ref?,retrieved_at,source_ids[]}`. Every catalog declares required fields, field types, length/decimal rules, rate limit, retry safety, readback capability, ownership/freshness and error mapping. Credentials referenced by secret handle only. Fixtures return same DTOs with FIXTURE origin/environment and synthetic receipts; contract tests simulate outage, rate limit, partial, conflict, duplicate and accepted-then-timeout. Production/provider acceptance remains separately gated.

## 4. Persistence, revision and action invariants

### 4.1 Preserve existing data and IDs

`REMEDIATION_03A_Additive_Schema.sql` uses app-generated UUIDs for new entities, opaque text tenants/books, JSONB for new typed payloads, UTC timestamps. It creates legacy `clients/holdings/interactions/briefs` only if all relevant missing baseline tables are absent, validates essential legacy PK/FKs/types, and adds nullable brief linkage columns without changing legacy IDs, String version, JSON sections or legacy approvals. Existing `audit_logs/client_memories` remain intact as legacy import sources. Do not treat legacy approval text as a valid current action authorization.

A separate `client_scope(tenant_id,client_id)` bridge references the existing UUID client; unique(client_id) requires one verified tenant owner per legacy record. No tenant mutation/default backfill of the existing client table. `books` and `client_assignments` cache authoritative assignments, not grant rights; query authorization verifies authoritative session revision as well. Bridge unassigned means inaccessible, not default tenant. Each new child carries tenant+client and composite FK to the corresponding workflow/meeting/artifact so same-tenant different-client references also fail. Household nodes can span clients only through explicit graph/entitlement relations, never by weakening workflow FKs.

### 4.2 Artifact lineage, current pointer and stable references

- `artifact_lineages.id` is stable `artifact_id`; different message drafts, workflows and meetings each have independent lineage and can each start at version 1. No `(client,kind,version)` uniqueness.
- `artifact_revisions.id` is immutable `revision_id`; unique `(tenant_id,artifact_id,version)`. `ArtifactRef={artifact_id,revision_id,version,hash}`; every source dependency/review/action references this exact ref, never `latest`.
- `artifact_lineages.current_revision_id` points to its current revision with a deferred same-lineage FK. Lock lineage, compare ETag, append revision/items/sources, invalidate affected authorizations, update pointer/context revision, audit and commit in one transaction. Revisions and review history never overwritten. Hash is SHA-256 of canonical JSON with sorted keys, decimals serialized as strings, UTC timestamps normalized and all content/source/version/recipient/destination/policy/assessment/attendee basis included; generated actor/time and review metadata excluded.
- `artifact_items` gives every brief section/extracted item/recommendation/pack checklist stable `item_key` within lineage and exact `item_hash` per revision. Reviews persist `REVIEW` decisions independent of action approvals. States `UNREVIEWED|NEEDS_REVIEW|APPROVED|REJECTED|BLOCKED` are computed from exact current item revision/hash and latest review; editing accepted item requires a fresh review.
- BRIEF uses existing `briefs.sections` as authoritative five-section content. New brief rows link artifact revision, workflow and optional meeting, retain `version` as canonical decimal string for legacy compatibility, and add positive integer `revision_no`. Generic revision payload for BRIEF stores `{brief_id}` only, not a competing section copy. Exact section hashes/source basis live in `artifact_items`; brief GET projects single `data.brief.sections`. Other artifacts store typed payload in `artifact_revisions.payload`.
- Regenerating/retrying section appends a new brief revision; unaffected section content/hashes remain unchanged, but **no approval is silently inherited**. New review explicitly references each current section hash; prior reviews remain visible as historical. This conservative rule is the sole contract, not UI-dependent behavior.

### 4.3 Review is not execution authorization

`review_decisions` records non-action reviews of brief sections, transcript items, notes, recommendations, messages, graph proposals and pilot packs. `scope=ITEM|ARTIFACT`, decision `APPROVED|REJECTED`; rejection/edit/correction uses configured structured reason. No review decision alone creates an outbox action or sends content. Sensitive suppression records impact set and blocks downstream revisions under approved retention/legal-hold policy; it is not audit deletion.

Explicit `action_previews` snapshot exact approved server-stored action bytes, destination, adapter/config versions, source refs and assessment. `action_authorizations` binds preview hash/ref, actor and exact action class `CRM_WRITE|TASK_WRITE|MEMORY_WRITE|CLIENT_SEND|TICKET_PREFILL`; approval request cannot edit content. Notes canonical acceptance/recommendation/pilot-pack review use non-action REVIEW, not a fake side-effect class. Shariah pack finalization archives only inside the app with readback; external archival adapter additionally requires specific authorized destination, never client send. Ticket is prefill/open only; no trading action exists.

Preview invalidated by any dependent revision/policy/mapping/recipient/product/account/amount/attendee/consent/entitlement/flag change. Mutation and authorization checks run transactionally; dispatch rechecks current entitlement and dependency revisions. Stale refs are blocked, not automatically rebased. `/actions` accepts **only authorization_id**. Caller cannot choose replacement provider/destination/payload/action class; unknown fields rejected.

### 4.4 Transaction/outbox/crash recovery

All internal writes (canonical notes/memory, reviews, states, audit, idempotency response) commit atomically before HTTP success. External dispatch uses outbox: approve immutable preview → explicit execute → in same transaction validate scope/version/approval/policy + insert unique intended action + audit + commit. Worker never invents a business intent. `POST /actions` is explicit execution even when UI labels a combined preview authorization/execute gesture; no generation/view/reauth automatically calls it.

States `PENDING -> SENDING -> SUCCEEDED|FAILED_SAFE|UNKNOWN|RECONCILE_REQUIRED`; `CANCELED_BEFORE_DISPATCH` only before any dispatch. `SUCCEEDED` requires confirmed provider receipt plus required readback; a 2xx local response is not proof. `FAILED_SAFE` requires authoritative NOT_ACCEPTED evidence. Lease configuration is technical operator config, not guessed institution business threshold; absent required lease config keeps worker unavailable.

Claim `PENDING` with `FOR UPDATE SKIP LOCKED`, store unique lease token, lease_until, increment attempt and append `outbox_attempts(mode=DISPATCH, status=STARTED)`; commit before network. Completion uses compare-and-swap lease token; stale worker cannot overwrite newer state. Renew lease while active; never hold DB transaction over network. Any expired SENDING lease/crash/timeout **always becomes UNKNOWN**, including crash before request might have left: safety beats assumed retry. Reconciler claims UNKNOWN/RECONCILE_REQUIRED with separate lease, appends READBACK attempt and queries provider using stable operation key/provider ref. No readback support or unresolved outcome -> RECONCILE_REQUIRED with named operator, no send-again CTA. Only confirmed NOT_ACCEPTED + idempotency guarantee + explicit same-intent retry authorization permits dispatch again. Same provider operation key always reused; new UI idempotency key cannot duplicate a unique authorization intent. Recording stop/revocation is a safety operation on existing capture session, not a new send/write business action; it must not await a new consent approval.

Idempotency response ledger `(tenant,actor,method,path,key)` with canonical request hash and stored status/result/ref; in-flight same key returns 409 REQUEST_IN_PROGRESS with status URL, same key different body 409 IDEMPOTENCY_CONFLICT; completed replay returns original HTTP/result. Unique authorization_id in outbox prevents duplicate effects under different keys. Ledger retention comes from approved retention policy; no default expiry permits duplicate approved actions.

## 5. HTTP/DTO common rules

Base `/api/v1` unless `/auth/*` or `/health/*`. All protected requests use session cookie + mutation CSRF. All POST/PATCH/PUT mutations require `Idempotency-Key` UUID. GET is read-only, no generation/refresh/poll-triggered effects. Each table row below inherits required authorization + tenant/client/book/context check and common errors, plus listed domain errors. Mutations append audit/telemetry where defined and commit before success. No raw provider body/secret/PII in logs or errors.

- Success `Envelope<T>={data:T,meta:{request_id:UUID,served_at:Timestamp,next_cursor:string|null}}`; `data` member names below are literal, not additional envelope. Error `{error:{code:string,message:string,fields:FieldError[],retryable:boolean,status_url:string|null},meta:{request_id,served_at,next_cursor:null}}`; `FieldError={path:string,code:string,message:string}`. Request and response Pydantic models `extra=forbid` and OpenAPI discriminated unions; runtime response validation enabled.
- **One validation status:** all syntactic/type/missing/invalid reference-format validation = **400 VALIDATION_ERROR** including normalized FastAPI validation. 422 only **POLICY_BLOCKED** for otherwise valid requests failing a known approved policy; never 422 VALIDATION_ERROR.
- Common errors: 401 UNAUTHENTICATED; 403 FORBIDDEN; 404 NOT_FOUND; 409 REQUEST_IN_PROGRESS/IDEMPOTENCY_CONFLICT/INVALID_TRANSITION/APPROVAL_INVALIDATED/CONTEXT_CHANGED/CONFIG_UNCONFIGURED/FEATURE_DISABLED/SOURCE_CONFLICT; 412 VERSION_MISMATCH; 422 POLICY_BLOCKED; 429 RATE_LIMITED with Retry-After; 503 DEPENDENCY_UNAVAILABLE/NOT_READY; 500 INTERNAL_ERROR with safe request ref. Unknown policy=409 CONFIG_UNCONFIGURED, provider outage=503, authorized empty result=200. Retryable does not mean safe to redispatch an action.
- Mutation of existing lineage/state/config requires `If-Match` latest ETag: `"<revision-id>:<hash>"` for immutable artifact ref; state objects use `"<id>:<row-version>"`. Missing required header=400, mismatch=412. Related dependency changes despite matching entity ETag=409 APPROVAL_INVALIDATED/CONTEXT_CHANGED. Path context must equal DTO/referenced parent or 400; no omitted server checks.
- IDs new entities UUID; external ref opaque strings, never convert into UUID or concatenate client identities. Timestamp RFC3339 UTC, Date ISO date, session timezone IANA. `Decimal` finite base-10 string (no floating NaN/Infinity); `Money={amount:Decimal,currency:string}` with ISO/provider-approved currency; all amounts/precision/rounding validated against catalog. `Hash` 64 lowercase hex. List pagination `limit=1..100` default 50 and opaque cursor bound to principal/scope/filter; never unauthorized total/count.
- Type notation below: property `?` may be omitted on request; response declares all properties including explicit null. `T|null` is nullable; `T[]` list. Named `*Ref` must resolve to permitted current records. `Object`/`any`/ellipsis payloads are not allowed; union `FieldValue` below is the only catalog-validated extensibility for actual approved provider fields.

```text
FieldValue = {type:TEXT,value:string}|{type:DECIMAL,value:Decimal}|{type:BOOLEAN,value:boolean}|
 {type:DATE,value:Date}|{type:TIMESTAMP,value:Timestamp}|{type:REFERENCE,value:string}|
 {type:CHOICE,value:string}|{type:CHOICE_LIST,value:string[]}|{type:NULL,value:null}
MappedValue = {field_key:string,value:FieldValue,catalog_ref:CatalogRef}
EvidenceRef = {source_id:UUID,source_version:string|null}
ItemRef = {artifact_ref:ArtifactRef,item_key:string,item_hash:Hash}
Review = {id:UUID,scope:ITEM|ARTIFACT,item_key:string|null,item_hash:Hash,
 decision:APPROVED|REJECTED,actor:string,at:Timestamp,reason:Reason|null}
Artifact<T> = {artifact_ref:ArtifactRef,kind:ArtifactKind,client_id:UUID,workflow_id:UUID,
 meeting_id:UUID|null,environment:Environment,payload:T,items:ReviewItem[],
 reviews:Review[],capability_state:CapabilityState,blockers:Blocker[],created_at:Timestamp}
ReviewItem = {key:string,hash:Hash,review_state:ReviewState,evidence_refs:EvidenceRef[]}
Blocker = {code:string,field:string|null,config_ref:ConfigRef|null,resolution:SAFE_RETRY|EDIT|REVIEW|ADMIN|CHECK_STATUS|NONE}
```

## 6. Complete domain contracts

HTTP mutation defaults: create/generate=201, existing-state update/review=200, durable job/external action accepted=202. Replays return original status/body. All list GETs return `{items:T[],next_cursor}` in data. Every mutation specifies request type; `{}` means empty object with unknown fields rejected, **not unspecified payload**. Drafts may contain explicit missing values; approval/finalization enforces required known catalog fields.

### 6.1 Session, clients, portfolio, My Day and calendar

| API | Method / path | Request | Response data | Permission / domain errors |
|---|---|---|---|---|
| AUTH-01 | GET `/auth/login` | `return_to:string` safe relative query | 302 to configured institutional issuer | no principal; CONFIG_UNCONFIGURED |
| AUTH-02 | GET `/auth/callback` | OIDC code/state/error query | 302 safe return, session cookie | validated OIDC; invalid callback 400, outage 503 |
| AUTH-03 | POST `/auth/logout` | `{}` | `{logged_out:true}` | session+CSRF; no action replay |
| API-001 | GET `/session` | none | `{principal:Principal,csrf_token:string,capabilities:Capability[],active_workflows:UUID[]}` | authenticated |
| API-002 | GET `/clients` | `book_id:string`, `q?:string`, pagination | `{items:ClientSummary[],next_cursor}` | client:read, assigned book |
| API-003 | GET `/clients/{c}` | none | `{client:ClientDetail}` | client:read |
| API-020 | GET `/clients/{c}/portfolio` | none | `{snapshot:Portfolio}` | portfolio:read |
| API-021 | GET `/dashboard/my-day` | `book_id,date:Date,timezone:string` | `{date,timezone,priorities:Region<PriorityEvaluation|null>,calendar:Region<CalendarEvent[]>,workflows:Workflow[],book_stats:Region<BookStats>,news:Region<NewsItem[]>}` | book:read, current assignments |
| API-022 | GET `/calendar/events` | `date,timezone`, pagination | `{items:CalendarEvent[],next_cursor,capability_state}` | calendar:read; 503 outage, 409 unconfigured |
| API-023 | POST `/calendar/events/{e}/resolutions` | `{event_version:string,client_id:UUID,confirmation:true}` | `{meeting:Meeting}` | calendar:resolve + client:read; canceled event 409, source identity conflict 409 |
| API-024 | GET `/meetings/{m}` | none | `{meeting:Meeting}` | meeting:read |

```text
Capability={key:string,state:READY|UNCONFIGURED|UNAVAILABLE|DISABLED,blockers:Blocker[]}
Region<T>={availability:Availability,completeness:COMPLETE|PARTIAL|EMPTY,
 capability_state:CapabilityState,as_of:Timestamp|null,value:T,sources:Source[],error_code:string|null}
ClientSummary={id:UUID,external_id:string|null,name:string,book_id:string,client_type:string|null,
 risk_label:string|null,source:Source}
ClientDetail={summary:ClientSummary,contacts:Contact[],accounts:Account[],
 profile:Profile|null,contact_policy:ContactPolicy,memory:MemoryEntry[]}
Contact={id:string,channel:EMAIL|SMS,destination:string,source:Source}
Account={id:string,client_id:UUID,currency:string,eligibility:ELIGIBLE|INELIGIBLE|UNKNOWN,source:Source}
Profile={id:string,version:string,risk_code:string|null,validity:CURRENT|EXPIRED|MISSING|CONFLICT,
 as_of:Timestamp|null,fields:MappedValue[],source:Source}
ContactPolicy={dnc:boolean|null,channels:{channel:EMAIL|SMS,consented:boolean|null}[],config_ref:ConfigRef|null}
Portfolio={id:string,client_id:UUID,as_of:Timestamp|null,base_currency:string|null,
 aum:Money|null,holdings:Holding[],allocation:Allocation[],performance:PerformancePoint[],sources:Source[]}
Holding={id:string,account_id:string|null,instrument_id:string,symbol:string|null,quantity:Decimal|null,
 market_value:Money|null,cost_basis:Money|null,asset_class:string|null,source:Source}
Allocation={asset_class:string,value:Money|null,weight:Decimal|null,evidence_refs:EvidenceRef[]}
PerformancePoint={date:Date,metric_key:string,value:Decimal|null,unit:string,evidence_refs:EvidenceRef[]}
BookStats={aum:Money|null,client_count:integer|null,definition_ref:ConfigRef|null,sources:Source[]}
NewsItem={id:string,title:string,summary:string|null,published_at:Timestamp|null,source:Source}
CalendarEvent={id:UUID,provider_event_id:string,provider_version:string,title:string,start:Timestamp,end:Timestamp,
 status:ACTIVE|CANCELED|INELIGIBLE,attendee_hints:string[],match_state:VERIFIED|AMBIGUOUS|UNMATCHED|CONFLICT,
 candidates:ClientSummary[],resolved_meeting_id:UUID|null,source:Source}
Meeting={id:UUID,client_id:UUID,calendar_event_id:UUID|null,event_version:string|null,
 resolution:VERIFIED|RM_CONFIRMED|CONFLICT,title:string|null,start:Timestamp|null,end:Timestamp|null,
 workflow_ids:UUID[],row_version:PositiveInt,source_refs:EvidenceRef[]}
```

Calendar resolutions never create/merge clients; candidates filtered before hints/results. Event changing/ambiguity invalidates dependent meeting suitability/handoff until explicit resolution. Independent manual meeting is created by API-007 with `meeting:{calendar_event_id:null,title?,start?,end?}` only for meeting workflows and entitled client; absent times stay null. Legacy `/clients POST` creating a client is outside scope and removed/disabled; no mass assignment or inferred Moderate/Private Wealth defaults.

### 6.2 Workflow and persistent skill catalog

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-007 | POST `/workflows` | `StartWorkflow` | `{workflow:Workflow}` | workflow:start; flags/policy errors |
| API-008 | GET `/workflows/{w}` | none | `{workflow:Workflow}` | workflow:read |
| API-025 | GET `/workflows` | `book_id,status?:WorkflowStatus`, pagination | `{items:Workflow[],next_cursor}` | workflow:read |
| API-009 | POST `/workflows/{w}/stages/{stage}/runs` | `{input_refs:ArtifactRef[],context_revision:PositiveInt}` | 202 `{run:StageRun}` | workflow:run; invalid transition/config/flag/context |
| API-026 | POST `/workflows/{w}/pause` | `{reason:string|null}` | `{workflow:Workflow}` | workflow:manage; ETag |
| API-027 | POST `/workflows/{w}/resume` | `{}` | `{workflow:Workflow}` | workflow:manage; reauthorize, never auto-run |
| API-028 | POST `/workflows/{w}/abandon` | `{confirmation:true,reason:string|null}` | `{workflow:Workflow,continuing_action_ids:UUID[]}` | workflow:manage; does not unsend/cancel dispatched actions |
| API-029 | GET `/workflows/{w}/runs/{r}` | none | `{run:StageRun}` | workflow:read |
| API-030 | GET `/skills` | none | `{items:SkillDescriptor[]}` | workflow:read; only visible allowed skills |

```text
WorkflowType=MEETING_PREP|MEETING_FOLLOWUP|OUTREACH|PRODUCT_SEARCH|SHARIAH_REVIEW|HOUSEHOLD_REVIEW
StartWorkflow={type:WorkflowType,client_id:UUID,meeting_id:UUID|null,
 meeting:{calendar_event_id:null,title:string|null,start:Timestamp|null,end:Timestamp|null}|null,
 entry:MY_DAY|CALENDAR|CLIENT|PRIORITY,resume_workflow_id:UUID|null,task_context:string|null}
WorkflowStatus=NOT_STARTED|RUNNING|NEEDS_REVIEW|PAUSED|BLOCKED|UNAVAILABLE|FAILED|ABANDONED|COMPLETED
Workflow={id:UUID,type:WorkflowType,client_id:UUID,meeting_id:UUID|null,status:WorkflowStatus,
 row_version:PositiveInt,context_revision:PositiveInt,entry:string,current_stage:string|null,
 stages:StageSummary[],action_ids:UUID[],last_confirmed_at:Timestamp,next_decision:string|null}
StageSummary={key:string,status:PENDING|RUNNING|NEEDS_REVIEW|APPROVED|BLOCKED|FAILED|SKIPPED|COMPLETED,
 run_id:UUID|null,skill_id:string,skill_version:string,artifact_refs:ArtifactRef[],blockers:Blocker[]}
StageRun={id:UUID,workflow_id:UUID,stage_key:string,status:StageSummary.status,
 input_refs:ArtifactRef[],output_refs:ArtifactRef[],context_revision:PositiveInt,
 skill_id:string,skill_version:string,started_at:Timestamp|null,completed_at:Timestamp|null,
 manual_intervention:boolean,error_code:string|null}
SkillDescriptor={id:string,version:string,input_kind:string[],output_kind:string[],
 required_permissions:string[],policy_keys:string[],flag_key:string|null,model_ref:string|null,
 prompt_ref:ConfigRef|null,deterministic_rule_ref:ConfigRef|null,timeout_policy_ref:ConfigRef|null}
```

Registry is persisted immutable skill_versions plus code handler allowlist (not arbitrary executable code from DB). Stage input refs resolve to exact typed artifacts defined below; no generic `input:{...}`. Domain generation endpoints call this **same orchestrator**, enqueue durable stage run and return resulting artifact or run; API-009 cannot bypass domain validations. Allowed chains: meeting prep `context.resolve -> brief.generate -> brief.review`; follow-up `meeting.capture OR notes.manual -> transcript.extract -> outcomes.review -> approved-actions`; outreach `priority.reason -> message.draft -> message.review -> approved-send`; product `product.interpret -> product.search -> suitability.assess -> recommendation.review`; pilot chains use same registry/context. Completion requires actual required reviews/actions or explicitly recorded safe skips/manual intervention, not an empty stage list. Stage-run worker persists lease/token and failures; expired model-call lease marks FAILED with preserved prior output, never counts completion, and requires explicit retry. No external action dispatch is hidden in a skill or automatic transition.

### 6.3 Canonical brief, regeneration, exact section review and feedback

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-004 | POST `/briefs` | `{workflow_id:UUID,meeting_id:UUID|null,previous_ref:ArtifactRef|null,section_keys:BriefSectionKey[]}` | 201 `{brief:Brief}` or 202 `{run:StageRun}` if queued | brief:generate; linked client implied, no contradictory caller ID |
| API-005 | GET `/briefs/{brief_id}` | none | `{brief:Brief}` | brief:read; no generation |
| API-031 | GET `/workflows/{w}/briefs` | pagination | `{items:BriefHeader[],next_cursor}` | brief:read |
| API-006 | POST `/briefs/{brief_id}/reviews` | `{artifact_ref:ArtifactRef,sections:{key:BriefSectionKey,hash:Hash,decision:APPROVED|REJECTED,reason:Reason|null}[]}` | `{brief:Brief,reviews:Review[]}` | brief:review; exact sections, ETag; invalidation 409 |
| API-032 | PATCH `/briefs/{brief_id}` | `{section_edits:{key:BriefSectionKey,narrative:string,agenda:AgendaItem[]|null}[],reason:Reason}` | 201 `{brief:Brief}` new row/revision | brief:edit; no holdings/source record edit |
| API-033 | POST `/feedback` | `{artifact_ref:ArtifactRef,item_key:string|null,type:HELPFUL|NOT_HELPFUL|UNSUPPORTED_FACT,reason:Reason,comment:string|null}` | `{feedback_id:UUID,recorded_at:Timestamp}` | artifact:read; no tuning/training |

```text
BriefSectionKey=portfolio_overview|material_changes|recent_interactions|market_news|proposed_agenda
BriefHeader={brief_id:UUID,artifact_ref:ArtifactRef,workflow_id:UUID,meeting_id:UUID|null,
 client_id:UUID,generated_at:Timestamp,generated_by:string,review_state:ReviewState}
Brief=BriefHeader & {version:PositiveInt,environment:Environment,source_cutoff:Timestamp|null,
 sections:{portfolio_overview:BriefSection,material_changes:BriefSection,recent_interactions:BriefSection,
 market_news:BriefSection,proposed_agenda:BriefSection},blockers:Blocker[]}
BriefSection={key:BriefSectionKey,item_hash:Hash,narrative:string|null,claims:BriefClaim[],
 agenda:AgendaItem[],availability:Availability,completeness:COMPLETE|PARTIAL|EMPTY,
 capability_state:CapabilityState,review_state:ReviewState,sources:Source[],limitations:string[]}
BriefClaim={id:string,text:string,origin:Origin,evidence_refs:EvidenceRef[],confidence:Decimal|null}
AgendaItem={id:string,text:string,origin:DERIVED|RM_ENTERED,evidence_refs:EvidenceRef[]}
```

The sole contract is **`response.data.brief.sections`**; meta wrapper is transport only. `Brief.sections` remains canonical JSON field, not flat competing generator output. Always exactly five keys, including unavailable sections; no invented placeholder facts. Missing material evidence blocks affected claim approval; successful no-news is EMPTY with completed search evidence, not failed feed. Regenerate explicit only, prior_ref for same lineage; unrelated new meeting gets independent lineage v1. Client route `/brief/[clientId]` resolves entitled existing brief or explicit generation prompt; `BriefModal` delegates to CanonicalBriefView, does not own independent state/API/enrichment. API returns real IDs/actor/time and ETags. Review/edits never approve downstream writes or auto-start recording.

### 6.4 Consent, capture, manual notes, transcript, extraction and withdrawal

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-034 | GET `/meetings/{m}/capture-policy` | none | `{policy:CapturePolicy|null,consent:Consent|null,capture:Capture|null,blockers:Blocker[]}` | meeting:read; missing policy displayed UNCONFIGURED |
| API-035 | POST `/meetings/{m}/consents` | `{policy_ref:ConfigRef,jurisdiction:string,platform:string,language:string,decision:ACCEPTED|DECLINED,method:string,participant_refs:string[],coverage_confirmation:true}` | `{consent:Consent}` | consent:record; policy catalog and coverage checked |
| API-036 | POST `/meetings/{m}/consents/{id}/withdraw` | `{reason:Reason|null}` | `{consent:Consent,capture:Capture|null,invalidated_refs:ArtifactRef[]}` | consent:withdraw; immediately deny new capture, server stop existing |
| API-037 | POST `/meetings/{m}/captures` | `{consent_id:UUID,policy_ref:ConfigRef}` | 202 `{capture:Capture}` | capture:start; accepted current consent/coverage/provider/device |
| API-038 | POST `/captures/{id}/controls` | `{command:PAUSE|RESUME|STOP}` | `{capture:Capture}` | capture:control; same session, ETag; resume checks current policy |
| API-039 | GET `/captures/{id}` | none | `{capture:Capture}` | capture:read |
| API-040 | GET `/meetings/{m}/transcripts` | pagination | `{items:Artifact<Transcript>[],next_cursor}` | transcript:read |
| API-041 | PATCH `/artifacts/{a}/transcript` | `{corrections:{segment_id:UUID,text:string,reason:Reason}[],suppress_segment_ids:UUID[],impact_confirmation:boolean}` | 201 `{artifact:Artifact<Transcript>,invalidated_refs:ArtifactRef[]}` | transcript:edit; suppression permission/legal hold applied |
| API-042 | POST `/workflows/{w}/manual-notes` | `{text:string,previous_ref:ArtifactRef|null}` | 201 `{artifact:Artifact<Notes>}` | notes:draft; nonblank save; no CRM effect |
| API-043 | POST `/workflows/{w}/extractions` | `{basis_ref:ArtifactRef}` | 201 `{artifact:Artifact<Extraction>}` or 202 `{run:StageRun}` | extraction:generate; input transcript/manual notes only |
| API-044 | PATCH `/artifacts/{a}/extraction` | `{edits:ExtractionEdit[],suppressed_item_keys:string[],impact_confirmation:boolean}` | 201 `{artifact:Artifact<Extraction>,invalidated_refs:ArtifactRef[]}` | extraction:edit; reason required on corrections |

```text
CapturePolicy={ref:ConfigRef,jurisdictions:string[],platforms:string[],languages:string[],methods:string[],
 participant_coverage_key:string,consent_text:string,retention_disclosure:string,
 retention_policy_ref:ConfigRef,attachment_rules:AttachmentRule[]}
Consent={id:UUID,meeting_id:UUID,policy_ref:ConfigRef,state:ACCEPTED|DECLINED|WITHDRAWN,
 jurisdiction:string,platform:string,language:string,method:string,participant_refs:string[],
 actor:string,recorded_at:Timestamp,withdrawn_at:Timestamp|null,row_version:PositiveInt}
Capture={id:UUID,meeting_id:UUID,consent_id:UUID,status:STARTING|RECORDING|PAUSED|STOPPING|STOPPED|PROCESSING|PARTIAL|COMPLETE|FAILED,
 row_version:PositiveInt,last_confirmed_audio_ms:integer|null,last_confirmed_transcript_ms:integer|null,
 provider_ref:string|null,lease_valid_until:Timestamp|null,error_code:string|null}
Transcript={capture_id:UUID,status:PARTIAL|COMPLETE,segments:TranscriptSegment[],suppressed_segment_ids:UUID[]}
TranscriptSegment={id:UUID,speaker_ref:string|null,start_ms:integer,end_ms:integer,text:string,
 confidence:Decimal|null,origin:RECORDED|RM_ENTERED,evidence_ref:EvidenceRef,corrected_from:UUID|null}
Notes={text:string,origin:RM_ENTERED|DERIVED,basis_refs:ItemRef[],evidence_refs:EvidenceRef[]}
Extraction={basis_ref:ArtifactRef,items:ExtractionItem[]}
ExtractionItem={key:string,type:DECISION|ACTION|PREFERENCE|COMMITMENT|FOLLOWUP_TOPIC,content:string,
 owner:{ref:string|null,display:string,origin:RECORDED|RM_ENTERED}|null,due_date:Date|null,
 due_date_origin:RECORDED|RM_ENTERED|null,evidence_refs:EvidenceRef[],confidence:Decimal|null,
 origin:DERIVED|RM_ENTERED,review_state:ReviewState}
ExtractionEdit={key:string,content:string,owner:ExtractionItem.owner,due_date:Date|null,
 due_date_origin:RECORDED|RM_ENTERED|null,evidence_refs:EvidenceRef[],reason:Reason}
```

Consent and capture have durable independent state and audit; calendar RSVP is not consent. Server enforces short-lived capture permission via approved policy-bound lease and no upload/stream acceptance after decline/withdrawal/revocation/session loss. Client must stop microphone on lease/session/connection loss, and server stops provider stream; UI cannot be only safeguard. Withdrawal transaction revokes lease, records consent, marks dependent source use disallowed and invalidates previews/authorizations; stop provider delivery reconciles actual stop, response never falsely says stopped while STOPPING/unknown. Manual notes survive. No complete transcript without confirmed provider completion; no synthesized speaker/owner/date/confidence. Correction preserves original retained evidence version; suppression excludes affected material from future prompts/drafts without erasing audit or violating legal hold. Review API-010 accepts/rejects exact extraction item refs; only accepted permitted items may build downstream artifacts.

Attachment contract (capture/pilot docs, not unrestricted file storage): `POST /meetings/{m}/attachments` or `/workflows/{w}/attachments` request `{filename,mime_type,byte_size:PositiveInt,checksum:Hash,policy_ref:ConfigRef}` -> 201 `{upload_id:UUID,upload_url:string,expires_at:Timestamp}` only with approved type/size/region/retention policy. `POST /attachments/{id}/complete` `{checksum:Hash}` -> `{attachment:{id,status:UPLOADED|SCANNING|READY|REJECTED,source:Source,policy_ref}}`; virus/type/checksum authorization checks precede READY. No parsing before READY. URLs scoped/short-lived, no raw public bucket, fixtures local only. Unknown policy blocks upload, no invented size cap. Metadata persisted in attachments table; object content in approved storage adapter only.

### 6.5 Artifacts, post-meeting preview, messages, actions and memory

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-045 | GET `/artifacts/{a}` | `revision_id?:UUID` (default current) | `{artifact:Artifact<ArtifactPayload>}` | artifact:read; history read-only |
| API-046 | PATCH `/artifacts/{a}` | `{payload:EditablePayload,reason:Reason|null}` | 201 `{artifact:Artifact<ArtifactPayload>}` new revision | artifact:edit; same discriminant/kind only; ETag |
| API-010 | POST `/artifacts/{a}/reviews` | `{artifact_ref:ArtifactRef,scope:ARTIFACT|ITEM,items:{key:string,hash:Hash,decision:APPROVED|REJECTED,reason:Reason|null}[],decision:APPROVED|REJECTED|null}` | `{artifact_ref,reviews:Review[],review_state:ReviewState}` | artifact:review; item/whole consistent, no action |
| API-047 | POST `/workflows/{w}/outcome-drafts` | `{accepted_item_refs:ItemRef[],kinds:(NOTES|CRM_CHANGE|TASK|MEMORY_PROPOSAL|MESSAGE|TICKET_PREFILL)[]}` | `{artifacts:Artifact<ArtifactPayload>[]}` or 202 `{run}` | outcome:generate; only accepted basis, missing mappings block affected draft |
| API-048 | POST `/action-previews` | `{artifact_ref:ArtifactRef,action_class:ActionClass}` | `{preview:ActionPreview}` | class-specific permission; material missing/unknown policy blocked |
| API-049 | POST `/action-previews/{p}/authorizations` | `{preview_hash:Hash,confirmation:true}` | `{authorization:ActionAuthorization}` | class-specific approve permission; cannot edit payload |
| API-011 | POST `/actions` | **`{authorization_id:UUID}` only** | 202 `{action:Action}` | class-specific execute permission; stale/invalid authorization 409 |
| API-012 | GET `/actions/{id}` | none | `{action:Action}` | action:read; no dispatch |
| API-050 | POST `/actions/{id}/reconcile` | `{}` | 202 `{action:Action}` | action:reconcile; readback only, never resend |
| API-051 | POST `/actions/{id}/retry` | `{confirmation:true}` | 202 `{action:Action}` | action:retry; FAILED_SAFE+current approval+guaranteed idempotency only |
| API-013 | GET `/clients/{c}/memory` | pagination | `{context_revision:PositiveInt,items:MemoryEntry[],next_cursor}` | memory:read; confirmed/conflict status explicit |
| API-014 | POST `/clients/{c}/memory/proposals` | `{workflow_id:UUID,previous_entry_id:UUID|null,entry:MemoryProposal}` | 201 `{artifact:Artifact<MemoryProposal>}` | memory:propose; never direct canonical write |
| API-052 | POST `/workflows/{w}/messages` | `MessageGenerate` | 201 `{artifact:Artifact<Message>}` or 202 `{run}` | message:draft; same orchestrator and composer |

```text
ActionClass=CRM_WRITE|TASK_WRITE|MEMORY_WRITE|CLIENT_SEND|TICKET_PREFILL
CRMChange={mapping_ref:ConfigRef,record_ref:string,record_version:string,
 changes:{target_field:string,old_value:FieldValue,new_value:FieldValue,evidence_refs:EvidenceRef[]}[]}
Task={title:string,owner_ref:string|null,due_date:Date|null,mapping_ref:ConfigRef|null,
 provider_fields:MappedValue[],basis_refs:ItemRef[]}
MemoryProposal={key:string,value:FieldValue,origin:DERIVED|RM_ENTERED,evidence_refs:EvidenceRef[],
 basis_refs:ItemRef[],confidence:Decimal|null,previous_version:PositiveInt|null}
MemoryEntry={id:UUID,key:string,value:FieldValue,version:PositiveInt,
 state:CONFIRMED|CONFLICT|SUPERSEDED,source_ref:ArtifactRef,confirmed_by:string,confirmed_at:Timestamp,sources:Source[]}
MessageGenerate={mode:FOLLOWUP|OUTREACH,channel:EMAIL|SMS,template_ref:ConfigRef,
 accepted_item_refs:ItemRef[],priority_reason_ref:PriorityReasonRef|null}
Message={mode:FOLLOWUP|OUTREACH,channel:EMAIL|SMS,template_ref:ConfigRef,
 recipients:{contact_id:string,destination:string,confirmed:boolean}[],subject:string|null,body:string,
 disclosures:{ref:ConfigRef,text:string}[],basis_refs:ItemRef[],priority_reason_ref:PriorityReasonRef|null,
 claims:{text:string,evidence_refs:EvidenceRef[],origin:Origin}[]}
TicketPrefill={product_ref:ProductRef|null,account_ref:string|null,amount:Money|null,
 assessment_ref:ArtifactRef|null,meeting_evidence_refs:ItemRef[],provider_fields:MappedValue[]}
ActionPreview={id:UUID,artifact_ref:ArtifactRef,class:ActionClass,hash:Hash,
 environment:Environment,provider_key:string,destination_ref:string,
 request:CRMChange|Task|MemoryProposal|Message|TicketPrefill,
 policy_refs:ConfigRef[],dependency_refs:ArtifactRef[],context_revision:PositiveInt,
 exclusions:string[],created_at:Timestamp,blockers:Blocker[]}
ActionAuthorization={id:UUID,preview_id:UUID,preview_hash:Hash,class:ActionClass,
 actor:string,authorized_at:Timestamp,state:VALID|INVALIDATED|REVOKED}
Action={id:UUID,authorization_id:UUID,class:ActionClass,status:ActionStatus,
 provider_ref:string|null,provider_state:ACCEPTED|SCHEDULED|DELIVERED|WRITTEN|PREFILLED|NOT_ACCEPTED|UNKNOWN|null,
 created_at:Timestamp,submitted_at:Timestamp|null,confirmed_at:Timestamp|null,readback_at:Timestamp|null,
 error_code:string|null,can_reconcile:boolean,can_retry:boolean,attempts:AttemptSummary[]}
AttemptSummary={id:UUID,number:PositiveInt,mode:DISPATCH|READBACK,status:STARTED|CONFIRMED|NOT_ACCEPTED|UNKNOWN,
 started_at:Timestamp,ended_at:Timestamp|null,error_code:string|null,receipt_ref:string|null}
```

`ArtifactPayload` is closed union of the named payload types in §6 (including BRIEF pointer, transcript, extraction, notes, CRM, task, memory, message, ticket, product/pilot). `EditablePayload` is the subset NOTES/CRM_CHANGE/TASK/MEMORY_PROPOSAL/MESSAGE/TICKET_PREFILL plus dedicated typed endpoints for extraction/brief/pilot proposals; caller cannot patch system-derived assessment/screen/forecast results or review metadata. Kind mismatch 400. Whole payload replacement creates immutable revision; no arbitrary JSON path edit.

CRM preview displays authoritative old values/version; version conflict re-reads and requires new review, no last-write-wins. TASK owner/due_date null unless sourced or explicitly RM-entered; mandatory catalog fields block execute. MEMORY_WRITE transaction writes confirmed entry version + audit/context revision; failures never appear confirmed, repeated same authorization no duplicate. Notes review saves canonical accepted note in artifact state but does not silently write CRM. FOLLOWUP messages only accepted decisions/actions; OUTREACH includes entitled approved priority reason, available facts/opener, omission of unsupported facts. Drafts blank/missing recipients/subject allowed for editing; send blocks until exact confirmed destinations/body/template/disclosure/current DNC/channel/consent and approved limits validate. No scheduling feature, CC/BCC extension or alternate consent bypass. Fixture preview cannot target live adapter. TICKET_PREFILL requires explicit meeting discussion and exact current suitability/client/product/account/amount/currency/provider mandatory fields; no speculative trade schema, submit, execution or claim `Trade placed`.

### 6.6 Book-wide priorities, reasons, controls and outcomes

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-015 | POST `/books/{b}/priority-evaluations` | `{date:Date,timezone:string,trigger:RM_REFRESH|MATERIAL_SIGNAL}` | 201 `{evaluation:PriorityEvaluation}` or 202 `{run_id:UUID,status_url:string}` | priority:evaluate on assigned book; trigger material system principal allowlisted |
| API-016 | GET `/books/{b}/priority-evaluations/latest` | `date:Date,timezone:string` | `{evaluation:PriorityEvaluation|null,capability_state}` | priority:read; null only no prior evaluation, no fabricated empty evaluation |
| API-053 | GET `/books/{b}/priority-evaluations/{e}` | none | `{evaluation:PriorityEvaluation}` | priority:read; re-filter revoked rows before serialization |
| API-054 | POST `/books/{b}/priority-controls` | `PriorityControlRequest` | `{control:PriorityControl,evaluation_state:STALE|CURRENT}` | priority:control; DEC-03 required; ETag per client control state |
| API-055 | POST `/books/{b}/contact-outcomes` | `{recommendation_ref:PriorityReasonRef,client_id:UUID,outcome:CONTACTED|MEETING_BOOKED|NO_RESPONSE|NOT_RELEVANT,occurred_at:Timestamp,note:string|null,meeting_id:UUID|null,evidence_refs:EvidenceRef[]}` | `{outcome_id:UUID,meaningful_touchpoint:CONFIRMED|NOT_CONFIRMED|UNCONFIGURED}` | outcome:record; time not future; cannot infer two-way/attendance |

```text
PriorityReasonRef={evaluation_id:UUID,client_id:UUID,reason_key:string,reason_hash:Hash}
PriorityEvaluation={id:UUID,book_id:string,date:Date,timezone:string,evaluated_at:Timestamp,
 policy_ref:ConfigRef,status:CURRENT|STALE|FAILED,criteria_summary:string,
 items:PriorityItem[],environment:Environment,source_refs:EvidenceRef[]}
PriorityItem={client:ClientSummary,rank:PositiveInt,reasons:PriorityReason[],rank_change_explanation:string|null,
 controls:PriorityControl[],last_updated_at:Timestamp}
PriorityReason={key:string,hash:Hash,classes:(RISK|OPPORTUNITY|RETENTION)[],code:string,
 explanation:string,signals:{key:string,value:FieldValue,source:Source}[],evidence_refs:EvidenceRef[]}
PriorityControlRequest={client_id:UUID,recommendation_ref:PriorityReasonRef,
 control:{type:SNOOZE,until:Timestamp}|{type:DISMISS,reason:Reason}|{type:PIN,pinned:boolean}}
PriorityControl={id:UUID,client_id:UUID,book_id:string,request:PriorityControlRequest.control,
 actor:string,recorded_at:Timestamp,row_version:PositiveInt,policy_ref:ConfigRef}
```

Persist evaluation and reason hash; unique client/rank per evaluation, cap 10. Material refresh runs as explicit scheduled/system intent under approved DEC-03, not on viewing GET; start-of-day uses RM IANA timezone, DST aware. Strict design default excludes DNC/out-of-book/unentitled/noneligible; pin never overrides eligibility/cap or discloses excluded clients. Snooze future, configured dismiss reason, pin effects from published policy only; no invented durations/weight values from current `ranking_service` defaults. Exception is not 200 empty list; prior list remains stale + error. Outcomes append, never rewrite canonical client preference. Meaningful contact counted only with approved definition and confirmed two-way/attendance evidence; send status alone excluded. Current DNC/consent always rechecked for open draft/action.

### 6.7 Product interpretation, search, comparison, selection, suitability, override

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-056 | POST `/workflows/{w}/product-interpretations` | `{query:string}` | 201 `{artifact:Artifact<ProductInterpretation>}` or 202 `{run}` | product:search, Tier B config; no inferred profile mutation |
| API-057 | PATCH `/artifacts/{a}/product-filters` | `{filters:ProductFilter[],sort_key:string|null,confirmation:true}` | 201 `{artifact:Artifact<ProductInterpretation>}` | product:search; hard filters immutable |
| API-058 | POST `/workflows/{w}/product-searches` | `{interpretation_ref:ArtifactRef,confirmation:true}` | 201 `{artifact:Artifact<ProductSearch>}` or 202 `{run}` | product:search; current entitled universe only |
| API-059 | POST `/workflows/{w}/product-comparisons` | `{search_ref:ArtifactRef,product_refs:ProductRef[]}` | 201 `{artifact:Artifact<ProductComparison>}` | product:read; selected returned entitled candidates only |
| API-060 | POST `/workflows/{w}/candidate-selections` | `{search_ref:ArtifactRef,product_ref:ProductRef,confirmation:true}` | `{selection_id:UUID,selected_at:Timestamp}` | product:select; telemetry M-08, no trade intent |
| API-061 | POST `/workflows/{w}/assessments` | `{product_ref:ProductRef,account_ref:string|null,amount:Money|null,previous_ref:ArtifactRef|null}` | 201 `{artifact:Artifact<Assessment>}` or 202 `{run}` | suitability:assess; conflicting identity blocks |
| API-062 | POST `/assessments/{a}/overrides` | `{assessment_ref:ArtifactRef,factor_keys:string[],reason:Reason,rationale:string,confirmation:true}` | 201 `{override:SuitabilityOverride}` | suitability:override; hard/unknown/missing profile blocked |

```text
ProductRef={id:string,version:string}
ProductFilter={key:string,operator:EQ|IN|GTE|LTE,value:FieldValue,
 metric_key:string|null,unit:string|null,source:QUERY|RM_EDIT|AUTHORITATIVE,
 hard:boolean,confirmed:boolean,catalog_ref:CatalogRef}
ProductInterpretation={query:string,filters:ProductFilter[],sort_key:string|null,
 universe_ref:ConfigRef,profile_ref:string|null,ambiguities:string[]}
ProductMetric={key:string,name:string,value:FieldValue|null,unit:string|null,definition_ref:ConfigRef,source:Source}
Product={ref:ProductRef,name:string,asset_class:string,currencies:string[],risk_code:string|null,
 minimum_investment:Money|null,fees:ProductMetric[],liquidity:ProductMetric[],metrics:ProductMetric[],
 esg:ProductMetric[],terms_source:Source,availability:Availability}
ProductSearch={interpretation_ref:ArtifactRef,executed_filters:ProductFilter[],executed_at:Timestamp,
 products:Product[],next_cursor:string|null,no_result_explanation:string|null,soft_edit_suggestions:string[],sources:Source[]}
ProductComparison={search_ref:ArtifactRef,products:Product[],metric_keys:string[]}
Assessment={client_id:UUID,product_ref:ProductRef,account_ref:string|null,amount:Money|null,
 profile_id:string|null,profile_version:string|null,profile_validity:CURRENT|EXPIRED|MISSING|CONFLICT,
 input_hash:Hash,policy_ref:ConfigRef,rating:GREEN|YELLOW|RED|UNAVAILABLE,current:boolean,
 factors:SuitabilityFactor[],ticket_eligible:boolean,blockers:Blocker[],assessed_at:Timestamp}
SuitabilityFactor={key:string,label:string,classification:HARD|SOFT|UNKNOWN,
 result:PASS|WARN|FAIL|MISSING,evidence_refs:EvidenceRef[],explanation:string,override_permitted:boolean}
SuitabilityOverride={id:UUID,assessment_ref:ArtifactRef,factor_keys:string[],reason:Reason,rationale:string,
 policy_ref:ConfigRef,actor:string,at:Timestamp,original_rating:GREEN|YELLOW|RED}
```

Filters are exactly displayed confirmed typed filters; ambiguity blocks search until correction; never silently relax hard restrictions. Currency, amount, risk, yield/return metric, liquidity, fees/minimums and ESG use approved catalog keys/units; no invented product-count cap. Search change invalidates results and dependent selection/assessment/preview. Currentness/entitlement and Shariah sensitivity enforced by construction across all recommendation surfaces. Missing/expired profile cannot yield GREEN and blocks ticket; known policy may yield Yellow, unknown policy yields UNAVAILABLE not invented classification. Green means no detected conflict, not compliance approval. Recommendation review API-010 is separate from override and ticket. Hard stop never override; soft override only exact current factor/authority/policy with rationale; does not cure missing KYC/account. Original rating immutable; every material change requires new assessment.

### 6.8 Runtime administration, approve versus activate, flags and readiness

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-018 | GET `/admin/configurations` | permitted Scope/pagination | `{items:Configuration[],next_cursor}` | config:read |
| API-063 | POST `/admin/configurations/{key}/drafts` | `{scope:Scope,base_ref:ConfigRef|null,value:ConfigurationValue,change_reason:string}` | 201 `{configuration:Configuration}` | config:edit; typed same key |
| API-064 | POST `/admin/configurations/{id}/validate` | `{}` | `{ref:ConfigRef,valid:boolean,errors:FieldError[],impacts:string[],diff:ConfigDiff[]}` | config:edit; validation no external credential call |
| API-065 | POST `/admin/configurations/{id}/approvals` | `{ref:ConfigRef,evidence_refs:UUID[],confirmation:true}` | `{configuration:Configuration}` | config:approve + jurisdiction/assigned governance; cannot activate |
| API-066 | POST `/admin/configurations/{id}/activations` | `{ref:ConfigRef,confirmation:true,reason:string}` | `{activation_id:UUID,active_ref:ConfigRef,readback_at:Timestamp}` | config:activate; approved/evaluated/audit ready, current gates |
| API-019 | GET `/admin/capability-controls` | permitted Scope | `{items:CapabilityControl[]}` | release:read |
| API-067 | POST `/admin/capability-controls/{key}/changes` | `{scope:Scope,enabled:boolean,cohort_refs:string[],evidence_refs:UUID[],reason:string,confirmation:true}` | `{control:CapabilityControl,affected_workflow_ids:UUID[],continuing_action_ids:UUID[]}` | release:operate; pilot current approvals required, ETag |
| API-068 | GET `/admin/readiness` | permitted Scope/environment | `{capabilities:Capability[],gates:GateEvidence[]}` | readiness:read |

```text
Configuration={ref:ConfigRef,key:string,scope:Scope,class:FIELD_MAPPING|RANKING|TEMPLATE|CONSENT|INTEGRATION,
 state:UNCONFIGURED|DRAFT|VALIDATED|APPROVED|RETIRED,value:ConfigurationValue,
 author:string,approver:string|null,approved_at:Timestamp|null,active:boolean,blockers:Blocker[]}
ConfigurationValue = FieldMappingConfig|RankingConfig|TemplateConfig|ConsentConfig|IntegrationConfig
FieldMappingConfig={connector_catalog:CatalogRef,mappings:{source_entity:string,source_field:string,
 target_entity:string,target_field:string,value_type:FieldValue.type,required:boolean}[]}
RankingConfig={objective_ref:ConfigRef,reasons:CatalogRef,signals:CatalogRef,
 numeric_parameters:MappedValue[],control_policy_ref:ConfigRef,eligibility_ref:ConfigRef,meaningful_touch_ref:ConfigRef|null}
TemplateConfig={name:string,channel:EMAIL|SMS,jurisdiction:string,text:string,
 allowed_tokens:string[],mandatory_disclosure_refs:ConfigRef[],evaluation_evidence_refs:UUID[]}
ConsentConfig={jurisdiction:string,platforms:string[],languages:string[],methods:string[],
 participant_coverage_ref:ConfigRef,consent_text_ref:ConfigRef,retention_ref:ConfigRef,
 legal_approval_evidence_refs:UUID[],security_approval_evidence_refs:UUID[]}
IntegrationConfig={capability:string,provider_key:string,environment:Environment,
 catalog_ref:CatalogRef,scopes:string[],owner:string,freshness_policy_ref:ConfigRef,
 limits_ref:ConfigRef,secret_ref:string|null,readback_mode:SUPPORTED|UNSUPPORTED,
 idempotency_mode:PROVIDER_KEY|AUTHORITATIVE_LOOKUP|UNSUPPORTED,reconciliation_owner:string}
ConfigDiff={field:string,old_value:FieldValue|null,new_value:FieldValue|null,secret_changed:boolean}
CapabilityControl={key:string,scope:Scope,enabled:boolean,cohort_refs:string[],revision:PositiveInt,
 actor:string,at:Timestamp,reason:string,evidence_refs:UUID[]}
GateEvidence={id:UUID,key:string,owner:string,scope:Scope,environment:Environment,reference:string,
 version:string,status:PENDING|APPROVED|EXPIRED|BLOCKED,approved_by:string|null,
 recorded_at:Timestamp,expires_at:Timestamp|null,blockers:Blocker[]}
```

No free-form institutional parameters: numeric_parameters keys and rules resolve to approved catalog; unresolved decisions DRAFT/UNCONFIGURED, activation blocked. Secret replacement separate `PUT /admin/configurations/{id}/secret` `{operation:REPLACE|REVOKE,secret_value:string|null,confirmation:true}` restricted secret:manage; value never returned/logged, blank REPLACE means unchanged, REVOKE explicit and pending operations reviewed; version history stores handle/change indicator only. Actual secret management adapter must be approved, fixture in tests. No live provider validation authorized by this task.

Author, approving governance role and activation capability are independently checked; required approver/evidence from approved policy, never self-certified by mere config edit. Config approval immutable, activation records separate current pointer. Restore previous approved ref is a **new activation** after current gate checks, no deleted history. Tenant scope part of every config/flag unique key, approval and FK. Pilot keys `pilot.shariah`, `pilot.family` have no row = disabled; stage controls use `stage.<registered-key>`, model-feature keys allowlisted. Tenant/book/jurisdiction disabled ancestor wins. Pilot enable requires explicit permitted cohort and valid legal/SSB/security/data evidence, never RM-owned toggle. Disable stops new stage/dispatch, retains safe history/manual core, does not claim unsent/undone provider effects.

### 6.9 Evidence, audit, telemetry, measurements and health

| API | Method/path | Request | Response data | Permission/errors |
|---|---|---|---|---|
| API-069 | GET `/sources/{s}` | none | `{source:Source,dependent_refs:ArtifactRef[]}` | source:read + original resource/node entitlement; no hidden counts |
| API-070 | GET `/audit-events` | `from,to:Timestamp,workflow_id?:UUID,client_id?:UUID,event_family?:string,status?:string`, pagination | `{items:AuditEvent[],next_cursor}` | audit:read scoped; RM own permitted workflows only |
| API-071 | GET `/audit-events/{id}` | none | `{event:AuditEvent}` | audit:read recheck lineage |
| API-072 | GET `/metrics` | `from,to,book_id,metric_ids:string[]` | `{items:MetricResult[]}` | metrics:read; fixture segregated |
| API-073 | GET `/guardrails` | permitted Scope/from/to | `{items:GuardrailResult[]}` | oversight:read |
| API-074 | POST `/telemetry/events` | `{event_id:UUID,name:BRIEF_VIEWED|PRIORITY_LIST_VIEWED|REASON_OPENED|RESULTS_VIEWED|ACTIVE_INTERVAL,workflow_id:UUID|null,artifact_ref:ArtifactRef|null,book_id:string,started_at:Timestamp|null,ended_at:Timestamp|null}` | `{event_id,recorded_at}` | telemetry:record; server actor/scope/time validation; cannot submit sent/approved/completed event |
| API-017 | GET `/health/live`, `/health/ready` | none | `{status:UP|NOT_READY,checks:{database:boolean,schema:boolean,identity_config:boolean},environment:Environment}` | public safe summary; ready failure 503, live 200 process only |

```text
AuditEvent={id:UUID,actor:string,action:string,resource_type:string,resource_id:string,
 workflow_id:UUID|null,artifact_ref:ArtifactRef|null,correlation_id:UUID,occurred_at:Timestamp,
 source_refs:EvidenceRef[],configuration_refs:ConfigRef[],outcome:string|null,previous_hash:Hash|null,event_hash:Hash}
MetricResult={id:M-01|M-02|M-03|M-04|M-05|M-06|M-07|M-08|M-09|M-10,definition_ref:ConfigRef|null,
 window:{from:Timestamp,to:Timestamp},environment:Environment,state:MEASURED|NOT_MEASURED|UNCONFIGURED,
 value:Decimal|null,unit:string,numerator:Decimal|null,denominator:Decimal|null,sample_size:integer|null,
 baseline_state:AVAILABLE|REQUIRED|NOT_APPLICABLE,baseline_value:Decimal|null,
 validation_target:string|null,inclusions:string[],exclusions:string[],updated_at:Timestamp|null,limitations:string[]}
GuardrailResult={id:string,baseline_state:string,observed_value:Decimal|null,numerator:Decimal|null,
 denominator:Decimal|null,threshold_ref:ConfigRef|null,status:PENDING|OK|ALERT|UNCONFIGURED,evidence_refs:UUID[]}
```

Only server-confirmed lifecycle emits consent/review/approve/send/write/complete events. Telemetry persists environment/correlation/actor-safe ID plus source/model/prompt/template/skill/rule versions, timestamps/duration/counts, never transcript/audio/full prompts/secret/hidden nodes/private chain-of-thought. Append-only audit permissions and hash chain per tenant (serialized chain-head update), external immutable export/checkpoint only when approved; hashes alone are not SOC2 certification. Metric definitions: M-01 active comparable prep intervals/time-motion baseline; M-02 meeting end→approved follow-up minus client-wait intervals; M-03 verified two-way/attended evidence, no drafts/failed sends; M-04 distinct active enabled brief RMs / active enabled entitled RMs plus briefs/eligible meeting; M-05 completed copilot prep/outreach / all eligible completed prep/outreach; M-06 cross-skill completions without manual stitch / eligible multi-stage completions; M-07 approved matched/book-adjusted retention method only; M-08 query→selected candidate with baseline; M-09 current-evidence Shariah holdings / eligible sensitive holdings; M-10 family effort baseline first. Unknown denominator/baseline -> null NOT_MEASURED, no zero/success/causality fiction. Fixture never contributes live numerator/denominator.

### 6.10 Shariah pilot ON contracts (same artifacts/context; default OFF)

All require `pilot.shariah` enabled for exact cohort, current approved synthetic fixture or institutional DEC-05 pack and client/node entitlement. OFF ->409 FEATURE_DISABLED. Production decisions not resolved by fixture values. Each endpoint persists typed artifact revision and skill run; review uses API-010; no external send/write as a side effect.

| API | Method/path | Request | Response data / permission |
|---|---|---|---|
| API-075 | POST `/workflows/{w}/shariah-preferences` | `{value:string,policy_ref:ConfigRef,evidence_refs:EvidenceRef[],confirmation:true}` | `{artifact:Artifact<MemoryProposal>}`; memory:propose; separate MEMORY_WRITE authorization to canonical |
| API-076 | POST `/workflows/{w}/shariah-screens` | `{instrument_refs:ProductRef[],rule_pack_ref:ConfigRef,previous_screen_ref:ArtifactRef|null}` | `{artifact:Artifact<ShariahScreen>}` /202 run; shariah:screen |
| API-077 | POST `/workflows/{w}/shariah-estimates` | `ShariahEstimateInput` | `{artifact:Artifact<ShariahEstimate>}` /202; shariah:estimate |
| API-078 | POST `/workflows/{w}/shariah-packs` | `{holding_refs:string[],screen_refs:ArtifactRef[],estimate_ref:ArtifactRef|null,ssb_evidence_refs:EvidenceRef[]}` | `{artifact:Artifact<ShariahPack>}`; shariah:pack |
| API-079 | POST `/artifacts/{a}/advisor-confirmations` | `{artifact_ref:ArtifactRef,advisor_ref:string,confirmation_evidence:EvidenceRef,confirmed_on:Date}` | `{confirmation_id:UUID}`; shariah:advisor-record + authoritative advisor evidence; RM tick not sufficient |
| API-080 | POST `/artifacts/{a}/finalizations` | `{artifact_ref:ArtifactRef,review_ids:UUID[],confirmation:true}` | `{artifact_ref,archive_ref:string,archived_at:Timestamp,status:FINALIZED}` only durable archive readback | shariah:finalize; incomplete/stale evidence 422, unavailable archive 503 |

```text
ShariahScreen={rule_pack_ref:ConfigRef,ssb_ref:EvidenceRef,instruments:{product_ref:ProductRef,
 result:PASS|FAIL|INSUFFICIENT_EVIDENCE,criteria:{key:string,result:PASS|FAIL|INSUFFICIENT_EVIDENCE,
 observed:FieldValue|null,threshold:FieldValue|null,evidence_refs:EvidenceRef[]}[],
 as_of:Timestamp|null,drift_from:ArtifactRef|null,required_action_codes:string[]}[]}
ShariahEstimateInput={method_ref:ConfigRef,assets:{holding_ref:string,value:Money,
 classification:ZAKATABLE|EXCLUDED,classification_evidence:EvidenceRef,valuation_evidence:EvidenceRef}[],
 nisab:{value:Money,evidence_ref:EvidenceRef,date:Date},hawl_start:Date|null,hawl_anniversary:Date|null,
 convention:LUNAR|SOLAR,purification:{product_ref:ProductRef,ratio:Decimal,evidence_ref:EvidenceRef,as_of:Date}[]}
ShariahEstimate={input:ShariahEstimateInput,items:{holding_ref:string,included:boolean,
 basis:string,estimated_zakat:Money|null,purification:Money|null}[],total_by_currency:Money[],
 assumptions:string[],caveat:string,advisor_confirmation_id:UUID|null}
ShariahPack={holding_refs:string[],screen_refs:ArtifactRef[],estimate_ref:ArtifactRef|null,
 ssb_evidence_refs:EvidenceRef[],checklist:{key:string,current:boolean,evidence_refs:EvidenceRef[]}[],
 completeness:COMPLETE|INCOMPLETE,archive_ref:string|null,caveat:string}
```

Unknown source/SSB/method/nisab/hawl/ratio -> insufficient evidence/unavailable, no default rate/total. Noncompliant instruments cannot surface as compliant recommendations anywhere. Existing failing holdings readable as risk evidence only. Preference accepted into same memory and context, never inferred from protected demographics. Drift/hawl reminders are **proposed** priority/task basis; no automatic trade/calendar/send. Every estimate states discussion-only, advisor confirmation required, never fatwa. Pack finalization is internal review/archive, not send or advice approval.

### 6.11 Family pilot ON contracts

All require `pilot.family`, cohort, DEC-06 coverage/tolerance/entitlement and source permissions. Authorize household and every node/source before graph queries/prompts and again per attendee **before** generating pack; unauthorized nodes/edges/counts/totals not returned, logged or passed to AI. Revocation bumps context revision and invalidates pending previews/packs immediately; historical content only if still entitled.

| API | Method/path | Request | Response data / permission |
|---|---|---|---|
| API-081 | GET `/households/{h}/graph` | none | `{household_id,version:PositiveInt,nodes:GraphNode[],edges:GraphEdge[]}`; household:read+per-node entitlement |
| API-082 | POST `/workflows/{w}/structure-extractions` | `{household_id:UUID,attachment_id:UUID,policy_ref:ConfigRef}` | `{artifact:Artifact<StructureProposal>}` /202; household:extract |
| API-083 | PATCH `/artifacts/{a}/structure` | `{nodes:GraphNodeProposal[],edges:GraphEdgeProposal[],reason:Reason}` | new `{artifact:Artifact<StructureProposal>}`; household:edit, current refs |
| API-084 | POST `/artifacts/{a}/structure-confirmations` | `{artifact_ref:ArtifactRef,accepted_item_refs:ItemRef[],rejected_item_refs:ItemRef[],confirmation:true}` | `{graph_version:PositiveInt,confirmed_node_ids:UUID[],confirmed_edge_ids:UUID[]}`; household:confirm, source/quality/policy valid; atomic canonical internal write+review+audit |
| API-085 | POST `/workflows/{w}/consolidations` | `{household_id:UUID,graph_version:PositiveInt,base_currency:string,custodian_snapshot_refs:EvidenceRef[],fx_refs:EvidenceRef[],tolerance_ref:ConfigRef}` | `{artifact:Artifact<Consolidation>}` /202; household:consolidate |
| API-086 | POST `/workflows/{w}/attendee-packs` | `{household_id:UUID,attendee_refs:string[],meeting_id:UUID,basis_refs:ArtifactRef[]}` | `{artifacts:Artifact<AttendeePack>[]}` /202; household:pack; unknown attendee entitlement blocks before AI |
| API-087 | POST `/workflows/{w}/family-scenarios` | `{household_id:UUID,type_code:string,jurisdiction:string,method_ref:ConfigRef,assumptions:ScenarioAssumption[],confirmation:true}` | `{artifact:Artifact<FamilyScenario>}` /202; household:scenario |
| API-088 | POST `/workflows/{w}/capital-notice-extractions` | `{household_id:UUID,commitment_ref:string,attachment_id:UUID}` | `{artifact:Artifact<CapitalNotice>}` /202; household:notice |
| API-089 | POST `/artifacts/{a}/notice-verifications` | `{artifact_ref:ArtifactRef,verified:CapitalNotice,confirmation:true}` | `{artifact:Artifact<CapitalNotice>,verified_at:Timestamp}`; household:notice-verify; immutable revision+review, not money transfer |
| API-090 | POST `/workflows/{w}/liquidity-forecasts` | `{household_id:UUID,as_of:Date,verified_notice_refs:ArtifactRef[],commitment_refs:string[],history_refs:EvidenceRef[],model_ref:ConfigRef}` | `{artifact:Artifact<LiquidityForecast>}` /202; household:forecast |
| API-091 | POST `/artifacts/{a}/forecast-actuals` | `{forecast_ref:ArtifactRef,notice_ref:ArtifactRef,actual_amount:Money,actual_date:Date,evidence_refs:EvidenceRef[]}` | `{actual_id:UUID,comparison:ForecastComparison}`; household:actual-record; current verified source |

```text
GraphNode={id:UUID,type_code:string,name:string,client_id:UUID|null,source_refs:EvidenceRef[],version:PositiveInt}
GraphEdge={id:UUID,from_node:UUID,to_node:UUID,type_code:string,evidence_refs:EvidenceRef[],version:PositiveInt}
GraphNodeProposal={item_key:string,existing_id:UUID|null,type_code:string,name:string,
 client_id:UUID|null,evidence_refs:EvidenceRef[],confidence:Decimal|null}
GraphEdgeProposal={item_key:string,existing_id:UUID|null,from_item_key:string,to_item_key:string,
 type_code:string,evidence_refs:EvidenceRef[],confidence:Decimal|null}
StructureProposal={household_id:UUID,attachment_id:UUID,nodes:GraphNodeProposal[],edges:GraphEdgeProposal[]}
Consolidation={household_id:UUID,graph_version:PositiveInt,base_currency:string,holdings:Holding[],
 lookthrough:Allocation[],reconciliation:{custodian_ref:string,expected:Money|null,observed:Money|null,
 difference:Money|null,tolerance_ref:ConfigRef,state:RECONCILED|UNRESOLVED|UNAVAILABLE}[],
 total:Money|null,source_refs:EvidenceRef[],fx_refs:EvidenceRef[],completeness:COMPLETE|PARTIAL}
AttendeePack={household_id:UUID,meeting_id:UUID,attendee_refs:string[],entitlement_revision:string,
 allowed_node_ids:UUID[],basis_refs:ArtifactRef[],narrative:string,commitments:ExtractionItem[],
 scope_hash:Hash,caveat:string}
ScenarioAssumption={key:string,value:FieldValue,origin:RECORDED|RM_ENTERED|DERIVED,
 evidence_refs:EvidenceRef[],illustrative:boolean,reviewed:true}
FamilyScenario={household_id:UUID,type_code:string,jurisdiction:string,method_ref:ConfigRef,
 assumptions:ScenarioAssumption[],outputs:MappedValue[],caveats:string[],illustrative:true}
CapitalNotice={household_id:UUID,commitment_ref:string,attachment_id:UUID,fund_ref:string|null,
 amount:Money|null,due_date:Date|null,recipient_account_ref:string|null,evidence_refs:EvidenceRef[],verified:boolean}
LiquidityForecast={household_id:UUID,as_of:Date,window_days:90,model_ref:ConfigRef,
 verified_notice_refs:ArtifactRef[],commitments:{ref:string,unfunded:Money,source:Source}[],
 windows:{from:Date,to:Date,forecast_amount:Money|null,evidence_refs:EvidenceRef[]}[],
 assumptions:string[],source_refs:EvidenceRef[],comparisons:ForecastComparison[],caveat:string}
ForecastComparison={notice_ref:ArtifactRef,forecast_amount:Money|null,actual_amount:Money|null,
 forecast_date:Date|null,actual_date:Date|null,error_amount:Money|null,state:OBSERVED|NOT_YET_OBSERVED}
```

No unknown graph type or weak extraction auto-canonical; accepted edges require both accepted/permitted endpoints. Graph confirmation is specific explicit human canonical-write approval, not authorization to CRM/memory/send; any memory propagation separately uses MEMORY_WRITE. Consolidation excludes unconfirmed/unauthorized nodes; absent FX/tolerance/feed yields partial/unresolved, no false total. Per-attendee entitlement classes receive separate immutable pack versions; attendee changes invalidate preview/review. Pack approval never sends. Notice verification cannot assert missing amount/date/fund/account; mandatory governed fields required. Only verified notices enter 90-day forecast; insufficient history yields unavailable forecast values, actual absent NOT_YET_OBSERVED not zero error. Liquidity/retention reasons use shared approved ranking policy and minimized evidence; no capital-call payment/marketplace/full planning.

## 7. Additive migration and baseline repair plan (executable handoff, no live operation)

1. **Read-only inventory before any migration:** actual database identity/environment, PostgreSQL version, schema-only dump, all table/column types/defaults/PK/FK/index/extension/row counts, Alembic table/current heads, sampled checksum manifest. Do not print secrets or client rows. Inspect `clients.id` actual UUID; no conversion based on model alone. SQL companion baseline checks are necessary but not a full fingerprint. Production approval requires verified backup+restored clone, named operator, write freeze/checkpoint/rollback owner and approved RPO/RTO; none are asserted here.
2. **Boot baseline:** remove stale `MarketTick` persistence imports in market/init/seed; move enum contracts to shared schemas, update `WorkflowStage/SourceKind` consumers, disable falsely LIVE mock behavior; retain extraction capability when deleting duplicate flat brief generator. No provider clients initialized at import with missing keys; dependency-injected unavailable adapters. Resolve config path relative to file, explicit environment profile, disable SQL echo; remove placeholder success routes. `get_db` yields session only, transaction belongs to use case; no success before commit. Register honest health/readiness once.
3. **Alembic baseline:** choose async engine+asyncpg/run_sync; fix `version_path_separator = os` on its own line and `version_locations = %(here)s/alembic/versions`, restore `script.py.mako`; metadata import includes all persistence models. Readiness checks expected revision and required schema, never boot-time `create_all` or seed. Seeds explicit fixture environment only.
4. **Revision graph decision:** inventory whether `001_add_briefs_audit`/`002_add_client_memories` were applied anywhere, not just current audited DB. Do not edit/reparent published applied history. Implement pre-001 baseline revision/adoption only if all relevant environments prove these revisions unpublished; then `000_baseline -> 001 -> 002 -> 003_contracts`. If any applied, preserve old IDs/history and use a reviewed bootstrap/adoption command on verified clone to provision missing baseline before old 001, then additive revision after 002. Document exact selected graph in migration batch before merge; no planner may assume history rewrite safe. Adoption of already-existing equivalent schema requires a signed inventory report and explicit operator-approved baseline record, never automatic `stamp head` from table presence.
5. **Executable schema companion:** legacy table creation occurs only when absent with consistency preflight; existing values/types are not overwritten. New tables and nullable `briefs` linkage columns are additive, fail on unexpected collisions. No `DROP`, `TRUNCATE`, reset, automatic ownership backfill, destructive cast or `IF NOT EXISTS` masking new schema drift. `client_scope` populated only by authorized source mapping; unmapped records inaccessible. New canonical rows written after bridge/auth ready. Legacy briefs/memory/audit history retained and imported with explicit legacy/unverified lineage; old approver strings do not authorize actions. No type conversion of legacy String `Brief.version`; canonical integer revision_no new column. Unknown prior timestamp timezone remains explicit unknown until verified, not blindly assigned UTC.
6. **Independent real-DB tests:** (a) completely empty disposable PostgreSQL 15 DB: actual full Alembic upgrade head, assert revision/table/columns/PK/FKs/index and no-op second upgrade; (b) model-legacy JSON/naive-time schema populated synthetic data; (c) re-audit-style JSONB/timestamptz preexisting data and no alembic_version; (d) known applied 001/002 fixture if history discovered; (e) incompatible PK/drift abort without mutation. Verify retained IDs/counts/checksums and restore checkpoint. Offline SQL with expected CREATE plus exit 0 insufficient. SQL companion itself is not the Alembic revision or proof tests passed.
7. **Frontend baseline:** `npm ci`, `tsc --noEmit`, Next production build; remove hardcoded client/approver/brief ID/AUM/fallback fabricated data, correct one envelope in typed client, consolidate BriefModal/page. Disabled features direct-route gated. Type errors fixed by correct typed data, not suppressions. Add error boundaries/partial/loading/a11y states matching design, no redesign.

## 8. Exact tiers and full traceability

**Counting and labels are distinct:** the PRD natively labels 15 FRs P0: FR-01…FR-15. Inventory §12.2 is an audit-tier grouping, not a rewrite of those PRD priority labels: its Tier A literal FR set is FR-01…15, FR-20, FR-22 (17 IDs); Tier B literal FR set is FR-16…19. FR-20/22 are inferred V1-wide cross-cutting controls in Tier A, not extra PRD-declared P0 FRs. The approved core scope contains 22 FRs, not 22 P0. FR-21 remains in the full 22-FR core scope and is inferred cross-cutting in inventory §2.4, but is omitted from both §12.2 literal FR lists; preserve its functional requirement without silently assigning it to a §12.2 tier. Its mobile release is gated by NFR-08/DEC-08. Shared auth/review controls apply to every view. Do not inflate declared P0 blockers or invent mobile policy/thresholds.

| Tier (inventory §12.2 literal grouping) | IDs | Acceptance |
|---|---|---|
| A audit grouping | FR-01…15, FR-20, FR-22; D0/1/2/4/5; B-01…07/B-10; NFR-01…07/NFR-09…11; GOV-01…05/07/08; INT-01…06/10/11; M-01…06; TEL-01…06/08/10; GRD-01/02/03/05/08/09/10; GATE-01/02/X; C-01…16 | Preserve inventory §12.2 grouping. Its 17 FR IDs are an audit tier, not 17 PRD-declared P0 labels; 15 declared P0 workflow delivery order 1.1→1.2→1.3→2.1→2.2. Ticket current-data guardrail still blocks prefill if Tier-B suitability unavailable, without making full product discovery P0. |
| B audit grouping / P1 GA Epics 1–3 | FR-16…19; D3; B-08/09; NFR-08; GOV-06; INT-07; M-07/08; TEL-07; GRD-04; GATE-03/04 | Preserve inventory §12.2 grouping; required for core GA, cannot delay declared-P0 delivery. FR-21 is not added to this literal FR set; its mobile release is separately gated by NFR-08/DEC-08. No legal sign-off inferred. |
| FR-21 cross-cutting core requirement (not assigned in §12.2 literal list) | FR-21 | Included in the 22-FR core scope; shared UI/session/device requirement applies, and mobile release waits for DEC-08/NFR-08 support/acceptance. No invented policy or thresholds. |
| C pilot default OFF | FR-4.1…4.3, FR-5.1…5.3; B-11/12; INT-08/09; M-09/10; TEL-09; GRD-06/07; C-17/18 | Separate cohort, ON-fixture and governance/rollback gates; no core-GA blocker. FR-5.3 P2; 5.1/5.2 P1 inferred. |
| D excluded as feature gaps | OOS/non-goals/open decisions/risks/objectives/RICE/personas/Q4 expanded autonomy | Never auto-send/trade/advice/fatwa/train/full plan/portal/marketplace. Human-approved action remains mandatory. |

### 8.1 All 28 FR: persistence, API and hard tests

| FR | Contract / persistence | Required reproducible verification |
|---|---|---|
| 01 | API-022/023/007/004; meeting/workflow/brief sections | resolved entitled event/client -> explicit generation -> real persisted ID/version |
| 02 | Source dimensions, API-005/069, five brief sections/items | each material claim source query/receipt/as-of/Recorded-vs-Derived; no fabricated LIVE |
| 03 | API-004/032/033; new lineage revisions/reviews | partial failed source leaves other sections; retry version+feedback, no CRM duplication |
| 04 | API-034…039; consent/capture/lease | decline/withdraw/session loss stops both client capture and server transmission; audit/no audio analytics |
| 05 | API-040…044/010; transcript/extraction revision/items | evidence speaker/time linked, owner/date null unless supplied; corrected/suppressed impact invalidates |
| 06 | Capture/manual-note recovery | provider loss retains confirmed position/manual edits, restart no duplicate meeting; never fake complete |
| 07 | API-045…049; typed review surfaces | individual accept/edit/reject; exact old/new basis and no hidden action |
| 08 | CRM/task preview/action/outbox/attempts | correct client authoritative readback, idempotency concurrency, accepted-timeout reconciliation |
| 09 | Message FOLLOWUP accepted-item basis | rejecting/withdrawing source removes later drafts; recipient/disclosure/version exact, draft not sent |
| 10 | TicketPrefill + current Assessment + action class | missing account/suitability/mandatory fields blocks; prefill only, no execute-trade API |
| 11 | book evaluation API-015/016/053 | <=10 distinct authorized non-DNC clients, local day/DST/start/material refresh, empty distinct outage |
| 12 | PriorityReason refs/source lineage | inspect signals and rank changes; protected-attribute fields rejected |
| 13 | API-054/055; controls/outcomes | persisted snooze/dismiss/pin published rules, no client-intent inference, contact evidence not send count |
| 14 | OUTREACH MessageGenerate | reason + available facts/opener, editable grounded draft, no unsupported filler |
| 15 | send preview/auth/action | DNC/channel/disclosure/entitlement before dispatch; no auto-send, scheduled vs sent truthful |
| 16 | product interpretation/filter/search refs | displayed confirmed filters exactly searched; hard filter cannot relax |
| 17 | sourced ProductMetric/comparison | current entitled products, no-result rationale, missing yield null, source/as-of preserved |
| 18 | Assessment immutable input/policy hash | Green only current profile; missing/expired Yellow at best and no ticket; failure UNAVAILABLE |
| 19 | exact factor override | hard stop denied, soft allowed actor+policy+rationale, original rating unchanged |
| 20 | all lineage/items/review/authorization | every artifact/section review persisted, approval invalidation across all dependency edits |
| 21 | shared UI + session/device policy | mobile lookup/brief/priorities/outreach at 320px/200% zoom; same denial/approval/cache rules, release DEC-08 |
| 22 | five typed configs validate/approve/activate | independent permissions, version/diff/readback/tamper-evident audit and no secret echo |
| 4.1 | preference MEMORY_WRITE/screens/shared filters | propagation across brief/search/outreach, no compliant unreviewed/stale label, drift risk evidence |
| 4.2 | itemized estimate/advisor evidence | method/nisab/hawl/convention/ratios from approved synthetic ON fixture, caveat, null missing input |
| 4.3 | Shariah pack/finalization/archive | incomplete/stale checklist blocked, complete version archived/readback, not client-send/fatwa |
| 5.1 | graph proposals/confirmation/consolidation | node/edge pre-prompt deny and revocation, confirmed-only graph, tolerance/FX reconciliation |
| 5.2 | attendee pack/scenario/commitment artifacts | unknown attendee blocked before generation; separate entitled versions; assumptions illustrative |
| 5.3 | notice verification/90-day forecast/actual | unverified notice excluded, sourced risk reason, actual missing not zero error; no payment |

### 8.2 Cross-cutting test bindings (no replacement of inventory criteria)

| IDs | Architecture and gate evidence |
|---|---|
| D0, INT-10, GRD-01/02 | verified identity/revocation, tenant bridge/composite FKs, deny tests before context/worker; security/privacy externally approved |
| D1, INT-01/02/04/05, B-02 | typed identity/portfolio/CRM/calendar adapters, source conflict and explicit event resolution |
| D2, B-03, GRD-03 | accepted current participant consent and fail-closed capture lease, withdrawal audit/invalidation |
| D3, B-08/09, INT-07, GRD-04 | catalog/current KYC hard stops, no Green or handoff on stale/missing/conflict |
| D4, M-01…10, TEL-01…10 | durable event definitions, source/model/version/correlation tags, denominators/baselines, fixture separation |
| D5, C-01…05/15 | persistent memory/shared context/graph, Q1 orchestrator, versioned registry and restart-safe stage chain |
| B-01/04/10, GOV-03/07 | separate availability/completeness/confidence, faithful evidence and manual fallback, per-stage kill switch |
| B-05, NFR-11 | outbox/attempt/lease/readback, no blind resend, verified backup restore and accepted-effect recovery |
| B-06/07, GOV-08, GRD-10 | truthful eligible Top10, DNC, no protected ranking inputs, meaningful evidence not automated volume |
| B-11/12, INT-08/09, GRD-06/07, C-17/18 | pilot-only SSB evidence and node/attendee entitlement hard gates, no core inflation |
| NFR-01/02/03 | p95 brief <10s/product search <5s in normal dependency conditions, separate dependency latency; load 1000 concurrent; uptime objective 99.5% monthly measured not local proof |
| NFR-04/05, GOV-02/06, C-13 | institutional encryption/residency/subprocessors/zero-retention/training/consent/suitability approval evidence, no code-only certification |
| NFR-06/07/10, GOV-01/03, C-08/09 | append-only source/version/review/action audit and PII-minimized correlated telemetry, no chain-of-thought |
| NFR-08/09 | DEC-08 supported mobile tasks plus WCAG 2.1 AA keyboard/dialog/focus/color/text/chart alternatives |
| GOV-04/05, C-10 | structured feedback/override, evaluated model/prompt/template/rule versions, rollback not auto-training |
| INT-11 | every displayed source has real owner/freshness config/version/as-of or explicit unknown, provider rate limits handled |
| GRD-05/08/09 | no unapproved sends, measured correction/rejection rates with denominators, unsupported-fact feedback path |
| GATE-01/02/X, C-06/07/11/12/14/16 | E1 foundations, two-persona value/trust/training/support, measurable closed loop/skill chain/manual stitch, no fabricated historic gate completion |
| GATE-03/04 | Tier B legal/entitlement tests separately from Tier C pilots; no expanded autonomous effects without new PRD |

## 9. Verification and deliverable acceptance gates

1. Pinned baseline import `app.main` and every registered router without provider credentials/network; enumerate exact OpenAPI paths/methods and validate all input/output DTOs and common error envelope. One canonical brief path and no fake success stubs. Ready returns 503 for unavailable DB/wrong head/schema and accurately distinguishes optional unavailable provider.
2. Real empty PostgreSQL Alembic upgrade and independent existing-schema adoption tests in §7; assert PK/FKs including **same-tenant different-client** cross-reference denials, artifact current-pointer/lineage uniqueness, config scope isolation, outbox attempt/lease uniqueness, and original data preservation. Restart app/worker and prove read-after-write of brief/section review/memory/workflow/action. No offline exit-only acceptance.
3. Frontend `tsc --noEmit`, build, typed API contract fixtures and negative schemas; same canonical component in route/panel/mobile. Explicit generate→persist→render→edit→section-review→new version→invalidation test. Opening/viewing/reload/GET never calls generation/execution.
4. Auth tests unauthenticated, wrong tenant/book, missing role, unknown or revoked entitlement, late old-client fetch, household node/attendee leakage **before prompt construction**, fixture principal rejected in production, no fixture→live action even with authorized RM.
5. Full review/action integration: accepted transcript/manual items→typed notes/CRM/task/memory/message/ticket drafts→separate review→server-stored preview→authorization→explicit action→confirmed readback. Arbitrary caller payload/provider/destination substitution rejected. Wrong class/stale/hash/consent/config/assessment invalidation denies. Concurrent double-click/different keys cannot duplicate same authorization.
6. Fault tests crash before/after network, lease expiry SENDING→UNKNOWN, stale worker completion denied, provider accepted-timeout reconcile without resend, no-readback operator queue, FAILED_SAFE explicit retry same operation key; confirmed sends never duplicated. Internal DB failure rolls back canonical write/audit/idempotency atomically.
7. Closed-loop test confirmed outcome/memory→next book evaluation reason→later brief via same context/registry, persistent skill/model/policy/source versions and telemetry. Missing memory persistence never counts completed. Manual intervention excluded from automated cross-skill numerator.
8. Pilot OFF direct-route/API deny, no row defaults false; **ON isolated synthetic tests** cover screening PASS/FAIL/insufficient, unknown zakat inputs, complete/incomplete archive, graph accepted/rejected, node revocation, attendee pack separation, reconciliation tolerance cases and verified-notice 90-day actual comparison. Synthetic thresholds exist only in named test fixture config, never shipped as institutional policy.
9. UI a11y/loading/empty/stale/conflict/offline/unknown-action/manual fallback, no secret/PII log leaks, no fake confidence/facts/LIVE. Performance/load/uptime/restore/security/legal/provider acceptance measured separately; all baseline/denominator/validation targets clearly distinguish engineering readiness from production certification.

## 10. Freeze and lead disposition

Frozen for planner after lead acceptance: exact routes, DTO fields/closed unions/error statuses, three provenance dimensions, artifact/section lineage and review refs, no-substitution action preview/authorization/execute contract, book-wide ranking controls/outcomes, durable stage/catalog/memory, policy/flag tenant scopes, outbox crash/reconciliation, SQL persistence and migration safety/test gates. The old revision-1 client-scoped priorities, arbitrary action payload/provider and side-effect-only review schema are withdrawn, not optional alternatives.

No remaining product-design conflict: brief review is separate from action authorization; no provider must be chosen by architecture; no ownership mapping guessed. External inputs DEC-01…08, SSO/provider contracts, actual schema inventory/applied-history and authoritative tenant ownership remain typed safe gates and operational prerequisites, not permission to invent values. Feature planner can independently split foundation/domain/UI/provider-fixture/pilot tests using this file and SQL companion; development begins only after lead review. Any change updates this file and SQL as needed, versioned with explicit notice to all affected implementers. No commit requested or made.

**Validation record for this revision:** content/SQL static consistency checks and actual-schema-runtime test results must be reported separately in handoff. No real provider/live database remediation has been executed.

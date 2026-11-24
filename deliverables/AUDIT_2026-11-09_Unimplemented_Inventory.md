# RM Workbench — Unimplemented / Half-Done Code Inventory

**Audit date:** 2026-11-09
**Scope:** `backend/app/**` (88 app files, 90 routes, 57 ORM tables, 4 migrations, 229 tests) + `frontend/app/**`
**Baseline documents:** `deliverables/03_PRD_Comprehensive_2026.md` (v3.0, 8 Nov 2026), `deliverables/family-office-integration-plan.md`
**Method:** AST static analysis + grep + file reads + runtime import/route verification against live `openapi.json` (85 routes)

## Summary

| Severity | Count | Meaning |
|---|---|---|
| CRITICAL | 14 | Broken/absent functionality — endpoint errors out or returns fabricated data |
| HIGH | 21 | Stub returning hardcoded/synthetic data |
| MEDIUM | 17 | Partially implemented, key branches missing |
| LOW | 12 | Cosmetic / TODO comment only |
| **Total** | **64** | |

Live route inventory confirms the double-prefix convention (`/api/v1/calendar/calendar/events`, `/api/v1/artifacts/artifacts/{id}`, `/api/v1/telemetry/telemetry/events`, `/api/v1/meetings/meetings/{id}`). Frontend `lib/endpoints.ts` matches these paths — **do not "fix" the prefixes without changing both sides together.**

---

## CRITICAL (14)

| ID | File (relative to `backend/`) | Lines | Problem | Required fix |
|---|---|---|---|---|
| C-1 | `app/api/v1/endpoints/calendar.py` | 63-72 | `POST .../resolutions` always raises 503; TODO only | Verify `event_id` + `event_version` (optimistic lock), create `Meeting` with resolution VERIFIED/RM_CONFIRMED, update `calendar_events.match_state`, return created meeting |
| C-2 | `app/api/v1/endpoints/artifacts.py` | 93-102 | `PATCH /artifacts/{id}` always raises 501 | Load `ArtifactLineage`, create new `ArtifactRevision` (version+1, real content_hash), update `current_revision_id`, invalidate dependent `ArtifactDependency` rows |
| C-3 | `app/api/v1/endpoints/calendar.py` | 25-35 | `GET /calendar/events` always `[]` + UNCONFIGURED | Query `calendar_events` filtered by tenant/actor; derive capability_state from config, not a constant |
| C-4 | `app/api/v1/endpoints/briefs.py` | 66-75 | `GET /briefs` always `{"data": []}`; DB session unused | Query briefs by `client_id` / `workflow_id`, return real list |
| C-5 | `app/api/v1/endpoints/priorities.py` | 38-69 | `GET /evaluations` empty + `snooze`/`dismiss`/`pin` have **no side effects** | Wire the four convenience endpoints to the real `ControlService` and book-level evaluation query; persist controls |
| C-6 | `app/api/v1/endpoints/products.py` | 88-90 | `POST /{wf}/interpretations` uses `client_id = uuid4()` | Resolve real client_id from workflow, enforce tenant/authorization |
| C-7 | `app/api/v1/endpoints/products.py` | 463-465 | `POST /{wf}/assessments` uses `client_id = uuid4()` | Same as C-6 |
| C-8 | `app/services/copilot/copilot_service.py` | 11 | `ImportError: WorkflowStage, SourceKind` — import fails, 247-line file is dead | Fix imports against actual `app.models` symbols (or remove dead module if genuinely unused) |
| C-9 | `app/scripts/init_db.py` | 6-9 | `ImportError: MarketTick, WorkflowInstance, AuditEvent` — only `create_all` entry point | Fix imports to real model names; ensure script runs |
| C-10 | `app/services/memory/memory_service.py` | 15-29 | `ClientMemory` defined in a **service** file → not in `Base.metadata`, no migration; `metadata` column name is reserved | Move model into `app/models/memory.py`, register in `app/models/__init__.py`, add migration, rename column to `extra_metadata` |
| C-11 | `app/models/models.py` | 41, 60 | `holdings` and `interactions` tables have **no migration** (only commented-out downgrade ALTERs) | Add an idempotent migration creating both tables; otherwise fresh DB → 500 on `/clients/{id}/portfolio`, brief/ranking services |
| C-12 | `app/api/v1/__init__.py` | 26-30 | Quadruple prefix double-stacking (calendar/artifacts/telemetry/meetings) | Document the convention; do NOT break it unilaterally — frontend matches. Normalise only with a coordinated frontend change |
| C-13 | `app/api/v1/endpoints/capture.py` | 310-315 | `POST /meetings/{id}/capture/segments` uses random `capture_id` | Query active `CaptureSession` by `meeting_id`, then `append_segment_progress` |
| C-14 | `app/api/v1/endpoints/capture.py` | 360-365 | `PATCH /extractions/{id}/edits` uses random `current_revision_id` → always ValueError | Load the real current `ArtifactRevision` for the extraction |

## HIGH (21)

| ID | File | Lines | Problem | Required fix |
|---|---|---|---|---|
| H-1 | `app/services/product/search_service.py` | 36-44 | `search_products` always `([], None, UNCONFIGURED)` → whole product chain dead | Implement a real catalog query (product_universe / product table) with entitled-universe filtering |
| H-2 | `app/services/product/search_service.py` | 46-58 | `get_product_details` always `None` | Query product by ref |
| H-3 | `app/services/product/suitability_service.py` | 171-179 | `_check_profile_validity` always `"CURRENT"` → **missing/expired profiles can get GREEN** (compliance risk) | Query KYC/profile freshness; return MISSING/EXPIRED/CONFLICT appropriately so RED gate triggers |
| H-4 | `app/services/product/suitability_service.py` | 181-217 | `_evaluate_factors` returns two fixed PASS factors → always GREEN | Evaluate real factors (risk match, objective match, complexity, concentration, HK suitability rules) against client profile and product |
| H-5 | `app/api/v1/endpoints/products.py` | 67-69 | `_get_suitability_policy` always `None` → rating UNAVAILABLE, overrides blocked | Resolve approved policy from `config_service` |
| H-6 | `app/api/v1/endpoints/products.py` | 51-64 | `_get_universe_config` / `_get_catalog_ref` return `uuid4()` + `"0"*64` hash | Resolve real `ConfigRef` with real content hash |
| H-7 | `app/services/capture/extraction_service.py` | 175-190 | `stub_ai_extraction` always `[]` | Implement deterministic rule-based extraction from transcript/notes (no external AI dependency) |
| H-8 | `app/services/brief/brief_generator.py` | 154-187 | `_generate_section` always UNAVAILABLE empty section — two competing brief paths | Assemble the 5 sections from real client/portfolio/calendar/interaction context |
| H-9 | `app/api/v1/endpoints/briefs.py` | 346 | `_persist_legacy_brief` hardcodes zero UUID `artifact_revision_id` → `review_brief` always 409 stale | Pass the real `revision.id` created by the generator |
| H-10 | `app/api/v1/endpoints/briefs.py` | 401, 480 | Content hash always `"0"*64` → `If-Match` always 412 | Compute real `content_hash` |
| H-11 | `app/services/messaging/message_service.py` | 99-159 | `_generate_message_content` returns template text with `destination="placeholder@example.com"`, `evidence_refs=[]` | Build draft from real client contact + grounded claims with evidence refs; never invent a destination |
| H-12 | `app/services/messaging/provider_stub.py` | 90-98, 152-158 | `send_message` simulates ACCEPTED; `readback_status` always DELIVERED | Only used by tests — keep as an explicit test double, do not let production call it |
| H-13 | `app/services/messaging/provider_stub.py` | 100-132 | `check_dnc` / `check_channel_opt_out` **allow all** when configured | Implement real DNC / opt-out registry lookup; fail closed on unknown |
| H-14 | `app/services/messaging/provider_stub.py` | whole | No provider wired into production `ActionService.execute_action` | Wire provider dispatch through the outbox worker |
| H-15 | `app/services/actions/outbox_worker.py` | whole | Worker never started — `main.py` has **no startup/lifespan/scheduler**; actions stay pending forever | Add lifespan startup that runs the outbox worker loop; graceful shutdown |
| H-16 | `app/services/shariah/shariah_service.py` | 35-53 | `screen_instrument` always `compliant: True`; keyword blacklist never fires (caller passes empty `business_description`); fabricates `"Shariah Screening Engine v1.0"` provenance | Use the real AAOIFI RAG/compliance service; return INSUFFICIENT_INFORMATION when evidence is missing; honest provenance |
| H-17 | `app/services/brief/brief_service.py` | 241-242 | Agenda decided by `"%" in changes["content"]` string matching | Use structured market-movement data |
| H-18 | `app/services/market/currency_service.py` | 26-28 | No API key → hardcoded static rates presented as live, no `as_of`/source | Tag fallback rates explicitly (`source: "STATIC_FALLBACK"`, `as_of`, `is_live: false`) and surface in the currency-exposure response |
| H-19 | `app/api/v1/endpoints/actions.py` | 52-54, 129-130, 215-216 | Fixed zero-UUID `client_id`; `get_current_tenant_id()` returns `"test-tenant"` (inconsistent with `FIXTURE_TENANT_001`) | Resolve client_id from artifact_ref; use the shared identity fixture constant |
| H-20 | `app/api/v1/endpoints/capture.py` | 20, 110, 163, 214, 262, 311, 360 | `MOCK_TENANT`/`MOCK_ACTOR` + random client_id → FK violations on `consent_records`/`capture_sessions` | Resolve real principal from `app.core.identity`; resolve client_id from meeting |
| H-21 | `app/api/v1/endpoints/capture.py` | 181, 233 | `policy_ref.hash = "mock"` | Use the real policy configuration hash |

## MEDIUM (17)

| ID | File | Lines | Problem | Required fix |
|---|---|---|---|---|
| M-1 | `app/api/v1/endpoints/workflow.py` | 64-65, 114-115, 160-161, 264-265, 308-309, 359-360 | `stages=[]`, `action_ids=[]` in 6 responses | Load `stage_runs` and `outbox_actions` |
| M-2 | `app/api/v1/endpoints/workflow.py` | 191-193 | `skill_id = stage_key`, `skill_version = "1.0.0"` literals | Call `SkillRegistry.get_skill()` |
| M-3 | `app/api/v1/endpoints/workflow.py` | 397 | `input_refs=[]` | Load `stage_artifact_refs` |
| M-4 | `app/api/v1/endpoints/workflow.py` | 256, 307, 351 | `type=WorkflowStatus(workflow.workflow_type)` — **wrong enum → pause/resume/abandon all 500** | Use `WorkflowType(...)` |
| M-5 | `app/services/workflow/registry.py` | 80-83 | Permission check simplified to "any workflow permission" | Check each skill's `required_permissions` |
| M-6 | `app/services/family/household_service.py` | 100-112 | `member_contexts=[]`; `consenting_count=len(members)` assumes all consent (violates its own docstring) | Check consent per member, aggregate real context |
| M-7 | `app/services/product/suitability_service.py` | 247-251 | `_compute_input_hash` omits policy_ref and profile version | Include all decision inputs |
| M-8 | `app/services/shariah/shariah_service.py` | 15-24 | `SHARIAH_TOOLS_PATH` default `/tmp` → always stub branch | Replace with the in-repo AAOIFI RAG service |
| M-9 | `app/services/capture/extraction_service.py` | 158 | `id=UUID` (the **type object**, not an instance) → insert fails | `id=uuid4()` |
| M-10 | `app/services/capture/extraction_service.py` | 150-153 | Non-canonical content hash | Use canonical JSON (`separators=(',',':')`, `ensure_ascii=False`) matching `message_service._compute_hash` |
| M-11 | `app/api/v1/endpoints/capture.py` | 225-226, 246-247 | Consent withdrawal does **not** revoke active captures (compliance risk) | Query and revoke all active `CaptureSession`s for the meeting; return real `invalidated_refs` |
| M-12 | `app/api/v1/endpoints/meetings.py` | 40-44 | `workflow_ids=[]`, `source_refs=[]` | Query associated workflows and source evidence |
| M-13 | `app/services/ranking/ranking_service.py` | 159, 171 | Concentration threshold hardcoded `0.10` | Read from config service |
| M-14 | `app/services/priority/ranking_service.py` | 221-262 | `_fetch_entitled_clients` returns 3 synthetic clients (`Alice Anderson` etc.) → FK violations into `client_assignments` | Query `client_assignments` + `contact_policy` with DNC filter |
| M-15 | `app/services/priority/ranking_service.py` | 480-488 | `_model_to_dto` fabricates `"Client 1"` names | Query real client name |
| M-16 | `app/services/priority/ranking_service.py` | 312-327 | Hardcoded signal values (15.5% / 45 days) for every client | Compute real AUM change and days-since-last-interaction |
| M-17 | `app/api/v1/endpoints/demo_clients.py` | 43-44, 53-95 | `inflation_pct` accepted but never used in `_deterministic_projection` | Apply inflation (real terms / inflation-adjusted target) |

## LOW (12)

Function-body imports (`artifacts.py:51`, `briefs.py:321`, `suitability_service.py:248`, `extraction_service.py:151-152`, `registry.py:73,124`, `message_service.py:180`, `outbox_worker.py:188`); constant zero-UUID `request_id` in `shariah.py:114,204`, `priorities.py:131,178,238,303,377`, `meetings.py:63`, `calendar.py:40`; `memory_service.py:16` reserved `metadata` column name; `briefs.py:50-58` hardcoded actor/tenant.

## Other structural findings

- `app/api/v1/endpoints/` has **no `__init__.py`** — works via PEP 420 but breaks on packaging. Add it.
- `alembic/env.py:22-25` swallows `ImportError` with `pass` → autogenerate silently produces empty migrations. Fix.
- `alembic/versions/README.md` is stale (references a non-existent `001_add_briefs_audit.py`). Update.
- `tests/test_priority_ranking.py` has 5 runtime `pytest.skip(...)` — controls/outcomes chains have zero coverage because evaluations return empty (M-14/C-5).
- `tests/test_migration_safety.py` requires external PostgreSQL.

## Frontend-expected but backend broken (11)

1. `POST /calendar/calendar/events/{id}/resolutions` — always 503 (C-1)
2. `GET /calendar/calendar/events` — always empty (C-3)
3. `PATCH /artifacts/artifacts/{id}` — always 501 (C-2)
4. `GET /briefs?client_id=` — always empty (C-4)
5. `POST /briefs/briefs/{id}/reviews` — always 409 (H-9/H-10)
6. `GET /priorities/evaluations` — always empty (C-5)
7. `POST /priorities/{id}/snooze|pin|dismiss` — no persistence (C-5)
8. `POST /products/{wf}/searches` — always empty (H-1)
9. `POST /products/{wf}/assessments` — random client + always GREEN/UNAVAILABLE (C-7/H-3/H-4)
10. `POST /meetings/{id}/capture/segments` — random capture_id (C-13)
11. `PATCH /extractions/{id}/edits` — random revision_id (C-14)

Also dead: `POST /workflow/{id}/pause|resume|abandon` → 500 (M-4); `GET /actions/{id}` never reaches terminal state (H-15).

---

## PRD §7 outstanding engineering scope (from `03_PRD_Comprehensive_2026.md`)

Items below are agreed roadmap scope, **not** stubs. Externally-gated items (Shariah board approval, legal disclaimer wording, production SSO provider, third-party data connections) are explicitly out of scope for an engineering pass.

| Theme | Implementable items |
|---|---|
| 7.1 HK regulatory | HK suitability rule set; conduct-standards tags on audit trail; jurisdiction-aware controls; KYC/suitability expiry monitoring with task creation |
| 7.2 Client record | Aggregated client view (one endpoint); document store with upload/retrieval/expiry/tagging; transaction history |
| 7.3 Portfolio analytics | Stress testing / scenario analysis; reference-portfolio comparison with drift; separate investment performance from currency movement; market-movement history |
| 7.4 Family office | Legal structures (trust/holdco/foundation/LP); ownership links with percentages; look-through exposure; consolidated net worth; provenance on imported figures |
| 7.5 Shariah depth | Manager review screen; portfolio-wide screening; Zakat with recognised thresholds and holding periods |
| 7.6 Everyday tools | CSV export of client book; brief export; calendar `.ics` export |
| 7.7 Live-readiness | UI/E2E test suite skeleton; load test script; deployment/rollback runbook |

## Fix order

1. Hard crashes (C-1, C-2, C-13, C-14, M-4)
2. Compliance false-green (H-3, H-4)
3. Startup/lifespan + outbox worker (H-15)
4. Missing migrations (C-10, C-11)
5. Dead imports (C-8, C-9)
6. Hardcoded returns (C-4, C-5, H-6, H-9, H-10)
7. PRD §7 engineering items (feature additions)

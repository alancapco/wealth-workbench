# RM Workbench — Feature Plan / Task Cards

**Date:** 2026-11-09
**Owner:** Delivery Director (齐活林)
**Baseline:** `AUDIT_2026-11-09_Unimplemented_Inventory.md`, `03_PRD_Comprehensive_2026.md` v3.0, `family-office-integration-plan.md`
**Team:** `rm-workbench-remediation-2c0a`

## Delivery strategy

Two waves. Wave 1 repairs all 64 audit findings (stubs / half-done / empty code) in parallel with **disjoint file ownership** so no two engineers touch the same file. Wave 2 adds the missing PRD §7 / family-office capability as new, additive code.

**Contract freeze:** route paths, response envelopes, existing table/column names and the double-prefix convention for calendar/artifacts/telemetry/meetings are frozen. The live OpenAPI shows 85 paths; that number must not shrink.

**Four iron rules:** (1) Simplicity — reuse existing helpers, no duplicate implementations, no over-abstraction. (2) Comments only at key logic/boundary points (why, not what). (3) Contract freeze as above. (4) All deliverables written to disk in real project directories.

## Wave 1 — Repair (Batch 0 + Batch 1)

| Card | Owner | File ownership (exclusive) | Findings |
|---|---|---|---|
| #1 Batch 0 Foundation | `fullstack-dev-foundation` | `app/models/**`, `app/scripts/init_db.py`, `app/services/copilot/**`, `app/services/memory/**`, `app/services/actions/outbox_worker.py`, `alembic/**`, `app/core/identity.py`, `app/main.py`, `app/api/v1/endpoints/__init__.py` | C-8, C-9, C-10, C-11, H-15, structural |
| #2 Batch 1A | `fullstack-dev-core-endpoints` | `endpoints/calendar.py`, `meetings.py`, `artifacts.py`, `telemetry.py`, `session.py` | C-1, C-2, C-3, M-12, LOW ids |
| #3 Batch 1B | `fullstack-dev-brief` | `endpoints/briefs.py`, `services/brief/**` | C-4, H-8, H-9, H-10, H-17 |
| #4 Batch 1C | `fullstack-dev-priority` | `endpoints/priorities.py`, `services/priority/**`, `services/ranking/**` | C-5, M-13, M-14, M-15, M-16 |
| #5 Batch 1D | `fullstack-dev-product` | `endpoints/products.py`, `services/product/**` | C-6, C-7, H-1..H-6, M-7, HK suitability |
| #6 Batch 1E | `fullstack-dev-capture` | `endpoints/capture.py`, `services/capture/**` | C-13, C-14, H-7, H-20, H-21, M-9..M-11 |
| #7 Batch 1F | `fullstack-dev-workflow` | `endpoints/workflow.py`, `actions.py`, `services/workflow/**`, `services/actions/action_service.py` | M-1..M-5, H-19 |
| #8 Batch 1G | `fullstack-dev-services` | `services/messaging/**`, `shariah/**`, `market/**`, `family/**`, `endpoints/shariah.py`, `demo_clients.py`, `clients.py`, `market.py` | H-11, H-13, H-16, H-18, M-6, M-8, M-17 |
| #9 Batch 1H Frontend | `fullstack-dev-frontend` | `frontend/**` | hardcoded data, orphaned pages, response shapes, loading/error/empty states |

**Gate:** every card must self-test with
`cd backend && .venv/bin/python -c "from app.main import app; print(len(app.openapi()['paths']))"` (must succeed, >= 85 paths) plus its relevant pytest module. Frontend must pass `npx tsc --noEmit`.

## Wave 2 — Missing PRD capability (Batch 2)

Sources: `03_PRD_Comprehensive_2026.md` §7 and `family-office-integration-plan.md` §2.1 / §3 Phase 1 / Appendix B.

### Card #10a — Family-office entity graph (read-only federation layer)
New models: `LegalEntity`, `EntityOwnership`, `ConsolidatedPosition`, `AssetMaster`, `DataLineage`, `Entitlement`, `FamilyGovernance`, `SuccessionPlan`, `IntegrationSource`, `IntegrationJob`. One new alembic migration (check the live head before setting `down_revision`). Look-through service with recursive ownership aggregation, cycle guard and a 3-level chain test (100% direct / 60% indirect / multi-hop). Seed data for the Chen Family example (Appendix A).

Frozen endpoint contract (from Appendix B):
```
GET /api/v1/entities/{entity_id}                                  -> entity + parent/child ownership
GET /api/v1/entities/{entity_id}/ownership?direction=both         -> recursive ownership_tree
GET /api/v1/entities/{entity_id}/positions                        -> positions + provenance
GET /api/v1/households/{household_id}/consolidated-view           -> total_net_worth, by_asset_class, by_entity, by_beneficiary
GET /api/v1/households/{household_id}/net-worth?base_currency=USD -> multi-currency consolidated net worth
GET /api/v1/positions/{position_id}/lineage                       -> source, as_of, reconciliation, fx, manager_return, fx_effect
GET /api/v1/households/{household_id}/governance                  -> succession plan, meetings, alerts
GET /api/v1/clients/{client_id}/beneficial-positions              -> look-through beneficial value
```
Every imported figure carries `source_id`, `as_of_date`, `reconciliation_status`, `valuation_status`. Read-only; never write back to a source system.

### Card #10b — PRD §7 client-record, analytics and export features
Implemented as additive endpoints/services, reusing existing `client_data` models and local file-backed demo stores (no second migration):
- Aggregated client view (one endpoint assembling profile + holdings + interactions + goals + documents + transactions)
- Document store (upload/list/retrieve/expiry/tagging), transaction history, opportunity pipeline with stage/value/forecast
- Stress testing / scenario analysis, reference-portfolio drift, performance-vs-FX decomposition, market-movement history
- Portfolio-wide Shariah screening and Zakat with recognised thresholds (nisab) and holding period (hawl)
- KYC/suitability expiry monitoring that raises a priority task before expiry; conduct-standard tags on audit records; jurisdiction-aware control lookup
- CSV export of the client book, brief export, calendar `.ics` export

### Card #10c — Frontend surfaces for Wave 2
New pages for the family-office consolidated view, documents, transactions, opportunities, stress testing and exports, wired into the existing navigation without changing the Capco visual style.

## Wave 3 — Gates
1. `code-reviewer`: contract consistency, duplicate implementations, over-abstraction, comment noise, security (fake recipients, fail-open DNC, fabricated compliance results).
2. `qa-verifier`: functional / boundary / exception / permission test cases; run the full backend suite; verify no endpoint regressed from the 85-path baseline.
3. `release-integrator`: end-to-end flow verification, feature-completeness check, delivery manifest and release note in `deliverables/`.

**Exit condition:** all 64 audit findings resolved or explicitly waived with a reason; zero hard-crash endpoints; no fabricated data reaching a client-facing surface; OpenAPI path count >= 85 plus all new Wave-2 paths; backend import smoke test clean; frontend type-check clean.

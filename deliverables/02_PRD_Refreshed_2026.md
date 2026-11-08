# RM Workbench — Refreshed PRD (2026 Edition)

**Date:** 2026-11-08  
**Author:** Team Lead  
**Status:** Draft for Review  
**Supersedes:** `01_PRD_Requirement_Inventory.md` (original 111 requirements)  
**Scope:** Full capability refresh incorporating family office, Shariah compliance, HSBC-style RM workflows, and HK regulatory specifics  

---

## 0. Executive Summary

This PRD refreshes the original requirement inventory against:
1. **Current implementation reality** — a codebase audit of 14 capability areas (see §2)
2. **HSBC Hong Kong RM benchmark** — WPIS, My Portfolio, Future Planner as reference features
3. **Family Office Integration Plan** — entity ownership graphs, look-through, succession
4. **Shariah Compliance RAG** — AAOIFI-backed product screening copied from islamic-ai project
5. **HK regulatory specifics** — SFC suitability obligations, HKMA conduct rules

**Headline finding:** The workbench has strong orchestration (workflow, brief, capture, audit) and priority/NBA infrastructure, but significant gaps in pipeline management, financial planning, portfolio analytics, document vault, and family office entity management. Shariah compliance RAG is newly integrated but requires AAOIFI data ingestion to activate.

---

## 1. The RM Daily Workflow (Reference Model)

Adapted from HSBC HK and Citi wealth management practices. Every feature in this PRD maps to one or more steps.

| Step | RM Action | System Capability Required | Status |
|------|-----------|---------------------------|--------|
| **1. Prepare** | Open client view, check life events, maturing products, recent contacts | Unified Client View + NBA signals | ⚠️ Partial |
| **2. Discover & Profile** | Update financials, goals, risk tolerance; planning tool models goals | Financial Planning + KYC/Suitability | ⚠️ Partial |
| **3. Advise** | Run portfolio analytics and stress tests; suitability check confirms product fits | Portfolio Analytics + Suitability Engine | ⚠️ Partial |
| **4. Execute & Document** | Complete onboarding/KYC refresh; audit trail of advice | Action Approval + Audit Log + Digital Documents | ⚠️ Partial |
| **5. Follow Up** | Log interaction, set tasks, record referrals/leads in pipeline | Meeting Capture + Tasks + Pipeline | ⚠️ Partial |

**Key insight from HSBC HK:** The RM and the client work from the *same screens*. WPIS (powered by BlackRock Aladdin) is available to Premier clients in mobile app, online banking, or together with their RM. This means the workbench's client-facing views must be shareable, not just RM-internal.

---

## 2. Capability Assessment (14 Areas)

### Legend
- ✅ Implemented — model + endpoint + frontend page all exist
- ⚠️ Partial/Stub — some layers exist but incomplete or hardcoded
- ❌ Missing — no model, no endpoint, no frontend

---

### A. Unified Client View

**Target:** One screen showing products, balances, transactions, interactions, and documents.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Client demographics + wealth profile | ✅ | `DemoClient` (client_data.py): religion, shariah_compliant, client_segment, aum, risk_profile |
| Portfolio holdings display | ✅ | `ClientPortfolioHolding` + `GET /clients/{id}/portfolio` + `AllocationChart.tsx` |
| Interaction history | ✅ | `ClientConversation` + `Interaction` model + brief sections include interactions |
| Document vault | ❌ | No document model, no storage endpoint, no document tab |
| Single aggregated Client 360 endpoint | ❌ | No `GET /clients/{id}/360` that joins all data; frontend assembles from multiple calls |
| Transaction history | ❌ | No transaction model; `Holding` is point-in-time, not time-series |

**Gap Priority:** HIGH — document vault and transaction history are fundamental to "one screen" promise.

**Requirement additions:**
- **FR-A1:** `GET /api/v1/clients/{client_id}/360` — single endpoint returning profile, holdings, interactions, documents, suitability status, and active workflows in one response
- **FR-A2:** Document vault model: `ClientDocument` (type, file_ref, uploaded_by, uploaded_at, expires_at, tags)
- **FR-A3:** Transaction history: `ClientTransaction` (date, type, amount, currency, description, source_system)

---

### B. Pipeline & Cross-Sell

**Target:** Stage-based opportunity tracking, renewals, and manager dashboards for forecasting.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Opportunity pipeline (stages) | ❌ | No `Opportunity` model, no pipeline endpoints |
| Renewals tracking | ❌ | No renewals model |
| Manager dashboard / forecasting | ⚠️ | `GET /dashboard/kpis` exists but returns hardcoded placeholder values |
| Cross-sell suggestions | ⚠️ | Priority ranking surfaces cross-sell reasons but no dedicated opportunity creation |

**Gap Priority:** MEDIUM — not in original PRD GA scope but needed for competitive parity with HSBC/Citi.

**Requirement additions:**
- **FR-B1:** `Opportunity` model: client_id, product_ref, stage (PROSPECT → PROPOSED → ACCEPTED → IMPLEMENTED → CLOSED), estimated_value, probability_pct, target_close_date, source (CROSS_SELL / RENEWAL / REFERRAL / INBOUND)
- **FR-B2:** `GET /api/v1/pipeline?book_id={book_id}` — list all open opportunities with stage breakdown
- **FR-B3:** `GET /api/v1/pipeline/forecast?book_id={book_id}` — weighted pipeline value by month/quarter
- **FR-B4:** Renewal calendar: products with maturity dates surfaced in dashboard "My Day" view

---

### C. Next-Best-Action (NBA)

**Target:** AI recommendations on what to offer or do for each client.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| AI recommendations per client | ✅ | `PriorityItem.reasons` JSONB with reason codes and signal sources |
| Book-wide priority ranking (Top 10) | ✅ | `RankingService` + `POST /books/{book_id}/priority-evaluations`, rank 1-10 constraint |
| Signal detection (market moves) | ⚠️ | `market_service.detect_market_signal()` called in dashboard; no persistent signal store |
| Signal detection (life events) | ❌ | No life event model, no life event detection service |
| Snooze/dismiss/pin controls | ✅ | `POST /priorities/{client_id}/snooze|dismiss|pin` |
| Contact outcome recording | ✅ | `ContactOutcome` with CONTACTED/MEETING_BOOKED/NO_RESPONSE/NOT_RELEVANT |

**Gap Priority:** LOW — core NBA is functional; life event detection is a Phase 2 enhancement.

**Requirement additions:**
- **FR-C1:** `LifeEvent` model: client_id, event_type (MARRIAGE / BIRTH / DEATH / RETIREMENT / JOB_CHANGE / RELOCATION / ILLNESS), detected_at, confidence, source (MANUAL / SIGNAL), confirmed_by
- **FR-C2:** Life event signals feed into priority ranking as reason codes

---

### D. Financial Planning

**Target:** Goal and retirement projections. Citi references MoneyGuidePro and NaviPlan.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Goal records | ⚠️ | `ClientFinancialPlan` exists but read-only demo data; no write endpoint |
| Retirement projections | ❌ | No projection calculation service |
| Life event simulation | ❌ | No simulation engine |
| "Investors like me" feature | ❌ | No peer comparison or cohort matching |

**Gap Priority:** MEDIUM — original PRD (OOS-01) defers full financial planning to V1. However, basic goal CRUD and simple projection are achievable.

**Requirement additions:**
- **FR-D1:** `POST/PUT/DELETE /api/v1/clients/{client_id}/financial-plans` — CRUD for financial plan records
- **FR-D2:** Simple goal projection: given current_value, monthly_contribution, target_amount, assumed_return_pct → months_to_goal or probability_of_success
- **FR-D3:** "Investors like me" — cohort matching by (age_band, risk_profile, asset_class_mix) → top 5 similar clients' allocation for comparison (aggregate/anonymized only, no PII)

---

### E. Portfolio Analytics

**Target:** Holdings by asset class, comparison with reference mix, currency exposure, and stress tests. (HSBC's WPIS benchmark)

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Holdings by asset class | ✅ | `Holding.asset_class` + `AllocationChart.tsx` |
| Reference mix comparison | ⚠️ | `GET /dashboard/performance-trend` has benchmark vs portfolio but hardcoded |
| Currency exposure breakdown | ❌ | `ClientPortfolioHolding.currency` exists but no aggregation endpoint |
| Stress test / scenario analysis | ❌ | No scenario model or analysis service |
| Performance attribution (manager return vs FX) | ❌ | No decomposition service (planned in family office Phase 2) |

**Gap Priority:** HIGH — WPIS-style analytics is a competitive differentiator for APAC wealth clients.

**Requirement additions:**
- **FR-E1:** `GET /api/v1/clients/{client_id}/portfolio/currency-exposure` — aggregate holdings by currency, show % allocation and converted base value
- **FR-E2:** `GET /api/v1/clients/{client_id}/portfolio/benchmark-comparison?benchmark=HSI` — compare actual allocation vs reference index, show drift % per asset class
- **FR-E3:** Stress test: `POST /api/v1/clients/{client_id}/portfolio/stress-test` with scenario params (market_shock_pct, currency_shock_pct, sector_shock) → impact on total portfolio value and per-asset-class
- **FR-E4:** Performance attribution: separate manager return from FX effect (ties to family office multi-currency work)

---

### F. KYC & Suitability

**Target:** Automated KYC refresh, suitability checks, and policy-governed workflows.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Suitability check against product rules | ✅ | `SuitabilityOverride` with GREEN/YELLOW/RED, factor_keys, reason_code |
| Policy-governed override with audit trail | ✅ | `SuitabilityOverride.rationale` + `ConfigurationRevision` + `AuditEvent` hash chain |
| KYC refresh workflow | ⚠️ | `ClientSuitabilityProfile.expiry_date` + `is_expired` exists but no automated refresh trigger or reminder |
| SFC suitability obligations (HK-specific) | ⚠️ | Policy config exists but no HK jurisdiction rules package |

**Gap Priority:** HIGH — KYC expiry currently only flagged, not actioned. HK regulatory exposure requires explicit SFC compliance.

**Requirement additions:**
- **FR-F1:** KYC expiry monitoring: daily job checks `ClientSuitabilityProfile.expiry_date`, creates priority alert when within 30 days
- **FR-F2:** `POST /api/v1/clients/{client_id}/kyc-refresh` — initiate KYC refresh workflow (generates Workflow with type=KYC_REFRESH)
- **FR-F3:** HK SFC suitability rule package: jurisdiction='HK', rules covering (a) reasonable basis for recommendation, (b) client's risk tolerance matching, (c) product complexity assessment, (d) disclosure obligations
- **FR-F4:** HKMA conduct rules reference: link audit events to HKMA-required conduct standards (fairness, transparency, suitability, avoid conflict of interest)

---

### G. Tasks & Case Management

**Target:** Automatic task routing and audit trails.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Action approval workflow | ✅ | `ActionPreview → ActionAuthorization → OutboxAction → OutboxAttempt` 4-level state machine |
| Audit trail (hash-chained, tamper-proof) | ✅ | `AuditEvent` with `previous_hash` + `event_hash`, `AuditChainHead` |
| Automatic task routing | ⚠️ | Action classes exist (CRM_WRITE, TASK_WRITE, etc.) but no routing rule engine |
| Task list / case queue UI | ⚠️ | `frontend/app/workflows/page.tsx` exists but not a dedicated task queue |

**Gap Priority:** LOW — core workflow + audit is solid; routing rules are a configuration layer on top.

**Requirement additions:**
- **FR-G1:** Task routing rules: `RoutingRule` model (condition → assignee, priority, due_in_hours) evaluated when actions are created
- **FR-G2:** `GET /api/v1/tasks?book_id={book_id}&status=open` — RM's task queue with filtering by action_class and priority

---

### H. Digital Documents

**Target:** Online document requests in place of paper.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Meeting brief generation | ✅ | `Brief` model + `BriefModal.tsx` + `CanonicalBriefView.tsx` |
| Document request workflow | ❌ | No document request model or endpoint |
| Document vault / storage | ❌ | No document storage, no upload/download endpoints |
| Document versioning | ❌ | `ArtifactLineage` handles AI artifacts, not client documents |

**Gap Priority:** HIGH — paper replacement is a core digital transformation promise.

**Requirement additions:**
- **FR-H1:** `ClientDocument` model: client_id, document_type (KYC / STATEMENT / CONTRACT / TAX_FORM / PROSPECTUS / CUSTOM), file_ref (path/URL), file_name, mime_type, file_size, uploaded_by, uploaded_at, expires_at, tags (JSONB), checksum
- **FR-H2:** `POST /api/v1/clients/{client_id}/documents` — upload document (multipart)
- **FR-H3:** `GET /api/v1/clients/{client_id}/documents?type=KYC` — list documents with filtering
- **FR-H4:** `GET /api/v1/documents/{document_id}/download` — download document
- **FR-H5:** Document request: `POST /api/v1/clients/{client_id}/document-requests` — request a document from client (type, deadline, message); creates task + notification

---

### I. Meeting Preparation

**Target:** A meeting-prep agent that summarises a client's holdings and recent interactions.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Pre-meeting brief generation | ✅ | `Brief` + `Workflow(MEETING_PREP)` + LLM integration |
| Recent interactions summary | ✅ | `Interaction` + `ClientConversation` + brief sections |
| Life events / maturing products surfaced | ⚠️ | No life event model; maturity derived from financial plan target_date but not auto-surfaced |
| Meeting capture with consent | ✅ | `ConsentRecord` + `CaptureSession` + `TranscriptSegment` |
| Shariah context in brief | ⚠️ | Client's shariah_compliant flag exists but brief doesn't auto-include Shariah compliance section |

**Gap Priority:** LOW — meeting prep is one of the strongest areas. Life event surfacing ties to FR-C1.

**Requirement additions:**
- **FR-I1:** Brief auto-includes "Maturing Products" section: scans `ClientFinancialPlan.target_date` for items within 90 days, surfaces in brief
- **FR-I2:** Brief auto-includes "Shariah Considerations" section when client has `shariah_compliant=true`: shows compliance status of current holdings, flags any non-compliant positions

---

### J. Shariah / Islamic Compliance

**Target:** Evidence-backed Shariah compliance estimation for investment products using AAOIFI standards RAG.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Client shariah preference flag | ✅ | `DemoClient.shariah_compliant` + `ClientSuitabilityProfile.shariah_preference` |
| AAOIFI-backed product screening (RAG) | ✅ | `AaoifiStandard` + `AaoifiClause` with pgvector; `ShariahRagService` (3-way hybrid search: tsvector + pgvector + direct citation, RRF fusion); `ShariahComplianceService` (LLM analysis with Riba/Gharar/Haram_Sector detection) |
| Shariah evidence records | ✅ | `ShariahEvidence` (evidence_type, source_url, compliance_status) |
| Shariah estimate with disclaimer | ✅ | `ShariahEstimate` (LIKELY_COMPLIANT / LIKELY_NON_COMPLIANT / INSUFFICIENT_DATA) + mandatory disclaimer |
| Zakat calculation | ⚠️ | Old `shariah_service.py` stub hardcodes 2.5%; no nisab/hawl logic |
| DEC-05 feature gate | ✅ | Config `SHARIAH_DEC05_ENABLED` + capability controls |
| AAOIFI data ingestion | ✅ | `ingest_aaoifi.py` script (page-level, all 54 standards); status='draft' until approved |
| Frontend Shariah review page | ❌ | No `/workflows/:id/shariah` page; no `ShariahReview.tsx` component |

**Gap Priority:** MEDIUM — backend RAG is complete; frontend page and real data ingestion needed to activate.

**Requirement additions:**
- **FR-J1:** Frontend: `frontend/app/workflows/[workflowId]/shariah/page.tsx` — Shariah review page showing estimate, findings (Riba/Gharar/Haram_Sector with severity), AAOIFI source citations, and mandatory disclaimer
- **FR-J2:** Zakat calculation service: `POST /api/v1/clients/{client_id}/zakat-estimate` — accepts asset breakdown, applies nisab threshold and 2.5% rate, returns zakat_due amount with calculation breakdown
- **FR-J3:** Portfolio-level Shariah screening: `POST /api/v1/clients/{client_id}/shariah-portfolio-screen` — screens all holdings, returns compliant/non-compliant/uncertain per holding with evidence

---

### K. Family Office

**Target:** Entity ownership graphs, look-through exposure, consolidated wealth reporting, succession planning.

**Reference:** "An RIA reports on accounts. A family office reports on a family." — entity graph navigation, not account lists.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Person-to-person relationships | ✅ | `FamilyRelationship` (SPOUSE/PARENT/CHILD/SIBLING/OTHER) |
| Household grouping | ✅ | `HouseholdGroup` + `HouseholdMembership` |
| Family graph visualization | ✅ | `FamilyGraphModal.tsx` component |
| Legal entity models (trusts, LLCs) | ❌ | No `LegalEntity` model; `DemoClient.family_office_name` is a text field only |
| Entity-to-entity ownership (%) | ❌ | No `EntityOwnership` model |
| Look-through exposure calculation | ❌ | No recursive ownership path calculation |
| Consolidated net worth by entity | ❌ | No aggregation across entities |
| Multi-currency positions | ❌ | `ClientPortfolioHolding` has single `currency` field but no FX conversion |
| Entitlements (VIEW/DECIDE per entity) | ❌ | No `Entitlement` model |
| Succession planning | ❌ | No `SuccessionPlan` model |
| Family governance tracking | ❌ | No `FamilyGovernance` model |
| Illiquid/lifestyle assets | ❌ | No asset type model supporting real estate, art, etc. |

**Gap Priority:** HIGH for UHNW segment; the `family-office-integration-plan.md` defines a 5-phase roadmap.

**Requirement additions (from family office integration plan):**
- **FR-K1:** `LegalEntity` model: entity_type (TRUST/LLC/FOUNDATION/HOLDCO/LP/INDIVIDUAL), jurisdiction, formation_date, tax_id
- **FR-K2:** `EntityOwnership` model: owner_entity_id, owned_entity_id, ownership_pct, ownership_type (DIRECT/BENEFICIAL), effective_date
- **FR-K3:** `ConsolidatedPosition` model: entity_id, asset_id, quantity, market_value, currency, as_of_date, source_system, reconciliation_status
- **FR-K4:** Look-through calculation service: recursive ownership % aggregation, materialized ownership paths for O(1) queries
- **FR-K5:** `GET /api/v1/households/{household_id}/consolidated-view?base_currency=USD` — consolidated net worth by asset class, entity, and beneficiary
- **FR-K6:** `Entitlement` model: entity_id, person_id, entitlement_type (VIEW/DECIDE/MANAGE), scope, granted_by, expires_at
- **FR-K7:** `SuccessionPlan` model: household_id, current_decision_maker_id, successor_id, training_status, target_transition_date, readiness_score
- **FR-K8:** `FamilyGovernance` model: household_id, governance_type (MEETING/CHARTER/SUCCESSION_PLAN), scheduled_date, attendees, minutes_ref, decisions

---

### L. Market Data

**Target:** Live quotes, market news, and signal detection integrated with Tiger Broker and Alpha Vantage.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Real-time quotes | ⚠️ | `market_service.py` with Alpha Vantage GLOBAL_QUOTE + Tiger Broker fallback; hardcoded mock when no API key |
| Market news | ✅ | `MarketNewsPanel.tsx` + 5-min news cache + Tiger Broker NewsClient + Alpha Vantage NEWS_SENTIMENT fallback |
| Market signal detection | ⚠️ | `detect_market_signal()` compares change% vs threshold; no persistent signal store |
| HK watchlist quotes | ✅ | `get_market_quotes_snapshot()` fetches HSBC, TCEHY, 0005.HK, 1299.HK, 0388.HK |
| Market snapshot endpoint | ✅ | `GET /api/v1/market/snapshot` |

**Gap Priority:** LOW — market data is functional. Signal persistence is a nice-to-have.

**Requirement additions:**
- **FR-L1:** `MarketSignal` model: symbol, signal_type (OPPORTUNITY/RISK), change_pct, price, timestamp, source — persisted for historical signal tracking
- **FR-L2:** `GET /api/v1/market/signals?days=7` — list recent market signals for dashboard alert feed

---

### M. Workflow Orchestration

**Target:** Multi-stage workflows with context, brief lifecycle, meeting capture.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Multi-stage workflow with context | ✅ | `Workflow` (9 states) → `StageRun` (8 states) → `SkillVersion` (versioned) |
| Context revision tracking | ✅ | `workflow.context_revision` field |
| Brief → review → approve → archive | ✅ | `ArtifactLineage → ArtifactRevision → ArtifactItem → ReviewDecision` |
| Meeting capture with consent | ✅ | `ConsentRecord` + `CaptureSession` + `TranscriptSegment` + `ExtractionEdit` |
| Workflow types | ✅ | MEETING_PREP / MEETING_FOLLOWUP / OUTREACH / PRODUCT_SEARCH / SHARIAH_REVIEW / HOUSEHOLD_REVIEW |

**Gap Priority:** NONE — workflow orchestration is the most complete area in the system.

---

### N. Regulatory / Compliance (HK-Specific)

**Target:** SFC suitability obligations, HKMA conduct rules, audit-proof advice log.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Audit trail for all advice events | ✅ | `AuditEvent` hash chain + `AuditChainHead` + `TelemetryEvent` |
| DNC (Do-Not-Contact) enforcement | ✅ | Priority ranking excludes DNC clients; `check_book_access()` authorization |
| SFC suitability rules (HK-specific) | ⚠️ | Policy config framework exists but no HK jurisdiction rules package |
| HKMA conduct rules | ❌ | No HKMA-specific rule reference or compliance check |
| Jurisdiction-aware compliance | ❌ | No `jurisdiction` field on policy configs; no versioned rules service |

**Gap Priority:** HIGH for HK market deployment. The family office integration spec (§2) explicitly calls for a "versioned jurisdiction-rules service, never hardcoded logic."

**Requirement additions:**
- **FR-N1:** `JurisdictionRule` model: jurisdiction (HK/SG/US/GB), rule_type (SFC_SUITABILITY / HKMA_CONDUCT / SEC_ADVISER / MAS_CMS), rule_version, effective_date, rule_content (JSONB), source_ref
- **FR-N2:** Versioned rules service: `GET /api/v1/compliance/rules?jurisdiction=HK&type=SFC_SUITABILITY` — returns active rule version
- **FR-N3:** Suitability evaluation calls jurisdiction rules service to validate against HK SFC requirements before returning result
- **FR-N4:** HKMA conduct rules reference: audit events tagged with applicable conduct standard (fairness, transparency, suitability, conflict avoidance)

---

## 3. Everyday Tools Integration

**Target:** Excel, Outlook, and Word integration for RM workflow.

| Sub-capability | Status | Evidence |
|----------------|--------|----------|
| Excel export of client data | ❌ | No CSV/XLSX export endpoint |
| Outlook calendar integration | ❌ | No calendar sync; `CalendarEvent` model exists but is demo data |
| Word document generation | ⚠️ | Brief generation exists (LLM text) but no .docx export |
| Brief export to PDF | ❌ | No PDF generation endpoint |

**Gap Priority:** MEDIUM — RMs live in Excel and Outlook. Export is the minimum viable integration.

**Requirement additions:**
- **FR-O1:** `GET /api/v1/clients/{client_id}/export?format=xlsx` — export client profile + holdings + interactions as Excel
- **FR-O2:** `GET /api/v1/briefs/{brief_id}/export?format=docx` — export brief as Word document
- **FR-O3:** `GET /api/v1/briefs/{brief_id}/export?format=pdf` — export brief as PDF
- **FR-O4:** Calendar export: `GET /api/v1/calendar/export?format=ics` — export calendar events as iCal for Outlook import

---

## 4. Summary Scorecard

| Area | ✅ Done | ⚠️ Partial | ❌ Missing | Priority |
|------|---------|-----------|----------|----------|
| A. Unified Client View | 1 | 2 | 2 | HIGH |
| B. Pipeline & Cross-sell | 0 | 1 | 2 | MEDIUM |
| C. Next-Best-Action | 2 | 1 | 0 | LOW |
| D. Financial Planning | 0 | 1 | 2 | MEDIUM |
| E. Portfolio Analytics | 1 | 1 | 2 | HIGH |
| F. KYC & Suitability | 2 | 1 | 0 | HIGH |
| G. Tasks & Case Management | 2 | 1 | 0 | LOW |
| H. Digital Documents | 1 | 0 | 2 | HIGH |
| I. Meeting Preparation | 2 | 1 | 0 | LOW |
| J. Shariah Compliance | 4 | 1 | 1 | MEDIUM |
| K. Family Office | 2 | 0 | 9 | HIGH |
| L. Market Data | 2 | 2 | 0 | LOW |
| M. Workflow Orchestration | 3 | 0 | 0 | NONE |
| N. Regulatory/Compliance | 2 | 1 | 2 | HIGH |
| O. Everyday Tools | 0 | 1 | 3 | MEDIUM |
| **TOTAL** | **22** | **14** | **25** | — |

---

## 5. Implementation Priority Batches

### Batch 1: Client Data Foundation (HIGH priority, 2-3 weeks)
Closes the largest gaps in the most user-facing areas.

| Item | Requirement | Effort |
|------|-------------|--------|
| Client 360 endpoint | FR-A1 | S |
| Document vault | FR-A2, FR-H1-H5 | M |
| Transaction history | FR-A3 | M |
| KYC refresh workflow | FR-F1, FR-F2 | S |
| Currency exposure | FR-E1 | S |
| Benchmark comparison | FR-E2 | S |

### Batch 2: Family Office Foundation (HIGH priority, 4 weeks)
From `family-office-integration-plan.md` Phase 1.

| Item | Requirement | Effort |
|------|-------------|--------|
| LegalEntity model | FR-K1 | M |
| EntityOwnership model | FR-K2 | M |
| ConsolidatedPosition model | FR-K3 | M |
| Look-through calculation | FR-K4 | L |
| Consolidated view endpoint | FR-K5 | M |

### Batch 3: Regulatory & Compliance (HIGH priority, 2 weeks)
HK-specific compliance foundation.

| Item | Requirement | Effort |
|------|-------------|--------|
| JurisdictionRule model | FR-N1 | M |
| Versioned rules service | FR-N2 | S |
| SFC suitability integration | FR-N3 | M |
| HKMA conduct tagging | FR-N4 | S |

### Batch 4: Shariah Activation (MEDIUM priority, 1 week)
Activate the RAG that's already built but needs data + frontend.

| Item | Requirement | Effort |
|------|-------------|--------|
| AAOIFI data ingestion (run script) | Operational | S |
| Approve clauses in DB | Operational | S |
| Shariah review frontend page | FR-J1 | M |
| Zakat calculation service | FR-J2 | S |
| Portfolio-level screen | FR-J3 | M |

### Batch 5: Portfolio Analytics + Stress Test (HIGH priority, 3 weeks)
WPIS-style analytics for competitive parity.

| Item | Requirement | Effort |
|------|-------------|--------|
| Stress test endpoint | FR-E3 | L |
| Performance attribution | FR-E4 | L |

### Batch 6: Pipeline & Planning (MEDIUM priority, 3 weeks)
| Item | Requirement | Effort |
|------|-------------|--------|
| Opportunity model + endpoints | FR-B1-B3 | M |
| Renewal calendar | FR-B4 | S |
| Financial plan CRUD | FR-D1 | S |
| Goal projection | FR-D2 | M |
| Investors like me | FR-D3 | M |

### Batch 7: Everyday Tools (MEDIUM priority, 1 week)
| Item | Requirement | Effort |
|------|-------------|--------|
| Excel export | FR-O1 | S |
| Brief docx export | FR-O2 | S |
| Brief PDF export | FR-O3 | S |
| Calendar iCal export | FR-O4 | S |

### Batch 8: Family Office Advanced (from plan Phase 2-4, 8 weeks)
| Item | Requirement | Effort |
|------|-------------|--------|
| Entitlements | FR-K6 | M |
| Succession planning | FR-K7 | M |
| Family governance | FR-K8 | M |
| Multi-currency + FX separation | (from plan) | L |
| Integration adapters (Addepar/Canoe) | (from plan) | L |

---

## 6. HSBC HK Reference Feature Mapping

| HSBC Feature | RM Workbench Equivalent | Status | Gap |
|-------------|-------------------------|--------|-----|
| **WPIS** (Aladdin-powered) | Portfolio Analytics (E) | ⚠️ | Missing: currency exposure, stress test, reference mix comparison |
| **My Portfolio** (all holdings in one place) | Unified Client View (A) | ⚠️ | Missing: document vault, transaction history, single aggregated endpoint |
| **Future Planner** (goal simulation) | Financial Planning (D) | ⚠️ | Missing: projection engine, life event simulation |
| **"Investors like me"** | Financial Planning (D) | ❌ | Missing entirely |
| RM + client same screen | Client-facing portal | ❌ | Workbench is RM-only; no client-facing portal |
| Meeting prep agent | Meeting Preparation (I) | ✅ | Strong implementation |
| Suitability pre-check | KYC & Suitability (F) | ✅ | Strong implementation with override + audit |
| Knowledge graph (clients/products/rules → NBA) | NBA (C) + Shariah RAG (J) | ✅ | Priority ranking + AAOIFI RAG are the knowledge graph components |

---

## 7. Architecture Principles (Carried Forward)

1. **Read-only federation** — workbench federates data from authoritative sources, never recomputes vendor-certified metrics, never writes back (family office spec)
2. **Trust is a first-class output** — every figure carries source_id, as_of_date, reconciliation_status, valuation_status
3. **DEC gates** — all pilots (Shariah, Family, Mobile) are default-OFF, explicitly enabled via config
4. **Audit-proof** — hash-chained audit trail for all advice events, no blind actions
5. **Separation of concerns** — RM workbench presents context; family office platforms own the ownership graph; CRM owns contacts
6. **No hardcoded thresholds** — AUM figures, compliance rules, and jurisdiction logic are versioned configuration, not code
7. **HK regulatory awareness** — SFC suitability and HKMA conduct rules as versioned rule packages, not hardcoded

---

## 8. Out of Scope (V1)

Carried forward from original PRD + new exclusions:

- Full financial planning engine (MoneyGuidePro / eMoney / NaviPlan integration) — OOS-01
- Real-time trade execution / order management — OOS-02
- Custodian integration / settlement — OOS-03
- Client-facing web portal (separate product) — OOS-04
- Real SSO / production auth (currently fixture mode for dev) — OOS-05
- Production SSB/AAOIFI certified provider contracts — OOS-06 (DEC-05 external)
- Shariah scholar review of estimates and disclaimers — OOS-07 (external compliance gate)
- Multi-entity accounting / GL / NAV / waterfalls — OOS-08 (family office accounting platforms own this)
- GP portal / capital call / K-1 ingestion beyond Canoe adapter — OOS-09

---

## 9. Differences from Original PRD

| Original PRD Item | Refreshed PRD Change | Reason |
|-------------------|----------------------|--------|
| 111 requirements (FR-01 to FR-111) | Reorganized into 14 capability areas (A-O) | Clearer structure for gap analysis |
| No family office requirements | FR-K1 through FR-K8 added | Family office integration plan |
| No Shariah RAG requirements | FR-J1 through FR-J3 added | islamic-ai/shariah integration |
| No HK regulatory specifics | FR-N1 through FR-N4 added | SFC suitability + HKMA conduct |
| No pipeline/opportunity | FR-B1 through FR-B4 added | Competitive parity with HSBC/Citi |
| No document vault | FR-H1 through FR-H5 added | Core digital transformation gap |
| No stress test | FR-E3 added | WPIS benchmark feature |
| No "investors like me" | FR-D3 added | HSBC My Portfolio feature |
| No everyday tools | FR-O1 through FR-O4 added | RM workflow reality (Excel/Outlook/Word) |
| No currency exposure | FR-E1 added | APAC multi-currency wealth |
| No performance attribution | FR-E4 added | Multi-currency manager return vs FX |

---

## 10. Acceptance Criteria for Refreshed PRD

This PRD is accepted when:
1. [ ] All HIGH priority items have implementation batches assigned
2. [ ] Shariah compliance RAG activation steps documented (ingest → approve → enable DEC-05)
3. [ ] Family office Phase 1 model creation scoped with timeline
4. [ ] HK regulatory rule package design reviewed by compliance
5. [ ] HSBC feature mapping confirmed as target benchmark
6. [ ] Out-of-scope items explicitly confirmed by product owner

---

**END OF REFRESHED PRD**

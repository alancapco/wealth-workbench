# Family Office Integration Plan — RM Workbench Phase 2

**Prepared by:** Team Lead  
**Date:** 2026-11-08  
**Status:** Draft for Review  
**Purpose:** Bridge the gap between current implementation and family office requirements for RM perspective

---

## Executive Summary

**Current State:** Basic family relationship models exist (FamilyRelationship, HouseholdGroup, HouseholdMembership) but lack the entity ownership graphs, look-through calculations, and multi-currency consolidated reporting required for true family office management.

**Target State:** RM workbench that federates family office data from authoritative sources (Addepar, Canoe Intelligence, etc.) and presents a unified view of:
- Entity ownership structures (trusts, LLCs, foundations, holdcos)
- Look-through exposure calculations
- Consolidated net worth across entities and currencies
- Cross-generational wealth transfer tracking
- Family governance and succession planning

**Key Principle:** The workbench is a **read-only federation layer**, not a competing system of record. Family office platforms own the ownership graph and total wealth; the RM workbench presents it in a client-centric view.

**Implementation Approach:** 3 phases over 6-9 months, starting with core entity models and ownership graphs, then adding integration adapters, and finally governance/succession features.

---

## 1. Gap Analysis

### 1.1 Current Implementation

**Existing Models** (`backend/app/models/family.py`):
- `FamilyRelationship` — bidirectional person-to-person relationships (SPOUSE, PARENT, CHILD, SIBLING, OTHER)
- `HouseholdGroup` — household grouping with primary contact
- `HouseholdMembership` — members within households (PRIMARY or MEMBER roles)

**Existing Demo Client Models** (`backend/app/models/client_data.py`):
- `DemoClient` — basic family office fields (family_office_name, family_role, family_patriarch_email)
- Portfolio holdings with single currency (value_usd_millions)
- No entity ownership structures
- No look-through calculations
- No multi-currency support beyond USD conversion

**Current Capabilities:**
✅ Person-to-person relationships  
✅ Household grouping  
✅ Basic family role tracking  
✅ Client demographics and wealth profile  
✅ Portfolio holdings (flat list)  

**Critical Gaps:**
❌ Legal entity models (trusts, LLCs, foundations, holdcos)  
❌ Entity-to-entity ownership with percentages  
❌ Look-through exposure calculations  
❌ Multi-currency position tracking with FX separation  
❌ Illiquid/lifestyle asset tracking (real estate, art, aircraft)  
❌ Entitlements and decision rights  
❌ Succession planning and governance tracking  
❌ Integration adapters for external family office systems  
❌ Consolidated net worth by entity/owner/currency  
❌ As-of dates and reconciliation status tracking  

### 1.2 Research Document Requirements

**From Integration Spec (rm-workbench-integration-spec.md):**

**Core Requirements:**
1. **Entity ownership graph** — "client = household" in both SFO/MFO modes; entity hierarchy with partial ownership %
2. **Look-through exposure** — trust owning 60% of holdco holding $10M fund = $6M exposure
3. **Multi-currency/multi-jurisdiction** — separate FX effect from manager return
4. **Illiquid & lifestyle assets** — real estate, art, aircraft, with manual marks and as-of dates
5. **Read-only federation** — never recompute vendor-certified metrics, never write back
6. **Trust metadata** — every figure carries source_id, as_of_date, reconciliation_status, valuation_status
7. **Entitlements** — WHO MAY SEE and WHO MAY DECIDE encoded separately
8. **Succession tracking** — G2 beneficiaries, next-gen read-only entitlement
9. **Family governance** — family meetings, charter, succession plan

**Key Insight from Research:**
> "An RIA reports on accounts. A family office reports on a family."

The workbench must support entity graph navigation, not just account lists.

**Integration Sources (MVP Priority):**
- **Addepar** — ownership graph, look-through, consolidated reporting (richest documented API)
- **Canoe Intelligence** — capital calls, distributions, K-1s → RM alerts
- **Orion Advisor Tech** — portfolio + CRM relationship data
- **Black Diamond / Tamarac** — RIA-style holdings and performance
- **Plaid / ByAllAccounts** — held-away account aggregation

### 1.3 RM User Stories (What This Enables)

**Story 1: Entity Ownership View**
As an RM managing the Chen Family Office, I need to see that:
- Chen Family Trust owns 100% of Chen Holdco LLC
- Chen Holdco LLC owns 60% of Chen Investment Partners LP
- So when I see a $10M private equity commitment in the LP, I know the family's real exposure is $6M (100% × 60% × $10M)

**Story 2: Multi-Generation Visibility**
As an RM, when the patriarch Mr. Chen asks "what does my daughter's portion look like?", I need to filter the consolidated view by beneficiary entitlement, showing only positions where she has beneficial ownership.

**Story 3: Succession Planning**
As an RM, I need to track that Mr. Chen (age 78) is the current decision-maker, his son David is successor trustee-in-training, and flag this family for succession planning review in my priorities queue.

**Story 4: Cross-Currency Clarity**
As an RM managing a Hong Kong family with SGD, USD, and HKD holdings, I need consolidated net worth that separates "manager return" from "FX effect" so I can discuss performance without currency noise.

**Story 5: Capital Call Alerts**
As an RM, when Canoe Intelligence extracts a $2M capital call from a PDF in the family's GP portal, I need that surfaced in my priorities queue with deadline and funding-source recommendation.

**Story 6: Consolidated Net Worth**
As an RM preparing for quarterly review, I need a one-page consolidated net worth by asset class, with clear as-of dates and reconciliation status, so I can confidently discuss "total family wealth" without manual Excel reconciliation.

---

## 2. Target Architecture

### 2.1 Core Data Model (New Models Required)

**LegalEntity** (new model)
- Represents trusts, LLCs, foundations, holdcos, individuals as legal persons
- Fields: entity_type (TRUST, LLC, FOUNDATION, HOLDCO, INDIVIDUAL), jurisdiction, formation_date, tax_id, trustee_info, beneficiary_info
- Replaces client as the primary wealth-holding unit

**EntityOwnership** (new model)
- Directed ownership edges: entity_a owns X% of entity_b
- Fields: owner_entity_id, owned_entity_id, ownership_pct, ownership_type (DIRECT, BENEFICIAL), effective_date, expiry_date
- Enables look-through calculations

**ConsolidatedPosition** (new model)
- Replaces flat ClientPortfolioHolding with entity-scoped positions
- Fields: entity_id, asset_id, quantity, market_value, currency, as_of_date, source_system, reconciliation_status, valuation_method
- Multi-currency aware: stores original currency + base currency conversion

**AssetMaster** (new model)
- Security/asset reference data
- Fields: asset_id, asset_type (EQUITY, BOND, FUND, REAL_ESTATE, ART, etc.), ticker, name, asset_class, sub_class, is_liquid, pricing_source

**Entitlement** (new model)
- WHO MAY SEE and WHO MAY DECIDE
- Fields: entity_id, person_id, entitlement_type (VIEW, DECIDE, MANAGE), scope (FULL, PARTIAL), granted_by, granted_at, expires_at

**FamilyGovernance** (new model)
- Family meetings, charter, succession plan tracking
- Fields: household_id, governance_type (MEETING, CHARTER, SUCCESSION_PLAN), scheduled_date, attendees, minutes_ref, decisions, next_review_date

**SuccessionPlan** (new model)
- Leadership and trustee succession tracking
- Fields: household_id, current_decision_maker_id, successor_id, succession_trigger, training_status, target_transition_date, readiness_score

### 2.2 Integration Layer (New Adapters Required)

**IntegrationSource** (metadata table)
- Tracks connected family office systems
- Fields: source_id, source_name (ADDEPAR, CANOE, ORION, etc.), connection_status, last_sync_at, sync_frequency, credentials_ref

**IntegrationJob** (audit/monitoring)
- Tracks sync jobs and data freshness
- Fields: job_id, source_id, job_type (FULL_SYNC, INCREMENTAL, ALERT), status, started_at, completed_at, records_synced, errors

**DataLineage** (trust metadata)
- Every imported figure carries provenance
- Fields: record_id, record_type, source_id, source_record_id, as_of_date, imported_at, reconciliation_status (RECONCILED, PENDING, EXCEPTION), valuation_status (PRICED, MANUAL_MARK, STALE)

### 2.3 Enhanced Family Models (Extend Existing)

**FamilyRelationship** (extend existing)
- Add: relationship_metadata JSONB for notes, effective dates
- Add: is_beneficial_owner boolean for beneficiary tracking
- Add: decision_authority_level (NONE, ADVISORY, PARTIAL, FULL)

**HouseholdGroup** (extend existing)
- Add: household_type (SFO, MFO_CLIENT, RIA_CLIENT)
- Add: primary_entity_id (link to root LegalEntity)
- Add: aum_base_currency, total_net_worth (cached, refreshed by sync jobs)
- Add: governance_status (ACTIVE, TRANSITION, AT_RISK)

---

## 3. Implementation Roadmap

### Phase 1: Core Entity Models (Weeks 1-4, MVP Foundation)

**Goal:** Build the entity ownership graph foundation without external integrations.

**Deliverables:**
1. ✅ New models: LegalEntity, EntityOwnership, ConsolidatedPosition, AssetMaster
2. ✅ Alembic migrations for new tables
3. ✅ Extend existing family.py models with new fields
4. ✅ Database seed script with sample family office data (Chen Family example: patriarch, spouse, 2 children, family trust, holdco, 3 entities, ownership graph)
5. ✅ API endpoints (read-only):
   - `GET /api/v1/entities/{entity_id}` — entity details
   - `GET /api/v1/entities/{entity_id}/ownership` — ownership tree (upstream and downstream)
   - `GET /api/v1/entities/{entity_id}/positions` — positions held by this entity
   - `GET /api/v1/households/{household_id}/consolidated-view` — consolidated net worth across all entities
6. ✅ Look-through calculation service (recursive ownership % aggregation)
7. ✅ Unit tests for look-through calculations (test cases: 100% direct, 60% indirect, multi-hop)

**Acceptance Criteria:**
- RM can view entity hierarchy for a household
- Look-through exposure calculates correctly for 3-level ownership chain
- All new models pass foreign key and constraint tests
- API returns consolidated positions grouped by asset class with correct ownership-adjusted values

**Risk:** Complex recursive queries for deep ownership graphs → mitigate with materialized views or cached look-through results.

---

### Phase 2: Multi-Currency & Data Lineage (Weeks 5-8)

**Goal:** Add multi-currency support, as-of dates, and trust metadata (source tracking).

**Deliverables:**
1. ✅ Currency model with FX rates table (historical rates from external source like ECB)
2. ✅ Update ConsolidatedPosition to store: original_currency, base_currency, fx_rate, fx_rate_date, converted_value
3. ✅ New models: IntegrationSource, DataLineage
4. ✅ "Performance vs FX" decomposition service (separate manager return from FX effect)
5. ✅ API endpoints:
   - `GET /api/v1/households/{household_id}/net-worth?base_currency=USD` — consolidated net worth in specified currency
   - `GET /api/v1/positions/{position_id}/lineage` — show source system, as-of date, reconciliation status
6. ✅ Reconciliation status UI indicators (green = reconciled, yellow = pending, red = exception)
7. ✅ Stale data alerts (positions with as_of_date > 5 days old flagged in RM priorities queue)

**Acceptance Criteria:**
- RM can view consolidated net worth in USD, HKD, or SGD
- Each position displays source system, as-of date, and reconciliation status
- Performance report separates "manager return" from "FX gain/loss"
- Stale data (>5 days old) appears in priorities queue

**Risk:** FX rate data quality and historical coverage → use ECB as authoritative source, fallback to manual entry for exotic currencies.

---

### Phase 3: Integration Adapters (Weeks 9-16, MVP External Data)

**Goal:** Connect to external family office systems and ingest real data.

**Deliverables:**
1. ✅ Addepar adapter (OAuth2, read-only):
   - Sync entities, ownership edges, positions, transactions
   - Map Addepar entity types to LegalEntity model
   - Incremental sync (only changed records since last sync)
2. ✅ Canoe Intelligence adapter (OAuth2, webhook):
   - Subscribe to capital call / distribution / K-1 events
   - Create RM alerts for new capital calls with deadline
3. ✅ Integration job scheduler (daily sync for Addepar, real-time webhook for Canoe)
4. ✅ IntegrationJob monitoring dashboard (admin view: sync status, last run, errors)
5. ✅ Error handling and retry logic (failed syncs logged, retry with exponential backoff)
6. ✅ Data reconciliation checks (flag mismatches between source and local data)

**API Endpoints:**
- `POST /api/v1/integrations/sync/{source_id}` — trigger manual sync
- `GET /api/v1/integrations/jobs?source_id=addepar&status=failed` — monitor sync jobs

**Acceptance Criteria:**
- Addepar ownership graph synced daily, entities and positions visible in RM workbench
- Capital call from Canoe appears in RM priorities queue within 5 minutes of extraction
- Failed sync jobs visible in admin dashboard with error details
- No duplicate records created on re-sync (idempotent sync logic)

**Risk:** API rate limits and auth token expiry → implement token refresh, respect rate limits with backoff.

---

### Phase 4: Entitlements & Governance (Weeks 17-20)

**Goal:** Add family governance, succession planning, and entitlement controls.

**Deliverables:**
1. ✅ New models: Entitlement, FamilyGovernance, SuccessionPlan
2. ✅ Entitlement enforcement in API (filter positions by VIEW entitlement before returning)
3. ✅ Succession planning workflow:
   - Flag households where decision-maker age > 75 or succession_plan.target_transition_date < 6 months
   - Track training status of successor
4. ✅ Family governance tracking:
   - Schedule family meetings, link to calendar
   - Store meeting minutes references (link to document vault)
   - Track decisions and action items
5. ✅ G2 beneficiary view (filtered view showing only positions where person has beneficial ownership)
6. ✅ API endpoints:
   - `GET /api/v1/households/{household_id}/governance` — governance events and succession status
   - `GET /api/v1/entities/{entity_id}/entitlements` — who can view/decide for this entity
   - `GET /api/v1/clients/{client_id}/beneficial-positions` — positions where client is beneficiary

**Acceptance Criteria:**
- G2 beneficiary (e.g., Mr. Chen's daughter) sees only her entitled positions, not full family wealth
- Succession planning alert appears in RM priorities for patriarch age > 75 with no documented successor
- Family meeting scheduled in calendar, linked to household governance record
- Entitlement checks enforce at API level (unauthorized users get 403 for restricted entities)

**Risk:** Complex entitlement rules (partial ownership, time-bounded access) → start with binary VIEW/NO_VIEW, add nuance in later iterations.

---

### Phase 5: Frontend & RM Experience (Weeks 21-24)

**Goal:** Build RM-facing UI for family office features.

**Deliverables:**
1. ✅ Entity ownership visualization (tree/graph view, click to drill down)
2. ✅ Consolidated net worth dashboard (by asset class, entity, beneficiary)
3. ✅ Multi-currency toggle (switch base currency, see FX effects)
4. ✅ Priorities queue enhancements:
   - Capital call alerts with deadline countdown
   - Stale data warnings (positions > 5 days old)
   - Succession planning flags
5. ✅ Family office client card (enhanced client detail page):
   - Entity hierarchy tab
   - Beneficiaries & entitlements tab
   - Governance & succession tab
   - Consolidated performance tab
6. ✅ Meeting brief enhancement: auto-populate family structure, recent capital calls, pending governance items

**Frontend Routes:**
- `/clients/{client_id}/family-office` — family office overview
- `/clients/{client_id}/entities` — entity ownership graph
- `/clients/{client_id}/governance` — governance and succession

**Acceptance Criteria:**
- RM can visualize entity ownership tree, see look-through exposure on hover
- Consolidated net worth loads in < 2 seconds for household with 100+ positions
- Capital call alert clickable from priorities queue, shows deadline and recommended funding source
- Meeting brief includes "Family Structure" section with patriarch, successors, and key entities

**Risk:** Performance with deep ownership graphs (10+ levels, 100+ entities) → use cached materialized views, lazy-load subtrees.

---

## 4. Technical Design Decisions

### 4.1 Read-Only Federation vs Local SOR

**Decision:** The workbench is a **read-only federation layer**, NOT a competing system of record.

**Rationale:**
- Family office platforms (Addepar, Eton, Masttro) are authoritative for ownership graphs and positions
- RM workbench adds relationship context, priorities, and client-centric views
- Never recompute vendor-certified metrics (IRR, TVPI, look-through) — import and display only
- Never write back to source systems (no two-way sync)

**Implications:**
- IntegrationSource is append-only during sync (no user edits to imported data)
- Local overrides stored separately (e.g., manual FX rate adjustment flagged as "local override")
- Reconciliation status tracks when local data diverges from source

### 4.2 Multi-Tenancy: SFO vs MFO

**Decision:** Same codebase, two tenancy modes.

**Implementation:**
- HouseholdGroup.household_type enum: SFO | MFO_CLIENT
- SFO mode: single household, deep ownership graph, cost-center billing
- MFO mode: many households, row-level security, AUM-based billing
- Entitlement checks enforce household isolation in MFO mode (hard boundary)

**Configuration:**
- Tenant-level setting: `tenant_config.family_office_mode = "SFO" | "MFO"`
- SFO tenants bypass some cross-household ACL checks (single family = single tenant)

### 4.3 Look-Through Calculation Strategy

**Challenge:** Recursive ownership chains can be 10+ levels deep.

**Solution:** Materialized path + periodic recalculation.
1. Store flattened ownership paths in `entity_ownership_paths` table (updated on ownership change)
2. Query uses join on materialized paths instead of recursive CTE
3. Background job recalculates paths nightly (or on-demand after ownership edit)
4. API response time: O(1) read from materialized view, not O(n) recursive query

**Example:**
```
EntityOwnershipPath:
  household_id, root_entity_id, leaf_entity_id, path_entities[], cumulative_ownership_pct
  
  chen_family, chen_trust, investment_lp, [chen_trust, chen_holdco, investment_lp], 0.60
```

### 4.4 Currency Conversion & FX Separation

**Approach:** Store positions in original currency + converted base currency.

**Fields:**
- `original_currency`, `original_value`
- `base_currency`, `base_value`
- `fx_rate`, `fx_rate_date`
- `fx_source` (ECB, BLOOMBERG, MANUAL)

**Performance Calculation:**
```
Manager return = (ending_value_original - beginning_value_original) / beginning_value_original
FX effect = (ending_fx_rate - beginning_fx_rate) / beginning_fx_rate
Total return in base currency = (1 + manager_return) * (1 + fx_effect) - 1
```

**Display:** Show manager return and FX effect as separate line items in performance report.

---

## 5. Data Model Diagram (ASCII)

```
┌─────────────────────┐
│   HouseholdGroup    │
│  (Chen Family SFO)  │
└──────────┬──────────┘
           │
           │ primary_entity_id
           ▼
┌─────────────────────┐
│    LegalEntity      │
│  (Chen Family Trust)│
│   entity_type=TRUST │
└──────────┬──────────┘
           │
           │ EntityOwnership (100%)
           ▼
┌─────────────────────┐
│    LegalEntity      │
│  (Chen Holdco LLC)  │
│   entity_type=LLC   │
└──────────┬──────────┘
           │
           │ EntityOwnership (60%)
           ▼
┌─────────────────────┐
│    LegalEntity      │
│(Chen Investment LP) │
│   entity_type=LP    │
└──────────┬──────────┘
           │
           │ ConsolidatedPosition
           ▼
┌─────────────────────────────────┐
│     ConsolidatedPosition        │
│  entity_id: investment_lp       │
│  asset_id: private_equity_fund  │
│  market_value: 10,000,000 USD   │
│  as_of_date: 2026-11-01         │
│  source_system: ADDEPAR         │
│  reconciliation_status: OK      │
└─────────────────────────────────┘
           │
           │ Look-through: 100% × 60% = 60%
           │ Effective exposure: $6M
           ▼
    [RM Dashboard Display]
    "Chen Family Trust effective exposure
     to Private Equity Fund: $6,000,000"
```

**Person-to-Entity Relationships:**
```
┌────────────────┐         ┌────────────────┐
│  Person (Mr.   │─────────│  LegalEntity   │
│  Chen, Client) │ Trustee │ (Family Trust) │
└────────────────┘         └────────────────┘
                                   │
                            Beneficiaries:
                            ├─ Mrs. Chen (50%)
                            ├─ David Chen (25%)
                            └─ Emily Chen (25%)
```

---

## 6. Migration Strategy

### 6.1 Backward Compatibility

**Existing Data:**
- DemoClient records remain unchanged
- family.py models extended, not replaced
- New entity models run in parallel initially

**Migration Path:**
1. Create new tables (LegalEntity, EntityOwnership, etc.) via Alembic
2. Backfill: convert DemoClient records to LegalEntity (entity_type=INDIVIDUAL)
3. Link: create HouseholdGroup.primary_entity_id → LegalEntity mapping
4. Validation: run parallel queries, ensure totals match
5. Cutover: switch API endpoints to new models
6. Deprecation: mark old DemoClient.portfolio_holdings as legacy (Phase 1 only, remove in Phase 2)

### 6.2 Data Quality Gates

**Before Production:**
1. ✅ All positions have valid as_of_date
2. ✅ All positions have source_system attribution
3. ✅ No orphaned entities (every entity linked to a household or parent entity)
4. ✅ No circular ownership (A owns B, B owns A = INVALID)
5. ✅ Ownership percentages sum correctly (all children of entity X sum to ≤ 100%)
6. ✅ FX rates present for all currency pairs used in positions
7. ✅ Entitlements validated (no VIEW without parent household membership)

**Automated Checks:**
- Nightly data quality job runs all checks, flags exceptions
- Admin dashboard shows data quality score (% of positions passing all checks)

---

## 7. Testing Strategy

### 7.1 Unit Tests (Phase 1)

**Look-through calculation tests:**
- Single-level: 100% ownership → 100% exposure
- Two-level: 100% → 60% → 60% exposure
- Three-level: 100% → 60% → 50% → 30% exposure
- Multi-parent: Entity owned by 2 parents (40% + 30%) → 70% exposure via different paths
- Circular detection: A → B → C → A should raise error

**Currency conversion tests:**
- USD → HKD at 7.80 rate
- EUR → USD with historical rate (2025-01-01 vs 2026-11-01)
- Performance decomposition: 10% manager return + 5% FX gain = 15.5% total return

### 7.2 Integration Tests (Phase 3)

**Addepar adapter:**
- Mock Addepar API responses (entities, positions, transactions)
- Verify correct mapping to LegalEntity and ConsolidatedPosition
- Test incremental sync (only fetch changed records)
- Test error handling (API timeout, invalid response)

**Canoe adapter:**
- Mock webhook payload (capital call PDF extracted)
- Verify alert created in priorities queue
- Test duplicate detection (same capital call received twice)

### 7.3 End-to-End Test (Phase 5)

**RM User Journey:**
1. RM logs in, selects Chen Family household
2. Views entity ownership graph (3 entities visible)
3. Clicks Chen Investment LP → sees $10M position
4. Hovers over position → tooltip shows "Effective exposure: $6M (60% look-through)"
5. Switches base currency from USD to HKD → all values recalculated with FX rate
6. Checks priorities queue → capital call alert visible with 30-day deadline
7. Clicks capital call alert → sees details, recommended funding source
8. Opens meeting brief → Family Structure section auto-populated with patriarch, successors

**Acceptance:** All steps complete without errors, data loads in < 3 seconds per page.

---

## 8. Success Metrics

**Phase 1 (Core Models):**
- ✅ 100% of look-through calculations pass unit tests
- ✅ API response time < 1 second for household with 50 positions
- ✅ All Alembic migrations pass on test database

**Phase 3 (Integrations):**
- ✅ Addepar sync completes in < 5 minutes for household with 500 positions
- ✅ Capital call alerts appear in RM queue within 5 minutes of Canoe extraction
- ✅ < 1% sync failure rate (99% successful syncs)

**Phase 5 (Frontend):**
- ✅ RM can complete "view consolidated net worth" task in < 30 seconds
- ✅ Entity ownership graph renders for household with 20 entities in < 3 seconds
- ✅ 100% of RM test users can successfully filter by beneficiary entitlement

**Business Metrics:**
- RM time saved: 2 hours/week per family office client (no manual Excel reconciliation)
- Data freshness: 95% of positions have as_of_date within 48 hours
- Alert response time: 50% of capital calls acknowledged within 24 hours (vs baseline TBD)

---

## 9. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Addepar API rate limits slow sync | High | Medium | Implement exponential backoff, cache frequently accessed data |
| Circular ownership in imported data | High | Low | Detect and reject circular references during sync, alert admin |
| Deep ownership graphs (10+ levels) cause performance issues | Medium | Medium | Use materialized ownership paths, limit recursion depth to 10 |
| FX rate data gaps for exotic currencies | Medium | High | Use ECB as primary source, fallback to manual entry, flag as "estimated" |
| Entitlement rules too complex for MVP | Medium | High | Start with binary VIEW/NO_VIEW, defer partial ownership % to Phase 2 |
| Existing DemoClient data incompatible with new models | Low | Medium | Run parallel systems during Phase 1, validate with dual queries |
| Integration auth tokens expire during sync | Low | High | Implement token refresh, retry failed syncs automatically |

---

## 10. Next Steps

**Immediate Actions (Week 1):**
1. ✅ Create Alembic migration for Phase 1 models (LegalEntity, EntityOwnership, ConsolidatedPosition, AssetMaster)
2. ✅ Implement look-through calculation service (recursive ownership aggregation)
3. ✅ Write unit tests for look-through calculations (6 test cases)
4. ✅ Create database seed script with Chen Family example data

**Phase 1 Completion Checklist:**
- [ ] All new models created and migrated
- [ ] API endpoints implemented and tested
- [ ] Look-through calculations passing all unit tests
- [ ] Sample data seeded and viewable via API
- [ ] Frontend stub pages created (entity graph, consolidated view)

**Decision Points:**
- **Week 4:** Review Phase 1 implementation, decide on Phase 2 priority (multi-currency vs integrations)
- **Week 8:** Demo to stakeholders, gather feedback on entity ownership visualization
- **Week 16:** Evaluate Addepar integration success, decide on additional integration sources

**Review & Approval:**
- [ ] Product owner approval
- [ ] Security review (entitlement model, data isolation)
- [ ] Performance review (query performance with large datasets)
- [ ] Legal review (data residency, PII handling for family office clients)

---

## Appendix A: Sample Entity Ownership Data (Chen Family)

**Entities:**
1. Chen Family Trust (root, entity_type=TRUST)
2. Chen Holdco LLC (entity_type=LLC, owned 100% by Trust)
3. Chen Investment Partners LP (entity_type=LP, owned 60% by Holdco)
4. Chen Real Estate LLC (entity_type=LLC, owned 100% by Trust)

**Ownership Edges:**
- Chen Family Trust → Chen Holdco LLC (100%)
- Chen Holdco LLC → Chen Investment Partners LP (60%)
- Chen Family Trust → Chen Real Estate LLC (100%)

**Positions:**
- Chen Investment Partners LP holds: $10M private equity fund
- Chen Real Estate LLC holds: $15M commercial property, San Francisco

**Look-Through Exposure (from Trust perspective):**
- Private equity fund: $10M × 100% × 60% = $6M
- Real estate: $15M × 100% = $15M
- Total look-through exposure: $21M

**Beneficiaries:**
- Mr. Chen (Patriarch, Trustee, 100% decision authority)
- Mrs. Chen (Spouse, Co-trustee, 50% beneficial interest)
- David Chen (Son, Successor trustee-in-training, 25% beneficial interest)
- Emily Chen (Daughter, 25% beneficial interest)

---

## Appendix B: API Endpoint Specifications

**Phase 1 Endpoints:**

```
GET /api/v1/entities/{entity_id}
Response: {
  id, entity_type, name, jurisdiction, formation_date, 
  parent_ownership: [{ owner_entity_id, ownership_pct }],
  child_ownership: [{ owned_entity_id, ownership_pct }]
}

GET /api/v1/entities/{entity_id}/ownership?direction=upstream|downstream|both
Response: {
  entity_id, ownership_tree: [recursive entity + ownership % structure]
}

GET /api/v1/entities/{entity_id}/positions
Response: {
  positions: [{
    position_id, asset_id, asset_name, quantity, market_value, 
    currency, as_of_date, source_system, reconciliation_status
  }]
}

GET /api/v1/households/{household_id}/consolidated-view?base_currency=USD
Response: {
  household_id, as_of_date, base_currency,
  total_net_worth, 
  by_asset_class: [{ asset_class, market_value, look_through_pct }],
  by_entity: [{ entity_id, entity_name, market_value }],
  by_beneficiary: [{ person_id, person_name, beneficial_value }]
}
```

**Phase 2 Endpoints:**

```
GET /api/v1/positions/{position_id}/lineage
Response: {
  position_id, source_system, source_record_id, as_of_date, 
  imported_at, reconciliation_status, valuation_status, 
  fx_rate, fx_rate_date, manager_return, fx_effect
}
```

**Phase 4 Endpoints:**

```
GET /api/v1/households/{household_id}/governance
Response: {
  succession_plan: { current_decision_maker, successor, target_date, readiness },
  family_meetings: [{ date, attendees, minutes_ref, decisions }],
  alerts: [{ type, description, due_date }]
}

GET /api/v1/clients/{client_id}/beneficial-positions
Response: {
  client_id, beneficial_ownership_pct,
  positions: [{ entity_id, position_id, asset_name, beneficial_value }]
}
```

---

**END OF PLAN**

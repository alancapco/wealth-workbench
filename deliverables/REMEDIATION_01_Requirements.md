# Remediation Requirements & Phase-1 Approval Proposal — RM Workbench

**Status:** Scope approved by Alan; Phase-1 requirements handoff complete (not implementation acceptance or production certification)  
**Owner:** Requirements Analyst — Xu Qingchu (许清楚)  
**Scope basis:** `deliverables/01_PRD_Requirement_Inventory.md` (frozen PRD v1.1 inventory); `deliverables/REAUDIT_00_CONSOLIDATED.md`; specialist re-audits 01–03; `PROGRESS.md`.  
**Boundary:** This document defines what must be remediated and how it is accepted. It does not approve implementation, select technologies, freeze API/schema details, or claim any remediation has been delivered.

## Executive proposal and confirmation gate

Treat “fix all gaps” as remediation of the PRD’s real product capabilities, not a demo-only cleanup. The proposed scope is the full PRD capability set, delivered in its declared tiers: 22 core FRs for Epics 1–3 (including the 15 explicitly P0 FRs), plus six Epic 4–5 pilot FRs behind feature flags. Preserve PRD release sequencing and the rule that pilot work must not delay core GA. Apply cross-cutting controls, dependencies, exception handling, governance and operational gates from the frozen inventory. Maintain all no-go autonomy exclusions.

The available consolidated evidence reports **0 of 28 FRs fully implemented** at the audit snapshot. This is not a current-state verification and must not be converted into a delivery percentage. Partial code/artifact work is not delivered capability. In particular, the app boot failure and failed frontend typecheck block reliable end-to-end verification before feature-level acceptance can be meaningful.

**Original G-01–G-30 traceability is incomplete:** the original canonical register could not be recovered from the supplied gap-analysis report or accessible project artifacts; historical transcript access was denied. This proposal therefore does not invent G-ID-to-FR mappings. It records only mappings explicitly verified in the consolidated/specialist reports, independently covers all 28 stable PRD FR IDs, and marks unverified original labels as pending mapping. The user can supply the original table later to complete exact label mapping without blocking safe scope approval.

**Scope approval record:** Alan explicitly selected **“确认完整修复范围（推荐）”**, as relayed by team-lead. The approved scope is full real PRD core GA plus **default-off** Epic 4–5 pilots, Tier D excluded, production integrations/compliance externally gated, and preservation of existing data. The approval covers the following scope boundaries:
1. Full PRD remediation: core GA (Epics 1–3) plus Epic 4–5 pilots only as default-off, feature-flagged pilot scope; pilots do not block core GA.
2. Production certification remains externally gated by named providers/entitlements, credentials, data-owner decisions, legal/compliance/security approvals and production operations—not promised as locally resolvable engineering work.
3. Preserve existing data. Phase 1 authorizes no destructive data operations, external credential-based calls, production deployment, or live business side effects. Retain the PRD no-go rules: no autonomous advice, auto-send, auto-trade, execution, fatwas, or bypass of RM approval without a separately approved PRD.

**Gate disposition:** User scope confirmation is satisfied. The next authorized stage is product design under the lead's phase chain; architecture/contracts and independently testable delivery batches follow in order. This scope approval is not a claim of implemented repairs, test acceptance, provider authorization, pilot enablement, production deployment approval, or compliance certification. API/schema decisions remain subject to the architecture freeze.

## 1. Project overview

- **One-line positioning:** Restore and complete the RM Workbench as the PRD-defined, single-orchestrator AI copilot for wealth advisory workflows, backed by persistent client context and human approval at every client-facing or system-writing boundary.
- **Target users:** Senior Private Wealth RMs and Mass Affluent RMs; operational administrators; Compliance/Legal, Security and pilot-governance approvers. These roles are grounded in the PRD; detailed institutional assignments remain subject to the open decisions below.
- **Core value:** Reduce fragmented RM work while producing traceable, permissioned and reviewable outputs; meeting outcomes, prioritization and subsequent briefs participate in a measured closed loop rather than stand-alone demo features.
- **Success criteria:** All in-scope functional acceptance criteria pass; all core-GA gates pass before a core GA claim; required PRD telemetry computes the defined metrics; no guardrail regression is accepted. Numeric business targets remain validation targets, not guaranteed outcomes. Examples include 45→10 minutes meeting preparation, 20→5 minutes post-meeting administration, 60% brief adoption, ≥70% copilot workflow rate and ≥85% cross-skill completion. Baselines and measurement methods must be established before claims.

## 2. Users, roles and permissions

| Role | Description | May do | Must not do |
|---|---|---|---|
| Relationship Manager (RM) | Authorized user assigned client/book access | View entitled records; inspect sources and explanations; edit/reject/approve permitted drafts; record consent and meeting outcomes; initiate allowed workflows | View another book/tenant without entitlement; treat unverified data as fact; bypass hard stops; delegate autonomous client-facing or trade actions to AI |
| Administrator | Institution-authorized configuration operator | Configure the five PRD classes: field mappings, ranking/reason-code policies, templates/disclosures, consent rules, integration credentials; review/version configuration changes | Act outside assigned administrative scope; silently change policy; erase audit history; use configuration to permit prohibited actions |
| Compliance / Legal approver | Institution-designated policy owner | Approve jurisdiction-specific consent, disclosure, recording/retention, suitability and override policies; review evidence and release gates | Substitute an unapproved policy or override a regulatory/product hard stop |
| Security / Privacy approver | Institution-designated security and data-governance owner | Approve residency, provider controls, retention/deletion, access, secrets and security evidence | Certify providers or controls without evidence or contractual authority |
| Pilot / release operator | Authorized person managing rollout | Enable/disable approved feature or orchestration stage at approved cohort/scope; monitor gates and roll back | Expand pilot/GA without exit criteria; disable audit; enable autonomy prohibited by PRD |
| External data/provider adapter | Institutional or vendor system, not a human role | Supply contracted, entitled, attributable data or perform explicitly approved integration action | Claim LIVE availability without successful authenticated provider result; infer missing authoritative data; provide false success |

**Permission invariant:** authorization is server-side and tenant/book/node-scoped. Unauthorized data is excluded before copilot context assembly, not merely hidden in the UI. Every write/send/handoff requires an authorized human and auditable approval state.

## 3. Core workflows and exception branches

### Workflow 1 — Prepare, meet, follow up (FR-01…FR-10)
1. RM selects an authorized client or eligible calendar event → system resolves the identity; ambiguity requires explicit RM resolution.
2. Copilot creates a sourced brief → available sections remain usable; missing/stale sources are identified with as-of status; no fabricated fact, source, timestamp or LIVE label.
3. If recording is permitted and consented, RM records meeting → consent and recording state are audited; refusal/withdrawal stops capture and manual notes remain available.
4. Copilot extracts transcript evidence and proposed outcomes → RM can correct, accept or reject each item; unsupported owner/date remains blank; low-confidence output is marked for review.
5. Copilot presents proposed notes, CRM changes, tasks, email draft and eligible ticket fields together → nothing is written, sent or submitted before explicit RM approval.
6. Approved actions are persisted/sent through entitled providers with idempotent status → retry does not duplicate records/actions; failure never reports success.

### Workflow 2 — Prioritize and converse (FR-11…FR-15)
1. Copilot ranks up to ten authorized clients from permitted, current signals → empty book/low-signal state remains empty; DNC and channel opt-outs exclude outreach.
2. RM inspects reason codes and evidence → each material reason links to source and timestamp; protected attributes are not ranking inputs.
3. RM snoozes, dismisses, pins or records contact outcome → choice persists and has an audit trail; dismissal is not assumed to express client intent.
4. Copilot drafts contact content using approved reasons and entitled facts → absent facts are omitted; message remains editable.
5. Policy checks run before send → only an authorized RM can explicitly approve; blocked send, provider outage and retry status are visible and auditable.

### Workflow 3 — Discover and assess product (FR-16…FR-19; Tier B)
1. RM submits a natural-language request → interpreted filters are shown and editable before search.
2. Copilot returns only entitled/current products with sourced metrics and as-of dates → no results explain the constraint and may suggest editable relaxation, never silently weaken suitability constraints.
3. Suitability pre-screen evaluates current profile and product evidence → Green means no detected conflict, never compliance approval; missing/expired profile cannot be Green.
4. RM may override only a permitted soft warning with recorded reason → hard regulatory/product prohibition remains blocked; assessment and override are auditable.

### Workflow 4 — Serve Shariah-sensitive needs (FR-4.1…FR-4.3; Tier C pilot)
1. Authorized RM manages client preference → preference propagates through the same copilot context and skills.
2. Screening applies versioned, SSB-reviewed rule pack → each criterion has current evidence; missing/stale evidence cannot be labelled compliant and non-compliant candidates are excluded.
3. Zakat/purification estimate provides itemization, methodology, source/date and caveat → explicitly labelled discussion estimate requiring Shariah advisor confirmation; never a fatwa.
4. Proposal finalization requires complete versioned evidence pack → incomplete evidence blocks finalization.

### Workflow 5 — Serve family/household needs (FR-5.1…FR-5.3; Tier C pilot)
1. Copilot assembles family/entity context filtered by each node’s entitlement → unauthorized nodes are excluded before context reaches any AI skill.
2. Extracted structures require RM confirmation before canonical use; holdings reconcile under defined tolerances → unresolved discrepancies are flagged, not silently reconciled.
3. Meeting packs are generated per attendee entitlement; scenarios are illustrative with assumptions → no attendee receives another’s restricted data.
4. Capital-call/liquidity forecast uses verified notices and history → RM verification required and forecast-vs-actual is tracked.

## 4. MVP scope

### 4.1 Included scope

| Feature ID / stable PRD IDs | Capability | Scope and objective acceptance evidence | Priority / tier |
|---|---|---|---|
| F-001 / FR-01…FR-03 | Brief generation, sourcing, partial data and feedback | All five required brief sections are supported; sources/as-of timestamps and derived-vs-recorded distinction are visible; failure is section-scoped and does not fabricate; regeneration/version and feedback are auditable. Proposed canonical contract `response.brief.sections` remains **pending technical freeze**. | P0 / Core |
| F-002 / FR-04…FR-06 | Consent, transcription, extraction and recovery | Consent policy precedes capture; transcript evidence links to extracted items; manual notes survive provider failures; no false “complete” transcript. | P0 / Core; provider/policy dependencies apply |
| F-003 / FR-07…FR-10, FR-20 | Review, CRM/task write, draft and ticket handoff | Review of each proposed artifact is explicit; only accepted edits are written; CRM/email operations are idempotent and status-visible; ticket is prefill-only, suitability-gated, never submitted/executed by AI. | P0 / Core |
| F-004 / FR-11…FR-13 | Daily priorities and RM controls | At most 10 unique authorized clients, with reason/evidence/time; controls persist and influence subsequent ranking according to approved rules; no eligible clients yields honest empty state. | P0 / Core |
| F-005 / FR-14…FR-15 | Grounded outreach and approved send | Draft has reason, permitted facts and conversation opener where available; DNC/channel/disclosure policy blocks prohibited send; RM approval is mandatory; provider failures never show false success. | P0 / Core |
| F-006 / FR-16…FR-19 | Product search and suitability pre-screen | Editable interpreted filters; entitled current results and defined metrics; explainable R/Y/G status; missing/expired profile cannot be Green; hard stops are non-overridable. | P1 / Tier B; must not delay P0 launch |
| F-007 / FR-4.1…FR-4.3 | Shariah preference, screening, estimate and evidence pack | Configurable SSB-reviewed rules; sourced criteria; explicitly non-authoritative estimate; complete evidence pack required. | P1 pilot / Tier C, feature-flagged |
| F-008 / FR-5.1…FR-5.3 | Family/entity graph, governance and liquidity | Node-level entitlement in context assembly; RM-confirmed structures; per-attendee packs; illustrative scenario assumptions; verified capital-call inputs. | FR-5.1/5.2 P1 pilot [PRD inference], FR-5.3 P2 / Tier C, feature-flagged |
| F-009 / FR-21 | Mobile tasks as scoped | Client lookup, briefs, priorities and outreach approval obey same authorization/consent and secure-session controls; desktop-only transcription/ticket handoff allowed if policy requires. | P0 inferred cross-cutting; release depends on DEC-08 |
| F-010 / FR-22 | Runtime administration | Five listed configuration classes are editable with versioning and tamper-evident audit record. | P0 inferred cross-cutting |
| F-011 / D0…D5, B-01…B-12, NFR-01…NFR-11, GOV-01…GOV-08, INT-01…INT-11 | Dependencies and cross-cutting controls | Implement and verify the precise frozen inventory criteria. Tier allocation below governs release; no parallel/double-counted feature list. | Mixed: core, Tier B, pilot or production dependency as inventory §12.2 |
| F-012 / M-01…M-10, TEL-01…TEL-10, GRD-01…GRD-10, GATE-01…GATE-X, C-01…C-18 | Measurement, guardrails, rollout and copilot qualification | Implement measurement path and gate evidence. Numeric outcome targets are not delivery promises; C-17/18 and pilot telemetry are Tier C only. | Tiered as inventory §12.2 |

The authoritative detailed requirement and acceptance text is the frozen `01_PRD_Requirement_Inventory.md` §§2–12. This deliverable deliberately references that 111-control inventory rather than duplicating and drifting its full acceptance text. For the user-facing Phase-1 decision, all 28 FRs are enumerated above and all cross-cutting groups are explicitly included.

### 4.2 Excluded / not authorized in this phase

| Item | Reason | Later? |
|---|---|---|
| Any application code, configuration, dependency, API/schema or deployment changes | Phase 1 is requirements and approval only; architecture and implementation follow approved stages | Phase 2+ only after user confirmation and subsequent design/contract gates |
| External credential-based calls, live provider onboarding, production data writes/sends | Requires user authorization, credentials, vendor agreements, and operational safeguards; no live side effects in Phase 1 | Potentially later, separately authorized |
| Auto-send, auto-trade, trade execution, autonomous financial advice, bypass of RM review | Explicit V1 no-go/OOS; Q4 autonomy requires new PRD and approval | No, absent separate approved PRD |
| Fatwa issuance or authoritative religious rulings | Copilot is an evidence/calculation assistant; SSB/advisors retain authority | No |
| General-purpose chatbot unrelated to RM workflow | Not PRD-defined product capability; avoid a demo surface in place of orchestration | No |
| Full financial planning, alternative-investment marketplace, client portal, replacing system of record, automatic training on client/RM data | PRD explicitly excludes; not necessary for in-scope remediation and creates separate product/compliance scope | No for V1 |
| Treat unachieved numeric outcome targets as functional gaps | Targets require baseline, exposure and validation; engineering cannot promise business outcome | Validate after pilot measurement |
| Make Epics 4–5 mandatory core-GA blockers | PRD assigns these to feature-flagged pilots/V2; preserve tier boundary | Pilot release only under their own gates |

## 5. Exception and dependency requirements

| Scope / PRD IDs | Exception | Required outcome |
|---|---|---|
| F-001 / B-01, FR-03 | Data source unavailable, stale or partial | Show section-level state and as-of time; preserve unaffected sections; omit unavailable facts; no substitution or fabricated LIVE provenance. |
| F-001 / FR-01, B-02 | Ambiguous client match or conflicting records | Require RM resolution; link conflicting sources; block suitability/ticket handoff until authoritative resolution. |
| F-002 / B-03, FR-04 | Consent declined/withdrawn or policy unknown | Capture/transmission does not start or stops immediately; manual notes remain available; preserve consent-state audit. Unknown policy fails closed. |
| F-002 / B-04, B-10, FR-05/06 | Low confidence, unsupported format, provider/model failure | Mark for review or omit client-facing assertion; preserve edits/manual workflow; expose failure and last confirmed state; no fabricated completion. |
| F-003 / B-05, FR-08/09 | CRM/email outage, duplicate submit, timeout | Keep draft, show pending/failed status, idempotent safe retry/reconciliation; no false success or duplicate write/send. |
| F-003 / B-09, FR-10/18/19 | Missing/stale suitability, account or mandatory ticket field | Block handoff with reason; never infer suitability or execute trade. |
| F-004 / B-06/07, FR-11…13 | No eligible priority or DNC/channel restriction | Return empty/filtered list with last evaluation; no weak filler; outreach remains blocked even if risk ranked. |
| F-005 / FR-14/15 | Unsupported fact, missing disclosure, opt-out, provider failure | Omit unsupported fact; block send until all checks and explicit approval; safe retry reports actual status. |
| F-006 / B-08/09 | No suitable products or stale KYC | Explain no results; permit explicit editable soft-filter relaxation only; never relax hard suitability; missing/expired data cannot yield Green. |
| F-007 / B-11 | Non-compliant candidate or missing SSB evidence | Exclude candidate by construction; do not label compliant without current evidence; stop evidence pack finalization if incomplete. |
| F-008 / B-12 | Unauthorized household node / attendee or missing entitlement | Filter before context assembly; block output/action; emit entitlement-blocked audit/telemetry; no cross-entity disclosure. |
| All / D0, INT-10 | Missing authorization, tenant/book change or identity revocation | Fail closed server-side; invalidate stale context after role/book change; no data exposed from stale entitlement. |
| All / provider-backed functions | Credentials, license, entitlement or provider unavailable | Capability marked unavailable/degraded; no fabricated records, provenance or success; fixture mode is visibly labelled and isolated from LIVE paths. |
| All / data persistence | Migration/schema mismatch, empty or inconsistent database | Readiness gate fails; no silent no-op migration; no claim of successful writes until persistence and readback verified. |

## 6. Acceptance and release gates

Acceptance is binary per frozen criteria: pass only with reproducible evidence in an approved test environment. A source file, UI mock, fixture, stub, route declaration or “works on my machine” alone does not count as delivered capability. A feature is end-to-end accepted only after its wired user path, authorization, persistence/provider outcome, exceptions and evidence are tested.

| Gate | Testable exit condition | Scope effect |
|---|---|---|
| G0 — runnable verification baseline | Backend imports/boots; frontend type-check/build passes; dependency manifests and launch path are reproducible; health/readiness reflects actual dependency state; migration runs against empty disposable DB and asserts expected schema/revision state. | Blocks reliable downstream end-to-end testing; not a production certification. |
| G1 — core P0 | All FR-01…FR-15 and their relevant dependencies, boundaries, controls, telemetry and tests pass; 15 explicitly P0 FRs remain non-negotiable; inferred cross-cutting priority is labelled as such. | P0 launch readiness. |
| G2 — copilot/core GA | FR-16…FR-22 and required Tier B dependencies/approvals pass for GA of Epics 1–3; C-01…C-16 all YES for a copilot claim; no pilot-tier C-17/18 is required for core GA. | Core GA only; Epic 3 does not delay P0 launch. |
| G3 — pilot readiness | Each Epic 4/5 capability remains feature-flagged and passes its own SSB/legal, data entitlement, source evidence, pilot cohort and rollback criteria. C-17/18 and pilot guardrails apply when claiming those pilots. | Pilot-only; cannot block core GA. |
| G4 — production certification | Named production owners accept privacy/residency, security, contractual provider retention/training, licensing/data entitlements, jurisdictional policy, backups/restore, monitoring/on-call, availability/scale and deployment evidence. | External/institutional approval; not satisfied by local tests or this proposal. |

**Cross-cutting test rules:**
- Demonstrate a complete closed loop: approved meeting outcomes can feed prioritization and later briefs through the same copilot and persistent client memory; show measured workflow events and source provenance at each transition.
- For each write/send/handoff, verify preview → explicit authorized approval → real persisted/provider outcome → audit/readback; reject actions without approval and ensure retries are idempotent.
- Provider/fixture simulation must be explicit (`FIXTURE`/`UNAVAILABLE`, not `LIVE`), isolated from production credentials/data and excluded from live success claims.
- Verify actual state after success and failure; 2xx/exit-0 alone is insufficient if no durable effect occurred.
- Run entitlement and no-go tests as hard gates, not observational checks.
- Metrics report denominator, event definition, baseline and limitations. No causal retention claim from raw cohort differences; baseline-first targets remain labelled as such.

## 7. Gap traceability (verified only; no guessed mappings)

### 7.1 Verified G-label findings in supplied re-audit evidence

| Original G label | Evidence-backed finding from re-audit | Remediation PRD linkage | Mapping status |
|---|---|---|---|
| G-01 | Brief partially improved, but mock market data is falsely stamped LIVE, agenda claimed AI-generated without call, and brief is not persisted/versioned. | FR-01…FR-03, FR-20; B-01; GOV-03; INT-03; NFR-06 | Evidence-backed mapping by capability; original register row not available for verbatim comparison. |
| G-04 | Timezone correction is partial; broad exception handling still returns an empty Top 10 with HTTP 200. | FR-11…FR-13; B-06; GOV-07; NFR-07/10 | Evidence-backed capability mapping; exact original wording pending. |
| G-11 | HubSpot fetch added but app cannot boot; idempotency, pagination and rate-limit handling not demonstrated. | FR-08; INT-04; B-05; NFR-11 | Evidence-backed capability mapping; provider operation additionally requires credentials/tenant authorization. |
| G-13 | Persistent D5 memory remains unwired; schema/table absent in inspected DB; model issues noted. | D5; FR-20/22; C-04/05/15; NFR-06; GATE-01 | Evidence-backed capability mapping; no claim that artifact equals delivered memory. |
| G-22 | Workflow orchestrator is in-memory/dead code; no stage execution or persistence; live start path returns empty stages. | FR-20; D5; C-01…C-05, C-09, C-11/12; TEL-08; GOV-07 | Evidence-backed capability mapping; original row detail pending. |
| G-23 | Provenance validator is structural, not tied to actual source query, and is not called; false provenance exists. | FR-02/03; GOV-03; NFR-07; INT-11; C-08 | Evidence-backed capability mapping; original row detail pending. |
| G-25 | Real health implementation is unregistered; live endpoint hardcodes database connected and returns 200 when unhealthy. | NFR-03/10/11; GATE-01; operational readiness G0 | Evidence-backed capability mapping; original row detail pending. |
| G-26 | Frontend/backend brief routes and response envelope mismatch; fake brief ID; workflow body/query mismatch latent; frontend fails typecheck. | FR-01…FR-03, FR-07/20/21; NFR-01/07/09; G0 | Evidence-backed mapping; contract proposal is not frozen. |
| G-28 | Migration files and ignore entries exist but release capability is absent: broken Alembic config/discovery, no baseline, missing tables; credentials remain on disk; artifact progress is not migration capability. | D0/D1/D5; NFR-04/05/06/11; GATE-01; GOV-02; operational G0/G4 | Evidence-backed capability mapping; keep artifact-level progress separate from delivered capability. |

### 7.2 Unverified labels and full capability coverage

The consolidated report lists G-02, G-03, G-05…G-10, G-12, G-14…G-21, G-24, G-27, G-29 and G-30 as unchanged/not attempted, but their original row titles and exact PRD mappings are **not available in the artifacts reviewed**. For G-10, G-12, G-15–G-21 and G-24 the lead specifically directs status “original label unverified; mapping pending.” No label’s identity, feature meaning or mapping is guessed here. Stable PRD IDs and feature groups F-001…F-012 define the complete remediation scope independently.

| Traceability set | Coverage treatment |
|---|---|
| All 28 functional requirements | Explicitly covered: FR-01…FR-22, FR-4.1…FR-4.3, FR-5.1…FR-5.3 in §4.1. |
| 15 declared P0 FRs | FR-01…FR-15 retained as P0; all acceptance remains required for P0 launch. |
| Remaining core FRs | FR-16…FR-19 are Tier B/P1 GA for Epics 1–3; FR-20…FR-22 have inferred P0 V1-wide priority as documented in frozen inventory. |
| Six pilot FRs | FR-4.1…4.3 and FR-5.1…5.3 are Tier C/feature-flagged; FR-5.3 is PRD-declared P2; pilots cannot silently become core-GA blockers. |
| Dependencies/control groups | D0…D5, B-01…B-12, NFR-01…NFR-11, GOV-01…GOV-08, INT-01…INT-11, M-01…M-10, TEL-01…TEL-10, GRD-01…GRD-10, GATE-01…GATE-X and C-01…C-18 are governed by frozen inventory §12.2 tiers and their detailed criteria. |
| G-01…G-30 | Exact row-by-row crosswalk remains pending original register; no fabricated mapping. Verified report mappings above are retained; all functional capability work is scoped via stable PRD IDs now. |

## 8. External and operational blockers (not promised locally fixable)

| Dependency/blocker | What must be supplied/approved | Why local code alone cannot certify it |
|---|---|---|
| Provider systems and credentials | Institution-selected CRM, calendar, email/SMS, core banking, portfolio, market/news, product/suitability, custodian/identity and any meeting/transcription providers; approved credentials/scopes and test tenants | These are environment/vendor choices, account-bound secrets and contractual integrations; no real LIVE response can be invented. |
| Licensing and data rights | Market/news/product data licenses, attribution terms, API limits and allowed client use | Entitlement and rights belong to provider/institution contracts; fixtures do not demonstrate licensed production access. |
| Privacy, security and residency | Approved regions, subprocessors, cross-border flows, retention/deletion/legal hold, encryption, access review, incident response and provider zero-retention/training evidence | Requires institutional and vendor evidence, and possibly independent assurance; code inspection alone cannot establish contractual or regulatory compliance. |
| Jurisdiction-specific legal/compliance | Recording consent, disclosures, suitability rules, hard-stop/override matrix, DNC/channel policy, retention policy and launch approvals | Product owner/legal/compliance authorities must resolve and approve; decisions are open in PRD DEC-01…DEC-08. |
| Epic 4 governance | Design partner, SSB owner, screening standard, methodology, zakat convention and evidence-source approval | SSB review/sign-off and valid sourced rules are external governance inputs. |
| Epic 5 data/access governance | Entity types, custodian feeds, reconciliation tolerances, attendee/node entitlement matrix and document quality thresholds | Institution-specific data and entitlements cannot be inferred or safely fabricated. |
| Production operations | Named service owner, deployment/release process, monitoring/alert routes, on-call, backup/restore objectives and tested recovery, capacity/availability evidence | Production certification requires operational execution, environment access and responsible owners beyond a local requirements plan. |
| Business validation | Baselines, representative pilot cohort across both RM personas, time-motion method, adoption definitions and matched retention method | PRD numeric targets are planning/validation targets; measured outcomes require real pilot operation and approved analytics. |

**Fail-closed rule:** if any dependency is absent, only a clearly labelled isolated fixture or unavailable state may be shown. The product must not present mock values as live, fabricate source lineage, silently downgrade controls, or report external action success before provider confirmation.

## 9. Assumptions and open decisions

| ID | Assumption / decision | Impact / required confirmation |
|---|---|---|
| A-01 | [Confirmed scope] The intended endpoint is a PRD-conformant operational product, not a demo-only prototype. Alan selected “确认完整修复范围（推荐）”, as relayed by team-lead. | Scope approved; implementation and certification still require subsequent evidence and gates. |
| A-02 | [Confirmed scope] Full 28-FR capability scope means core GA plus default-off Tier C pilots, preserving PRD tiering and feature flags. | Pilots are included in scope but do not block core GA or become enabled by scope approval. |
| A-03 | [Assumption] The frozen inventory is authoritative for detailed criteria and stable requirement IDs; this document references it instead of rewriting 111 controls. | Prevents duplicate or drifting requirements. |
| A-04 | [Assumption] The original canonical G-01…G-30 table is not currently recoverable from allowed project sources; only explicitly evidenced specialist/consolidated mappings may be stated. | Exact label crosswalk requires user-supplied table; no need to block capability planning. |
| A-05 | [Assumption] “Delivered” means wired end-to-end, authorized, persisted/externally confirmed where applicable, observable and tested—not an artifact, mock, route stub or partial code change. | Governs closure claims and acceptance reporting. |
| A-06 | [Assumption] Provider integrations remain unavailable unless the institution names the provider, grants entitlements/credentials and approves the test environment. | LIVE behavior and provider-backed acceptance cannot be claimed until supplied. |
| D-01 | DEC-01 — meeting platforms/languages, jurisdictional consent, audio/transcript retention/deletion. | Blocks recording/transcription scope until Legal/Security approval. |
| D-02 | DEC-02 — target CRM/email/calendar, authoritative fields, write scope, retry/reconciliation owner. | Blocks production CRM automation and reliable provider acceptance. |
| D-03 | DEC-03 — ranking weights, signal freshness, DNC precedence and meaningful-touchpoint definition. | Blocks prioritization policy tuning and valid M-03 claims. |
| D-04 | DEC-04 — product universe, data entitlements, suitability owner, hard-stop/override matrix, KYC freshness. | Blocks Epic 3 release. |
| D-05 | DEC-05 — Islamic design partner, SSB, screening standards, zakat method and wording. | Blocks Epic 4 pilot. |
| D-06 | DEC-06 — entity/custodian coverage, entitlement matrix, extraction quality bar. | Blocks Epic 5 pilot. |
| D-07 | DEC-07 — retention window/definition, matched method and baseline sample. | Blocks retention success claims, not base product functionality. |
| D-08 | DEC-08 — mobile OS/device, sensitive caching and approval requirements. | Blocks mobile release decision. |
| D-09 | Proposed canonical brief contract `response.brief.sections`. | Pending technical freeze by architecture owner; requirements only. |
| D-10 | Exact G-register row text and mappings. | Pending user-provided original register; no invented mappings in this version. |

## 10. Terminology

| Term | Definition |
|---|---|
| RM | Relationship Manager; authorized human user responsible for client relationship actions. |
| Core GA | General-availability scope for Epics 1–3; Epic 3 is P1 and must not delay P0 launch. |
| Tier A | Core P0 / GA-blocking set as defined in frozen inventory §12.2. |
| Tier B | P1 scope required for GA of Epics 1–3, but not a P0 launch blocker. |
| Tier C | Feature-flagged Epic 4–5 pilot scope; not a core-GA blocker. |
| Tier D | PRD out-of-scope, non-goals, open decisions and risks; never count as feature gaps. |
| D5 | Persistent Client Memory & Relationship Graph used by copilot context and cross-skill workflows. |
| Provenance | Verifiable source identity, record/entitlement, timestamp/as-of and derivation status for a material statement. |
| LIVE / FIXTURE / UNAVAILABLE | LIVE means actual authorized provider result; FIXTURE means synthetic/test-only data clearly isolated; UNAVAILABLE means no valid data. These states must never be conflated. |
| Copilot | Single orchestrating agent using persistent client context and workflow skills; prepares/ranks/drafts/explains while RM approves client-facing or system-writing actions. |
| Acceptance evidence | Reproducible test result, trace, readback or approval artifact proving a requirement; not an implementation claim or demo screenshot alone. |

---

**Phase-1 disposition:** Alan's full-scope approval is recorded above. Requirements handoff is complete; product design may proceed under the lead's phase chain, followed by architecture/contract freeze and delivery-batch planning. Preserve existing data, keep pilots default-off, retain Tier D exclusions and external production/compliance gates. This document does not certify implementation, authorize live side effects, enable pilots, or approve production deployment.

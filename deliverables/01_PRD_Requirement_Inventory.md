# PRD v1.1 Requirement Inventory — Next-Generation RM Workbench

**Deliverable 01 · Requirements side only (no code audit)**
**Analyst:** Xu Qingchu (许清楚), Requirements Analyst
**Audit:** PRD-vs-implementation gap audit, Phase 1
**Source of truth:** `RM_Workbench_PRD.docx`, v1.1, November 2026, "Product Requirements Document · V1.1 — Next-Generation RM Workbench — The AI Copilot for the Entire Wealth Advisory Day", Status: *Proposed for engineering/design estimation*, Scope: V1 (12-month roadmap), Banking & Wealth Management.

---

## 0. Method, notation and counting rules

### 0.1 Sources actually read

| Item | Detail |
|---|---|
| Authoritative PRD | `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_PRD.docx` (NOT re-opened, per instruction) |
| Lossless plain-text extraction | `/tmp/prd_full.txt` — 308 lines, 39,560 chars — read in full |
| Structure tree | `/tmp/prd_structure.json` — `effective_mode: full`, `pagination.has_more: false`, 193/193 nodes: 39 headings, 142 paragraphs, 12 tables, 17 numbering lists — used to cross-check row/paragraph counts |
| Codebase | NOT inspected. This document contains zero claims about the implementation. |

The structure tree confirms the plain-text extraction is complete and that no table row was lost. All 12 tables were cross-checked against the plain text; all row counts below are derived from the structure tree, not from eyeballing the text.

### 0.2 Notation

| Marker | Meaning |
|---|---|
| `FR-xx`, `D0`–`D5`, `FR-4.x`, `FR-5.x` | **PRD-native IDs**, reproduced verbatim. |
| `B-`, `NFR-`, `GOV-`, `INT-`, `M-`, `TEL-`, `GRD-`, `GATE-`, `C-`, `OOS-`, `NG-`, `DEC-`, `OBJ-`, `WF-`, `E-`, `A-`, `N-` | **[INVENTORY ID]** — assigned by this analysis to PRD table rows / unnumbered paragraphs that the PRD does not itself number. Frozen for this audit (Iron Law 3: contracts must not drift). |
| **[INFERENCE]** | A statement that is NOT literally in the PRD; derived from explicit PRD text. The derivation is always shown. |
| **[DECOMPOSED]** | One PRD paragraph split into atomic testable controls. The un-decomposed PRD statement is preserved. |
| `Dependency` | A foundational/gating item that is not an end-user feature but blocks one or more features. |
| `P0 / P1 / P2` | PRD-declared priority where present; otherwise assigned by epic/scope tie and tagged **[INFERENCE]**. |

### 0.3 Counting rule (important for the total)

One discrete requirement/control = one PRD-numbered FR, one PRD dependency, one **data row** of a PRD requirements table, one numbered governance/telemetry/objective paragraph, one atomic guardrail clause, or one rollout phase. **Header rows are never counted.** Where a PRD paragraph contains several independent "must" clauses, it is decomposed only where explicitly tagged **[DECOMPOSED]**, and an alternative non-decomposed total is also given (§10).

Duplicate-restatement control (Iron Law 1 — simplicity, no duplicate implementations): normative statements repeated across sections are **folded into one ID**, never double-counted. Specifically:

- §1.1 "Product principle" → folded into `C-09` / `FR-20`, not a separate requirement.
- §5 Epic 4 "Positioning" table → folded into `C-18` and `FR-4.x` ACs, not a separate requirement.
- §13 risk mitigations ("stage-level kill switches", "leakage tests as hard release gate", "node-level entitlements in copilot context assembly") → folded into `C-11`, `C-17`, `GATE-03`, `GOV-07`, not separately counted.
- §1.4 V1 objectives and §2.2 Core V1 Workflows → definitional/overlapping with the FRs and the copilot checklist; listed in §15 as supplementary, not counted.
- §7 NFR "Mobile" and §5 `FR-21` overlap by design but are kept as two distinct testable controls (one functional, one non-functional).

### 0.4 Compliance with the four global iron laws

| Law | Application to this deliverable |
|---|---|
| 1 Simplicity first | Single canonical ID per requirement; restatements folded in; no parallel inventories. |
| 2 Chinese comments at critical points only | No code is produced here. This is a requirements contract; no line-by-line commentary. |
| 3 Contracts frozen | Every ID, source section and acceptance condition below is a frozen contract for Phases 2–3. Downstream audit must reference these IDs, not invent new ones. |
| 4 Deliverables on disk | This file is written to `deliverables/01_PRD_Requirement_Inventory.md`. |

---

## 1. Evidence classification: research findings vs planning assumptions/targets

The PRD itself draws this line twice:

> "Evidence base: Phase 1 user personas, pain points and AI priorities; Phase 1 market-gap findings. **RICE reach/effort values and numeric targets are planning assumptions, not research findings.**" (PRD front matter, extraction line 41)

> "Values are **initial planning assumptions** to be replaced after technical discovery and pilot sizing." (§4.1, line 93)

> "…supports a 15–20% relative retention improvement for AI-user cohorts (**a validation target, not a guaranteed outcome**)." (§1.1, line 44)

### 1.1 Research-derived evidence (observed, attributable to Phase 1)

| ID | PRD statement | Source | Attribution in PRD |
|---|---|---|---|
| E-01 | RMs lose 20–30% of their time to fragmented data; engage reactively and miss opportunities; spend 2–3 hours/day on administration | §1.2 | "Phase 1 research found…" |
| E-02 | Meeting Intelligence, Intelligent Prioritization, Product Recommendation ranked highest-value AI capabilities | §1.2 | "Research ranked…" |
| E-03 | Competitive gaps: native meeting intelligence; mid-market pricing ($100–200 vs Salesforce $325–475 per user/month); Next-Best-Conversation guidance rather than product-only recommendations | §1.2, §1.3 | "Competitive analysis identified…" / "Phase 1 market-gap findings" |
| E-04 | Two personas, their book sizes/needs and V1 design implications (Senior Private Wealth RM: 50–150 HNWI clients, $50M–$500M AUM; Mass Affluent RM: 100–300 clients, $20K–$2M per client) | §2.1 | Explicit "Source: Phase 1 user research." |
| E-05 | Fragmented AI point features force the RM to act as the integration layer — copying context between tools | §1.2 | "The v1.1 **architecture review** additionally found…" — a documented v1.1 review finding, NOT Phase 1 user research |
| E-06 | Customers: banks/wealth firms with 1,000–10,000 RMs | §1.3 | Stated as target-customer definition; no research citation (treated as a planning/segmentation statement, not an observed finding) |

### 1.2 Planning assumptions, hypotheses and targets (NOT observed facts)

| ID | PRD statement | Source | Why it is an assumption/target |
|---|---|---|---|
| A-01 | RICE reach/impact/confidence/effort values; scores 48.0 / 36.0 / 33.6 / 31.5 / 28.0 / 13.2 / 9.0; effort 3/5/5/4/3/5/4 | §4.1 | Explicit: "initial planning assumptions to be replaced after technical discovery and pilot sizing" |
| A-02 | All numeric success targets | Front matter, §1.4, §3, §10.1 | Explicit: "numeric targets are planning assumptions, not research findings" |
| A-03 | 4–6 hours/RM/week saved; 15–20% relative retention improvement | §1.1 | "a validation target, not a guaranteed outcome" |
| A-04 | Mid-market packaging/pricing hypothesis | §1.3 | PRD literally calls it a "hypothesis" |
| A-05 | Two metric rows demand a baseline BEFORE the target is valid: "Pilot baseline first; validate approx. 20 → 2 min goal"; "Baseline first; target −70%" | §10.1 M-08, M-10 | Targets are conditional on an unmeasured baseline |
| A-06 | 12-month rollout, 4 quarters, all gate timing | §11, Figure 2 | A delivery plan |
| A-07 | Illustrative effort claims inside user stories ("save 15–30 minutes", "about two minutes rather than 15", "about two minutes rather than 20") | §5 Epic 1.3 / 2.2 / 3.1 user stories | Narrative justification, not measured data |
| A-08 | NFR thresholds (<10s p95, <5s p95, 1,000 concurrent users, 99.5% monthly uptime, SOC 2 attestation, WCAG 2.1 AA) | §7 | Acceptance targets / programs to achieve, not measured current state |
| A-09 | §14 "Decisions Required Before Build/Launch" — 8 open decisions | §14 | Explicitly unresolved; assumptions cannot yet be closed |

### 1.3 Numeric target register (all flagged)

| ID | Number | PRD source | Classification |
|---|---|---|---|
| N-01 | 4–6 hours/RM/week effort reduction | §1.1 | **[TARGET]** planning / validation |
| N-02 | +15–20% relative retention, AI-user cohort | §1.1, §10.1 M-07 | **[TARGET]** validation target, no causality claim allowed; matched/book-adjusted comparison required |
| N-03 | 45 → 10 min meeting preparation | §1.4 OBJ-01, §10.1 M-01 | **[TARGET]** |
| N-04 | 20 → 5 min post-meeting administration | §1.4 OBJ-02, §10.1 M-02 | **[TARGET]** |
| N-05 | 4–6 → 8–12 meaningful touchpoints/client/quarter | §1.4 OBJ-03, §10.1 M-03 | **[TARGET]** |
| N-06 | 60% monthly brief adoption within 6 months | §1.4 OBJ-04, §10.1 M-04 | **[TARGET]** |
| N-07 | ≥70% of meeting-prep + outreach workflows via copilot single entry point by GA | §1.4 OBJ-05, §3, §10.1 M-05 | **[TARGET]** also a copilot qualification property (`C-07`) |
| N-08 | ≥85% cross-skill task completion without manual stitching | §3, §10.1 M-06 | **[TARGET]** also `C-06` |
| N-09 | approx. 20 → 2 min product search | §10.1 M-08 | **[TARGET]** "Pilot baseline first" |
| N-10 | 100% Shariah screening coverage | §10.1 M-09 | **[TARGET]** v1.1 pilot |
| N-11 | −70% family reporting effort | §10.1 M-10 | **[TARGET]** "Baseline first" |
| N-12 | ≤10 clients in daily Top 10 | §5 FR-11 | **[HARD DESIGN CONSTRAINT]** not a target |
| N-13 | 90-day liquidity forecast window | §5 FR-5.3 | **[HARD DESIGN CONSTRAINT]** |
| N-14 | brief <10s p95; product search <5s p95 | §7 Performance | **[ACCEPTANCE TARGET]** |
| N-15 | 1,000 concurrent users | §7 Scale | **[ACCEPTANCE TARGET]** |
| N-16 | 99.5% monthly uptime | §7 Availability | **[ACCEPTANCE TARGET]** |
| N-17 | 12-month roadmap / Months 1–3, 4–6, 7–9, 10–12 | §11 | **[PLAN]** |
| N-18 | RICE scores and effort weights | §4.1 | **[PLANNING ASSUMPTION]** |
| N-19 | 20–30% time lost; 2–3 h/day admin | §1.2 | **[RESEARCH-DERIVED BASELINE]** observed |
| N-20 | $100–200 vs $325–475/user/month; 1,000–10,000 RMs | §1.2, §1.3 | **[MARKET FINDING / SEGMENT HYPOTHESIS]** |
| N-21 | 50–150 HNWI / $50M–$500M AUM; 100–300 clients / $20K–$2M | §2.1 | **[RESEARCH-DERIVED DESCRIPTOR]** |
| N-22 | 15–30 min saved; ~2 min vs 15 / ~2 min vs 20 | §5 user stories | **[ILLUSTRATIVE CLAIM]** |

> **Audit consequence:** a missing metric *target* is not, by itself, a functional gap. The audit should verify that the **measurement capability** (definitions, telemetry, comparison method, baseline handling) exists, not that a number has already been hit. §10.1 M-07 explicitly forbids causality claims from raw cohort differences; §10.1 M-08/M-10 explicitly require baselines first.

---

## 2. Functional Requirements (PRD Section 5)

### 2.1 Epic 1 — AI Meeting Intelligence (P0)

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-01 | Brief creation and access: generate on demand from a client/meeting page and from an eligible upcoming calendar event; resolve correct client/household; display client name, meeting time, data-as-of timestamp and generating RM. | P0 | Given an authorized RM and resolvable client, a brief returns within the §7 Performance NFR; ambiguous calendar attendees require explicit client selection and never auto-merge identities; unauthorized clients are not exposed. | §5 / Epic 1 / 1.1 (RICE rank 1) |
| FR-02 | Required brief content: portfolio/AUM + allocation summary; material changes and risk alerts; recent interactions and open actions; relevant entitled market news; proposed agenda tied to client context. | P0 | All five sections render when data exists; every material fact, alert and news item links to its source and timestamp; selecting a source opens the originating record/entitled source detail; generated agenda items are distinguishable from recorded facts; no news or portfolio fact is presented without provenance. | §5 / 1.1 |
| FR-03 | Partial data, regeneration and feedback: preserve available sections when a source fails; label missing/stale inputs; allow retry/regeneration; capture helpful/not-helpful feedback with reason. | P0 | A failed market-news feed does not block portfolio/agenda sections; missing data produces an explicit "unavailable" state, never inferred values; repeated generation creates an audited version without duplicating CRM records. | §5 / 1.1 |
| FR-04 | Consent and recording controls: require jurisdiction/policy-appropriate client consent before audio capture; present consent language; record method/timestamp; persistent recording indicator; pause/stop. | P0 | No audio is captured or transmitted before required consent; declined or withdrawn consent prevents/stops transcription and offers manual notes; consent and recording state changes are auditable; consent is NOT inferred from calendar acceptance. | §5 / 1.2 (RICE rank 2); depends D2 |
| FR-05 | Transcript and structured extraction: time-stamped, speaker-labelled transcript excerpts; extract decisions, action items (owner/due date where stated), client preferences, commitments, follow-up topics; RM correction/edit/delete with confidence and source timestamps. | P0 | Every extracted item links to its transcript evidence; unspoken owners/dates remain blank; low-confidence content is marked for review; deleted sensitive content is excluded from generated follow-ups subject to retention policy. | §5 / 1.2 |
| FR-06 | Failure recovery: handle audio loss, unsupported meeting format and transcription-provider failure without blocking manual notes. | P0 | Interruption displays the last confirmed transcript position and recovery state; retry does not create duplicate meetings/actions; failure never results in a fabricated "complete" transcript. | §5 / 1.2 |
| FR-07 | Unified post-meeting review: present proposed notes, CRM field changes, tasks, client preferences, email draft and eligible trade-ticket fields side by side with source evidence. | P0 | Nothing is written, sent or submitted before explicit RM confirmation; RM can accept individual items, edit them or reject all; the final review identifies who approved and when. | §5 / 1.3 (RICE rank 3) |
| FR-08 | CRM update and task creation: map accepted content to configured CRM interaction, preference, opportunity and task fields; use idempotency keys. | P0 | Preview shows old and proposed new values; confirmed updates appear in the correct client record; CRM outage queues or safely retries only with visible status and never reports success prematurely. | §5 / 1.3 |
| FR-09 | Follow-up email draft: draft in the RM's editable workflow using accepted decisions/actions only; include required disclosures; omit unapproved sensitive information. | P0 | Default state is draft, never sent; recipients are confirmed by the RM; edits and final send are attributable to the RM; withdrawing consent or rejecting an extracted item removes it from subsequent drafts. | §5 / 1.3 |
| FR-10 | Pre-filled trade-ticket handoff: where explicitly discussed and supported by entitled integrations, pre-fill product, account and amount fields and link back to meeting evidence. | P0 | Handoff requires current suitability status and all mandatory fields; AI cannot submit, approve or execute a trade; stale/missing suitability or account data blocks handoff with a clear reason. | §5 / 1.3; §6 B-02/B-09 |

### 2.2 Epic 2 — Intelligent Prioritization & Outreach (P0)

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-11 | Daily Top 10 and refresh: generate up to 10 authorized clients by the RM's local start of day; rerank on material new risk/opportunity/retention signals. | P0 | Default view contains no more than 10 unique clients; each has a rank, reason and last-updated timestamp; clients outside the RM's book, lacking permission, or under do-not-contact restrictions are excluded. | §5 / 2.1 (RICE rank 4) |
| FR-12 | Reason codes and evidence: classify as Risk, Opportunity and/or Retention; show main contributing signals/data sources; concise explanation rather than a bare score. | P0 | Selecting a reason opens one-click client detail and underlying evidence; stale signals are labelled; users can inspect why rank changed; no protected attribute is used as a ranking feature. | §5 / 2.1; §8 GOV-08 |
| FR-13 | RM control and learning: snooze, dismiss with reason, mark contacted, pin; capture outcome (contacted, meeting booked, no response, not relevant). | P0 | Actions persist and affect subsequent ranking according to published rules; dismissal is not silently treated as negative client intent; an audit trail distinguishes AI recommendation from RM action; all original evidence remains reviewable. | §5 / 2.1 |
| FR-14 | Grounded draft generation: from an approved reason code, use reason for contact, permitted portfolio facts, client-relevant conversation opener and selected channel/template. | P0 | Draft contains all three required content elements when data exists; factual statements link to evidence; unavailable facts are omitted rather than invented; message is fully editable before approval. | §5 / 2.2 (RICE rank 5) |
| FR-15 | Policy checks and approved send: apply do-not-contact, channel-consent, disclosure and restricted-content checks; RM editing and explicit approval before email/SMS send. | P0 | No auto-send occurs; blocked clients/channels cannot be sent through the workbench; sent/scheduled status, final content, approver and template/model version are logged; failed sends expose provider status and safe retry. | §5 / 2.2; §9 INT-06 |

### 2.3 Epic 3 — Enhanced Product Recommendation (P1; depends on D3)

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-16 | Query interpretation and search: accept NL queries such as "ESG bond funds, 3%+ yield, conservative 55-year-old, $200K"; display interpreted filters and allow RM correction before/after search. | P1 (depends D3) | Results return within the §7 Performance NFR; displayed filters reflect the actual query executed; only entitled, currently available products are returned; client-specific searches use the selected client's current suitability profile. | §5 / 3.1 (RICE rank 7); §2.3 D3 |
| FR-17 | Result explanation and comparison: product identifier, key risk, yield/return metric with as-of date and definition, fees, liquidity, minimum investment, verified ESG attributes where requested, suitability status and source. | P1 | RM can sort/filter and compare selected products; yield is not labelled guaranteed unless the source product terms support it; no-result searches suggest editable filter relaxation without silently dropping suitability constraints. | §5 / 3.1 |
| FR-18 | Red/Yellow/Green assessment: Green = no detected conflict, Yellow = missing data or review required, Red = detected conflict/prohibition, with rule/signal-level justification and data timestamps. | P1 | Every rating shows contributing factors and conflicts; missing/expired KYC or risk profile cannot produce Green; Green is explicitly labelled "pre-screen, not compliance approval"; assessment recalculates when material inputs change. | §5 / 3.2 (RICE rank 6) |
| FR-19 | Overrides and hard stops: authorized RM may override soft Yellow/Red warnings with a mandatory reason where policy permits; hard regulatory/product prohibitions are never overridable. | P1 | Override captures original rating, rationale, user, timestamp and final action; prohibited trades remain blocked; all assessments and overrides are available to compliance audit. | §5 / 3.2; §8 GOV-06 |

### 2.4 Cross-Cutting Functional Requirements

> **Priority note [INFERENCE]:** the PRD does not assign an explicit P-level to FR-20…FR-22. They are marked **P0 (V1-wide)** because §4.1 makes Epics 1–2 P0 and these three govern every P0 artifact. FR-21 is qualified by the PRD's own carve-out.

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-20 | Universal human review: every AI-generated brief section, note, CRM write, message, recommendation and ticket handoff has an identifiable review state and approver where applicable. | P0 (V1-wide) **[INFERENCE]** | For each of the six artifact classes, a persisted review state and approver identity/timestamp is queryable; no artifact transitions to written/sent/submitted without it. | §5 Cross-Cutting; §8 GOV-01; §1.1 |
| FR-21 | Mobile parity for defined tasks: client lookup, view briefs, inspect daily priorities, edit/approve outreach on mobile. | P0 (V1-wide) **[INFERENCE]** | The four defined tasks work on mobile under the same RBAC/consent controls (§7 Mobile), secure sessions and no uncontrolled sensitive-data caching; transcription and trade handoff may remain desktop-only in V1 if policy requires. | §5 Cross-Cutting; §7 Mobile; §14 |
| FR-22 | Administration: authorized admins configure field mappings, ranking/reason-code policies, templates/disclosures, consent rules and integration credentials without code deployment. | P0 (V1-wide) **[INFERENCE]** | Each of the five configuration classes is editable at runtime; every change is versioned and appears in the tamper-evident audit log (§7 Auditability / GOV-05). | §5 Cross-Cutting; §8 GOV-05 |

### 2.5 Epic 4 — Islamic Wealth & Shariah-Compliant Advisory (v1.1, P1 pilot)

> **Positioning constraint (folded into `C-18` and the FR-4.x ACs; not separately counted):** "the copilot is a calculation and evidence assistant, never a fatwa issuer. All methodologies, screenings and zakat treatments are configurable rule packs reviewed by the institution's Shariah Supervisory Board (SSB)." — §5 Epic 4, positioning table.

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-4.1 | Shariah preference profile and compliant product universe: store client/household Shariah sensitivity in client memory and propagate automatically to search, rebalancing and outreach; apply business-activity and configurable financial-ratio screens with per-criterion evidence; drift monitoring re-screens holdings and raises Risk reason codes with SSB-policy-required actions. | P1 pilot | No non-compliant product appears in any recommendation surface for a Shariah-sensitive client; every screened instrument shows pass/fail per criterion with source and as-of date; products without current SSB evidence cannot be marked compliant. | §5 / Epic 4; §6 B-11; §9 INT-08 |
| FR-4.2 | Zakat and purification copilot: configurable methodology (e.g. AAOIFI vs local rulings), nisab and hawl tracking, income-purification calculations; proactively schedule zakat conversations ahead of hawl anniversaries. | P1 pilot | Outputs itemize zakatable vs excluded assets, methodology applied, nisab source/date and lunar/solar convention; every output is labelled "estimate for discussion — confirm with your Shariah advisor"; purification ratios are sourced and dated. | §5 / Epic 4 |
| FR-4.3 | Shariah-compliant proposal and evidence pack: proposals auto-include screening evidence per holding, SSB approval references, purification and zakat-treatment notes. | P1 pilot | No proposal can be finalized for a Shariah-sensitive client without a complete, versioned evidence pack archived for audit. | §5 / Epic 4 |

### 2.6 Epic 5 — Family Office & Multi-Generational Support (v1.1, P1/P2 pilot)

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| FR-5.1 | Household and entity consolidation: model trusts, foundations, holding companies and family members as a permissioned graph; document intelligence extracts structures for RM verification; consolidate holdings across custodians and currencies with look-through exposure. | P1 pilot **[INFERENCE]** (epic heading is "P1/P2 pilot") | AI-extracted structures require RM confirmation before becoming canonical; family-level exposure reconciles to custodian totals within tolerance; intra-family entitlements are enforced in **copilot context assembly**, not only in UI; entitlement tests are a hard release gate. | §5 / Epic 5; §6 B-12; §11 GATE-03 |
| FR-5.2 | Family governance and succession copilot: per-attendee entitled meeting packs; track commitments across meetings; model succession/transfer scenarios with jurisdiction caveats; track next-gen engagement feeding family-level retention reason codes. | P1 pilot **[INFERENCE]** | Each attendee class receives only its entitled pack version; scenarios are labelled illustrative with itemized assumptions. | §5 / Epic 5 |
| FR-5.3 | Alternatives and capital-call orchestration: track unfunded commitments; forecast capital-call windows from GP patterns and parsed notices; feed 90-day liquidity forecasts into prioritization triggers. | **P2** (PRD-declared) | Notices parsed with RM verification; forecast-vs-actual accuracy tracked; liquidity alerts appear as Risk reason codes with evidence. | §5 / Epic 5 |

**Functional subtotal: 28** (22 core FR-01…FR-22 + 3 Epic 4 + 3 Epic 5).

---

## 3. Foundational Dependencies (PRD Section 2.3)

All are priority **Dependency** — they are not user-facing features, and a missing dependency invalidates the features that rely on it.

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| D0 | Identity, tenant isolation, RBAC, audit and AI-provider controls. | Dependency (required by **every** epic) | Any epic fails closed if tenant/role authorization or the audit record is missing; AI-provider controls enforce zero retention; server-side authorization and prompt revocation after role/book changes (§9 INT-10). | §2.3; §7 Security/Auditability; §8 GOV-02 |
| D1 | Client, portfolio, CRM and calendar integration. | Dependency (Epics 1 and 2) | Inbound authoritative data carries IDs and as-of timestamps; no cross-client identity guessing; ambiguous calendar attendee matching requires user resolution. | §2.3; §9 INT-01/02/04/05 |
| D2 | Consent and recording policy service. | Dependency (**before transcription**) | No audio capture/transmission without policy-appropriate consent; FR-04 cannot operate without D2; declined/withdrawn consent stops capture and preserves the consent audit. | §2.3; §5 FR-04; §14 DEC-01 |
| D3 | Entitled market/product data plus current KYC/suitability data. | Dependency (Epic 3) | Current-version product evidence is present; stale/expired KYC cannot produce a Green rating and blocks ticket handoff. | §2.3; §5 FR-16…FR-19; §9 INT-07 |
| D4 | Ranking/outcome telemetry. | Dependency (**before optimizing prioritization or retention claims**) | TEL-04/05/08 event groups and version/correlation tagging exist before any ranking tuning or retention claim is made. | §2.3; §10.2; §10.1 M-07 |
| D5 | Client Memory & Relationship Graph (v1.1): persistent per-client context and family/entity graph. | Dependency (**Q1 critical path alongside D0/D1**; required by copilot orchestration and Epics 4 and 5) | Present as the **Context** layer of the five-layer architecture; ships with the E1 alpha in Months 1–3 alongside the Copilot Core skeleton; node-level entitlements enforced in context assembly. | §2.3; §3; §11 GATE-01; §5 FR-5.1 |

> **Audit note:** D5 is the single most load-bearing dependency for the "is there a copilot?" question. It is explicitly on the **Q1** critical path, not a later-phase enhancement.

---

## 4. Boundary and Exception Behaviour (PRD Section 6)

The PRD §6 table contains **12 data rows** (structure tree: table idx 6, `row_count: 13` including header). See §14 D-1 for the discrepancy with the "11" in the task brief.

| ID | Exception scenario | Priority | Required behaviour (testable condition) | Source |
|---|---|---|---|---|
| B-01 | Source unavailable or stale | P0 | Show partial output with per-section status/as-of time; never invent or silently substitute data. | §6 row 1; FR-02/03 |
| B-02 | Conflicting client/portfolio records | P0 | Flag conflict and link both sources; block suitability/trade handoff until authoritative resolution. | §6 row 2; FR-10 |
| B-03 | Client declines/withdraws recording consent | P0 | Do not start, or stop capture; offer manual notes; preserve consent audit. | §6 row 3; FR-04 |
| B-04 | Low AI confidence or insufficient evidence | P0 | Label item, require explicit review, and suppress unsupported client-facing assertions. | §6 row 4; GOV-03 |
| B-05 | CRM/email/SMS provider outage | P0 | Keep editable draft, expose pending/failed status, use idempotent retry; never show false success. | §6 row 5; FR-08/09/15 |
| B-06 | No high-priority clients | P0 | Return an empty state with criteria and last evaluation time; do not fill Top 10 with weak leads. | §6 row 6; FR-11 |
| B-07 | Do-not-contact/channel opt-out | P0 | Exclude from outreach and block send even if ranked for risk/retention. | §6 row 7; FR-11/15 |
| B-08 | No suitable product | P1 | Show no-result explanation; never relax a hard suitability filter automatically. | §6 row 8; FR-17/19 |
| B-09 | Suitability data missing/expired | P1 | Yellow at best; block any trade-ticket handoff requiring current assessment. | §6 row 9; FR-18 |
| B-10 | Model/service failure | P0 (V1-wide) | Fall back to existing search/manual workflow and show status; preserve user edits. | §6 row 10; GOV-07 |
| B-11 | Shariah-sensitive client, non-compliant candidate | P1 pilot | Exclude by construction; never surface with a disclaimer as a workaround. | §6 row 11; FR-4.1 |
| B-12 | Intra-family entitlement boundary | P1 pilot | Copilot context assembly filters per node entitlement; no cross-entity leakage in any AI artifact. | §6 row 12; FR-5.1; GATE-03 |

---

## 5. Non-Functional Requirements (PRD Section 7)

Structure tree: table idx 7, `row_count: 12` → **11 areas**. Priority is assigned by scope tie; pre-production gates are marked Dependency **[INFERENCE]**.

| ID | Area | Priority | Requirement / acceptance target | Source |
|---|---|---|---|---|
| NFR-01 | Performance | P0 | Pre-meeting brief <10s p95 and product search <5s p95 under normal dependent-service conditions; progressive status for longer jobs; dependency latency recorded separately. | §7 |
| NFR-02 | Scale | P0 | 1,000 concurrent users at launch configuration without breaching p95 targets; tenant workload isolation and horizontal scaling tested at peak windows. | §7 |
| NFR-03 | Availability | P0 | 99.5% monthly uptime excluding contracted maintenance; degraded third-party capabilities fail gracefully rather than take down core client lookup. | §7 |
| NFR-04 | Security | Dependency (pre-production; GATE-01 sign-off) | SOC 2 program/attestation target; TLS in transit and strong encryption at rest; enterprise RBAC, least privilege, tenant isolation, session timeout, secrets management, periodic access review. | §7; §2.3 D0; §11 GATE-01 |
| NFR-05 | Privacy and residency | Dependency (pre-production; GATE-01 sign-off) | Configurable EU/US/APAC residency (plus GCC/Malaysia/Indonesia options for Epic 4); documented subprocessors and cross-border flows; retention/deletion/legal-hold policies apply to audio, transcript, prompts, outputs and logs. | §7; §8 GOV-02; §11 GATE-01 |
| NFR-06 | Auditability | Dependency | Immutable/tamper-evident logs for consent, source versions, AI output, RM edits/approvals, writes/sends, overrides, model/template versions and administrative changes. | §7; §8 GOV-05 |
| NFR-07 | AI explainability | P0 | Material recommendations show source data, timestamps and concise user-facing rationale; no private chain-of-thought or unrelated client data exposed. | §7; §8 GOV-03 |
| NFR-08 | Mobile | P1 **[INFERENCE]** (gated on §14 "Before mobile release" decision) | Client lookup, briefs, priorities and outreach use the same RBAC/consent controls; secure sessions and no uncontrolled sensitive-data caching. | §7; FR-21; §14 DEC-08 |
| NFR-09 | Accessibility | P0 | New V1 interfaces target WCAG 2.1 AA; keyboard operation; readable status labels; non-color-only Red/Yellow/Green indicators. | §7 |
| NFR-10 | Observability | Dependency (D4 / §10) | Correlated technical, AI-quality and business telemetry with PII-minimized logs; alerts for latency, error rate, provider failure, data staleness, unusual block rates. | §7; §10.2 |
| NFR-11 | Recoverability | Dependency (before production) | Defined backup/restore and disaster-recovery objectives before production; no loss of accepted CRM updates or approved sends during retry/recovery. | §7; §6 B-05 |

---

## 6. AI Governance and Responsible Operation (PRD Section 8)

Structure tree confirms **8 paragraphs** under Heading 8 (paragraph indices 145–152).

| ID | One-line statement | Priority | Condensed acceptance criterion / testable condition | Source |
|---|---|---|---|---|
| GOV-01 | Human-in-the-loop: RM review mandatory for all external communications, CRM updates, recommendations and trade handoffs. | P0 | V1 contains no autonomous client action or execution; every one of the four artifact classes has an enforced approval gate before it becomes external/system-writing. | §8; §1.1; FR-20; §1.5 |
| GOV-02 | Zero provider retention/training: contractual and technical controls so LLM providers cannot retain or train on client data. | Dependency (vendor/security review) | Provider logging disabled where possible; prompts minimized; controls verified during vendor/security review; no automatic model training on client/RM data (§12). | §8; §12 |
| GOV-03 | Grounding and explainability: show source records, data-as-of timestamps, material factors and confidence/limitations. | P0 | Explanations are faithful summaries, not unsupported rationalizations; no material AI output without provenance; no private chain-of-thought. | §8; NFR-07 |
| GOV-04 | Override and feedback: RMs can edit, reject, dismiss and permitted-override outputs with structured reasons. | P0 | Feedback is reviewed before tuning and never automatically alters production behavior; structured reason is captured for every override/dismiss. | §8; FR-13/19 |
| GOV-05 | Model, prompt and rule-pack change management: version models, prompts, templates, ranking policies and Shariah rule packs. | P0 | Evaluate on approved representative test sets before release; SSB sign-off required for Shariah rule-pack changes; rollback supported. | §8; FR-22; NFR-06 |
| GOV-06 | Compliance ownership: Legal/compliance approves consent language, disclosures, recording/retention rules, suitability logic and override policy by jurisdiction before launch. | Dependency (before launch) | Five named approval artifacts exist and are jurisdiction-scoped before launch; GATE-03 re-checks ratings/overrides approval. | §8; §11 GATE-01/GATE-03 |
| GOV-07 | Monitoring and kill switch: track hallucination/unsupported-fact reports, extraction correction rates, blocked sends, suitability conflicts and drift. | P0 | Authorized operators can disable **a model feature or a single orchestration stage** while preserving manual workflows and audit records; the five monitored quantities are actually collected. | §8; §13 "stage-level kill switches"; §6 B-10 |
| GOV-08 | Fairness and data minimization: no protected attributes for contact ranking; inputs restricted to necessary entitled data. | P0 | Disparate ranking/outcome patterns monitored where lawful and appropriate; no protected attribute appears as a ranking feature. | §8; FR-12 |

---

## 7. Integration Requirements (PRD Section 9)

Structure tree: table idx 8, `row_count: 11` → **10 system rows**. See §14 D-2 for the discrepancy with the "11 systems" in the task brief. `INT-11` is the unnumbered closing paragraph — the 11th discrete integration control.

| ID | System | Data / direction | Priority | Functional requirement and failure rule (testable condition) | Source |
|---|---|---|---|---|---|
| INT-01 | Core banking | Client identity, households, accounts, balances; inbound | P0 | Authoritative IDs and as-of timestamps; no cross-client identity guessing. | §9 row 1 |
| INT-02 | Portfolio management | Holdings, allocation, performance, risk; inbound | P0 | Client/household aggregation and stale/conflict labeling. | §9 row 2 |
| INT-03 | Market data | Prices, news and licensed fundamentals; inbound | P0 | Respect entitlements, attribution and source timestamps; unavailable feed does not block unrelated sections. | §9 row 3 |
| INT-04 | CRM | Contacts, interactions, preferences, tasks; bidirectional | P0 | Configurable field mapping, old/new preview, idempotent writes, visible sync status. | §9 row 4 |
| INT-05 | Calendar | Outlook/Google meeting metadata and attendee hints; inbound | P0 | Least-privilege scopes; ambiguous client matching requires user resolution. | §9 row 5 |
| INT-06 | Email/SMS | Draft handoff and RM-approved send; outbound | P0 | Consent/DNC/disclosure checks; final content and provider status logged; no background autonomous send. | §9 row 6 |
| INT-07 | Product/suitability source | Product terms, fees, availability, KYC/risk profile, restrictions; inbound | P1 (Epic 3, D3) | Current-version evidence required for Epic 3; stale data limits rating and blocks ticket handoff. | §9 row 7 |
| INT-08 | Shariah rule/source data (v1.1) | Screening ratios, SSB approvals, purification ratios; inbound | P1 pilot | Versioned rule packs with SSB sign-off; stale evidence blocks "compliant" labeling. | §9 row 8 |
| INT-09 | Custodian/entity sources (v1.1) | Multi-custodian holdings, trust/entity documents; inbound | P1 pilot | Reconciliation tolerances and per-node entitlements enforced before consolidation. | §9 row 9 |
| INT-10 | Identity/administration | SSO/user, role, book assignment, tenant policy; inbound | P0 | Server-side authorization; prompt revocation after role/book changes. | §9 row 10 |
| INT-11 | Cross-cutting integration contract (unnumbered closing paragraph) | Freshness SLAs, API limits, authoritative-source ownership | Dependency | Finalized during technical discovery **and surfaced in each client-facing data-as-of label**; testable by inspecting any client-facing data-as-of label for SLA/ownership provenance. | §9 closing paragraph |

---

## 8. Analytics and Success Measurement (PRD Section 10)

### 8.1 Success metrics (§10.1) — structure table idx 9, 10 data rows

| ID | Metric | Definition | V1 target / method | Priority | Testable condition | Source |
|---|---|---|---|---|---|---|
| M-01 | Meeting preparation time | Active RM preparation minutes per eligible meeting; time-motion study plus workflow timestamps | **45 → 10 min**; comparable meeting types | P0 | Instrumentation produces comparable-meeting-type prep durations; baseline and post-launch values reportable. | §10.1; §1.4 |
| M-02 | Post-meeting administration | Minutes from meeting end to approved notes/follow-up completion, excluding client wait time | **20 → 5 min** | P0 | Durations computable from approval timestamps (FR-07). | §10.1; §1.4 |
| M-03 | Meaningful touchpoints | Completed two-way interactions or attended meetings per client per quarter; drafts and failed sends excluded | **4–6 → 8–12** | P0 | Definition enforced: drafts and failed sends are excluded from the count. | §10.1; §1.4 |
| M-04 | Brief adoption | Monthly active enabled RMs generating/viewing ≥1 brief ÷ monthly active enabled RMs with access | **60% within 6 months**; also track briefs per eligible meeting | P0 | Numerator/denominator computed from TEL-01; both measures reported. | §10.1; §1.4 |
| M-05 | Copilot orchestration rate (v1.1) | % of meeting-prep and outreach workflows completed through the copilot single entry point | **≥70% by GA** | P0 | Computable from TEL-08 `copilot_workflow_*` events; no chat-volume proxy accepted. | §10.1; §1.4; §3 |
| M-06 | Cross-skill task completion (v1.1) | Multi-step orchestrations completed without RM manual stitching | **≥85%** | P0 | Computable from TEL-08 `manual-stitch interventions` and workflow completion events. | §10.1; §3 |
| M-07 | Client retention | Retained clients/assets for enabled AI-user cohort over an agreed observation window | **Validate +15–20% relative improvement** with matched/book-adjusted comparison; no causality claims from raw cohort differences | P1 **[INFERENCE]** | A matched/book-adjusted comparison method exists (§14 DEC-07); the product makes no causality claim from raw cohort differences. | §10.1; §1.1 |
| M-08 | Product-search efficiency | Time from submitted NL query to saved/selected candidate | **Pilot baseline first; validate approx. 20 → 2 min goal** | P1 | Baseline is captured before the goal is asserted; TEL-07 provides timestamps. | §10.1 |
| M-09 | Shariah screening coverage (v1.1) | % of Shariah-sensitive client holdings with current screening evidence | **100%** | P1 pilot | Every Shariah-sensitive holding has a current, dated SSB evidence record; TEL-09 supports the count. | §10.1 |
| M-10 | Family reporting effort (v1.1) | Time to prepare consolidated family-level reporting | **Baseline first; target −70%** | P2 pilot **[INFERENCE]** | Baseline is captured before the target is asserted. | §10.1 |

### 8.2 Required telemetry (§10.2) — structure confirms 10 numbered paragraphs (indices 160–169)

| ID | Event group / rule | Priority | Condensed testable condition | Source |
|---|---|---|---|---|
| TEL-01 | `brief_requested / generated / viewed`, source completeness, latency, regeneration, feedback | P0 | All named events emitted; source-completeness and latency fields populated; regeneration and feedback distinguishable. | §10.2 item 1 |
| TEL-02 | `consent_shown / accepted / declined / withdrawn`, recording start/stop/failure | P0 | All named events emitted; **no sensitive audio in analytics**. | §10.2 item 2 |
| TEL-03 | `transcript_item_accepted / edited / rejected`, extraction correction reason | P0 | All named events emitted with a structured correction reason. | §10.2 item 3 |
| TEL-04 | `crm_update_previewed / approved / succeeded / failed`, `email_draft_edited / approved / sent / failed`, `ticket_handoff_blocked / completed` | P0 | All named events emitted; blocked vs completed ticket handoff distinguishable; no false-success event. | §10.2 item 4 |
| TEL-05 | `priority_list_viewed`, reason-code detail opened, snooze/dismiss/contact outcome, time-to-contact | P0 | All named events emitted with outcome and time-to-contact. | §10.2 item 5 |
| TEL-06 | `outreach_generated / edited / approved / blocked / sent`, response/meeting outcome | P0 | All named events emitted; blocked sends distinguishable; outcome captured. | §10.2 item 6 |
| TEL-07 | `product_query / filter_corrected / results_viewed / no_result`, `suitability_rating / override / hard_stop` | P1 | All named events emitted; hard_stop distinguishable from override. | §10.2 item 7 |
| TEL-08 | `copilot_workflow_started / stage_approved / completed / abandoned`, **skill invocation chain**, **manual-stitch interventions** | P0 (copilot qualification evidence) | Full orchestration lifecycle, skill invocation chain and manual-stitch interventions are emitted; this is the only basis for M-05/M-06 and `C-12`. | §10.2 item 8; §3; §7 Observability |
| TEL-09 | `shariah_screen_run / drift_alerted`, `zakat_estimate_generated / confirmed_by_advisor`, `household_consolidated / entitlement_blocked` | P1 pilot | All named events emitted; entitlement_blocked is a hard-gate test signal. | §10.2 item 9 |
| TEL-10 | Model/prompt/template/rule-pack version, source timestamps and **tenant-safe correlation ID** on relevant events | Dependency (D4) | Every relevant event carries version, source timestamps and a tenant-safe correlation ID; PII-minimized per §7 Observability. | §10.2 item 10; §8 GOV-05 |

> **Count note:** items 1–9 are the **9 required telemetry event groups**; item 10 is a **cross-event tagging rule**. Both are discrete controls and both are counted.

### 8.3 Guardrails (§10.3) — **[DECOMPOSED]** from one paragraph

PRD verbatim: *"No increase in privacy incidents, unauthorized data exposure, non-consented recordings, unsuitable hard-stop bypasses, unapproved sends, Shariah-compliance labeling without evidence, or intra-family entitlement leakage. Monitor correction/rejection rates and RM-reported unsupported facts. Growth in touchpoints must not come from low-value automated volume."*

Decomposition into atomic non-regression controls is an **[INFERENCE]** (the PRD presents these as one paragraph). Each requires a baseline, a monitored threshold, and review at the §11 gates.

| ID | Guardrail control | Priority | Condensed testable condition | Source |
|---|---|---|---|---|
| GRD-01 | No increase in privacy incidents | P0 | Non-regression metric with baseline and alert. | §10.3 |
| GRD-02 | No increase in unauthorized data exposure | P0 | Non-regression metric with baseline and alert. | §10.3 |
| GRD-03 | No increase in non-consented recordings | P0 | Non-regression metric with baseline and alert; TEL-02 provides the signal. | §10.3 |
| GRD-04 | No increase in unsuitable hard-stop bypasses | P1 | Non-regression metric; TEL-07 `hard_stop` provides the signal. | §10.3 |
| GRD-05 | No increase in unapproved sends | P0 | Non-regression metric; TEL-04/06 `blocked / approved / sent` provides the signal. | §10.3 |
| GRD-06 | No increase in Shariah-compliance labeling without evidence | P1 pilot | Non-regression metric; INT-08/FR-4.1 provide the evidence check. | §10.3 |
| GRD-07 | No increase in intra-family entitlement leakage | P1 pilot | Non-regression metric; TEL-09 `entitlement_blocked` provides the signal. | §10.3 |
| GRD-08 | Monitor correction/rejection rates | P0 | Rate reported from TEL-03 and reviewable at gates. | §10.3; GOV-07 |
| GRD-09 | Monitor RM-reported unsupported facts | P0 | Report channel exists and rate is tracked. | §10.3; GOV-07 |
| GRD-10 | Growth in touchpoints must not come from low-value automated volume | P0 | M-03 definition (two-way interactions / attended meetings; drafts and failed sends excluded) is enforced so automated volume cannot inflate the metric. | §10.3; §10.1 M-03 |

---

## 9. Phased Rollout and Release Gates (PRD Section 11)

Structure table idx 10, `row_count: 5` → **4 phases**. Figure 2 caption maps them to Q1 Meeting Intelligence, Q2 Prioritization & Outreach, Q3 Product Recommendation + niche pilots, Q4 agentic pilots + GA.

| ID | Timing | Scope | Exit gate before expansion (testable condition) | Priority | Source |
|---|---|---|---|---|---|
| GATE-01 | Months 1–3 (Q1) | Meeting Intelligence: briefs first, then consented transcription and reviewed post-meeting automation; **D5 memory/graph and Copilot Core skeleton ship with E1 alpha** | Security/residency and consent sign-off; source traceability working; pilot demonstrates prep/admin time savings; no unresolved critical privacy/compliance defects. | Dependency | §11 row 1; §2.3 D5 |
| GATE-02 | Months 4–6 (Q2) | Prioritization & Outreach: daily Top 10, reason codes, grounded drafts and **approved send via the copilot**; Islamic wealth design partner signed; Shariah rule-pack discovery | Data-quality/ranking review; RMs understand and act on reasons; DNC/channel controls verified; touchpoint and response lift without guardrail regression. | Dependency | §11 row 2 |
| GATE-03 | Months 7–9 (Q3) | Product Recommendation + niche pilots: NL search and suitability pre-screen; Epic 4 Shariah pilot and Epic 5.1 entity/household pilot (**feature-flagged**) | Product-data entitlements and current KYC feeds validated; legal/compliance approves ratings/overrides; SSB sign-off for Shariah rule packs; test sets show correct hard-stop and entitlement behavior. | Dependency | §11 row 3 |
| GATE-04 | Months 10–12 (Q4) | Limited agentic AI pilots + GA: orchestration of already-approved, low-risk steps with expanded autonomy boundaries; **GA for Epics 1–3; Epics 4–5 roll into V2** | Separate risk assessment, narrow permissions, sandbox/pilot cohort and rollback; **no auto-send, auto-trade or bypass of RM approval without a new PRD and approval**. | Dependency | §11 row 4 |
| GATE-X | Cross-phase rule (unnumbered closing paragraph) | Each phase begins with a representative pilot across **both RM personas**, includes training and support | Expansion only after quantitative value and qualitative trust review. | Dependency | §11 closing paragraph |

---

## 10. Count table and TOTAL

| # | Category | ID range | Count | PRD source | PRD-declared count? |
|---|---|---|---|---|---|
| 1 | Functional — Epic 1 (features 1.1 / 1.2 / 1.3) | FR-01…FR-10 | 10 | §5 Epic 1 | yes (numbered FRs) |
| 2 | Functional — Epic 2 (features 2.1 / 2.2) | FR-11…FR-15 | 5 | §5 Epic 2 | yes |
| 3 | Functional — Epic 3 (features 3.1 / 3.2) | FR-16…FR-19 | 4 | §5 Epic 3 | yes |
| 4 | Functional — Cross-Cutting | FR-20…FR-22 | 3 | §5 | yes |
| | **Core functional subtotal (FR-01…FR-22)** | | **22** | | |
| 5 | Functional — Epic 4 Islamic Wealth (pilot) | FR-4.1…FR-4.3 | 3 | §5 Epic 4 | yes |
| 6 | Functional — Epic 5 Family Office (pilot) | FR-5.1…FR-5.3 | 3 | §5 Epic 5 | yes |
| | **Functional total** | | **28** | | |
| 7 | Foundational dependencies | D0…D5 | 6 | §2.3 | yes |
| 8 | Boundary / exception behaviours | B-01…B-12 | **12** | §6 table | table rows; brief said 11 → §14 D-1 |
| 9 | Non-functional requirement areas | NFR-01…NFR-11 | 11 | §7 table | yes |
| 10 | AI governance / responsible-operation controls | GOV-01…GOV-08 | 8 | §8 paragraphs | yes |
| 11 | Integration systems | INT-01…INT-10 | **10** | §9 table | table rows; brief said 11 → §14 D-2 |
| 12 | Integration cross-cutting control (freshness SLA / API limits / source ownership) | INT-11 | 1 | §9 closing paragraph | unnumbered paragraph |
| 13 | Success metrics | M-01…M-10 | 10 | §10.1 table | yes |
| 14 | Required telemetry event groups | TEL-01…TEL-09 | 9 | §10.2 items 1–9 | yes (numbered) |
| 15 | Telemetry version/correlation tagging rule | TEL-10 | 1 | §10.2 item 10 | yes (numbered) |
| 16 | Guardrails (atomic, **[DECOMPOSED]**) | GRD-01…GRD-10 | 10 | §10.3 | one paragraph, decomposed |
| 17 | Phased rollout gates | GATE-01…GATE-04 | 4 | §11 table | yes |
| 18 | Cross-phase rollout rule | GATE-X | 1 | §11 closing paragraph | unnumbered paragraph |
| | **TOTAL — discrete requirements / controls** | | **111** | | |

**Arithmetic:** 22 + 3 + 3 + 6 + 12 + 11 + 8 + 10 + 1 + 10 + 9 + 1 + 10 + 4 + 1 = **111**.

### 10.1 Alternative "strict PRD-native" total

If a reviewer refuses all **[DECOMPOSED]** and unnumbered-paragraph items (guardrails counted as 1 paragraph, `INT-11` and `GATE-X` excluded), the strict count of literally-enumerated PRD statements is **100**:

28 (functional) + 6 (dependencies) + 12 (§6) + 11 (§7) + 8 (§8) + 10 (§9 systems) + 10 (§10.1) + 10 (§10.2 numbered items) + 1 (§10.3 paragraph) + 4 (§11 phases) = **100**.

Delta 111 − 100 = 11 = +9 guardrail decomposition + `INT-11` + `GATE-X`. Both totals are defensible; **111 is the recommended basis for a gap audit** because each of those 11 is independently testable.

### 10.2 Explicitly NOT in the total (must not become "gaps")

| Excluded set | Count | Where documented |
|---|---|---|
| §12 Out of Scope for V1 | 7 | §13 below |
| §1.5 Explicit Non-Goals | 8 (partially overlapping §12) | §13 below |
| §14 Decisions Required Before Build/Launch | 8 | §13 below |
| §13 Risks and Mitigations | 11 | §13 below |
| §1.4 V1 Objectives | 5 | §15 |
| §2.2 Core V1 Workflows | 4 | §15 |
| §2.1 Personas | 2 | §15 |
| §4.1 RICE rows | 7 | §15 |
| §1.1 product principle / §5 Epic 4 positioning / §4.1 release policy / §9 + §11 closing paragraphs | folded into IDs | §0.3 |
| Q4 "expanded autonomy boundaries" | explicitly requires a new PRD | §12 |

---

## 11. What "AI Copilot" means in this PRD — definition and YES/NO qualification checklist

### 11.1 Definition (synthesised from §1.1, §2.2, §3, §4.1, §8, corroborated by §1.4, §10.1, §11)

> **"The AI Copilot" in PRD v1.1 is the single orchestrating agent that is the one entry point for the entire wealth advisory day.** All AI capabilities are delivered as **skills behind that one copilot**, never as independent AI point features. It holds **one persistent client memory** (D5, Client Memory & Relationship Graph) shared across all skills and all workflows, and it runs a **closed loop**: meeting outcomes feed the ranking model → ranking drives the next briefs → briefs carry the latest preferences. It **prepares, ranks, drafts and explains**, while **the RM reviews and approves every client-facing or system-writing action**. Its success is measured by **orchestration quality** (cross-skill task completion ≥85% without manual stitching, ≥70% of meeting-prep and outreach workflows through the single entry point, context reuse) — **not by chat volume**.

Verbatim anchors:

- §1.1: "Extend the existing RM Workbench into the AI copilot that orchestrates the entire wealth advisory day — **one client memory, every workflow, human-approved**." Product principle table: "AI prepares, ranks, drafts and explains; the RM reviews and approves every client-facing or system-writing action. **One copilot, one client memory, many skills** — AI orchestrates the workflow; the RM orchestrates the relationship."
- §2.2: four core workflows — Prepare → meet → follow up; Prioritize → converse; Discover → assess; Serve new needs (v1.1) — and "Shariah-preference-aware advisory and family/household consolidation executed **through the same copilot skills and client memory — not separate modules**."
- §3: "**All AI capabilities are delivered as skills behind a single orchestrating copilot, not as independent features.** The architecture has five layers… Experience, Orchestration, Context (D5), Skills, Trust." "Closed loop: meeting outcomes feed the ranking model; ranking drives the next briefs; briefs carry the latest preferences. Orchestration quality is measured by cross-skill task completion (target ≥85% without manual stitching) and context reuse, **not by chat volume**."
- §4.1: RICE model + "Compliance dependencies and workflow order can override raw score order"; release policy table (§12 below) makes Epics 1–2 P0 and fixes delivery order 1.1 → 1.2 → 1.3 → 2.1 → 2.2. §1.2: fragmented AI point features "force the RM to act as the integration layer — copying context between tools. The copilot architecture (Section 3) resolves this by design."
- §8: human-in-the-loop, zero provider retention/training, grounding and explainability, override and feedback, model/prompt/rule-pack change management, compliance ownership, monitoring and kill switch, fairness and data minimization.
- §11 GATE-01: "**D5 memory/graph and Copilot Core skeleton ship with E1 alpha**" (Months 1–3) — orchestration is a Q1 foundation, not a late add-on.
- §12: a "general-purpose chatbot unrelated to RM workflows" is explicitly out of scope — therefore a chat box is **not** the copilot.

**What the PRD does NOT specify** (do not audit these as gaps): no chat UI is prescribed, no LLM vendor/model, no RAG/agent framework, no orchestration engine, no specific skill taxonomy or count, no programming language, no database. These are technical choices, not PRD requirements. Any inference about them is out of scope for a requirement gap audit.

### 11.2 Mandatory architectural properties

| # | Property | PRD evidence | Status |
|---|---|---|---|
| 1 | Single orchestrating copilot vs independent AI point features | §3, §1.1, §1.2, §2.2 | PRD-explicit |
| 2 | Five layers: Experience / Orchestration / **Context (D5)** / Skills / Trust | §3, Figure 1 | PRD-explicit |
| 3 | Skill registry (catalog of invocable, versioned skills) | §3 "skills", §1.1 "many skills", §10.2 "skill invocation chain", §8 "single orchestration stage", §13 "stage-level kill switches" | **[INFERENCE]** — "registry" is not literally named; a discoverable/invocable/versionable skill catalog is implied |
| 4 | Client Memory & Relationship Graph (D5), Q1 critical path, E1 alpha | §2.3 D5, §3, §11 GATE-01 | PRD-explicit |
| 5 | Closed loop: meeting outcomes → ranking → briefs → preferences | §3 | PRD-explicit |
| 6 | Cross-skill task completion ≥85% without manual stitching, instrumented | §3, §10.1 M-06, §10.2 TEL-08 | PRD-explicit (target) |
| 7 | ≥70% of meeting-prep + outreach workflows through copilot single entry point by GA | §1.4, §10.1 M-05 | PRD-explicit (target) |
| 8 | Provenance/evidence: source records, data-as-of timestamps, material factors, confidence/limitations | §8 GOV-03, §1.1, FR-02, §7 AI explainability | PRD-explicit |
| 9 | Human approval gates; no autonomous client action or execution | §8 GOV-01, §1.1, FR-20, §1.5 | PRD-explicit |
| 10 | Versioning + representative test-set evaluation + rollback (models, prompts, templates, ranking policies, Shariah rule packs) | §8 GOV-05 | PRD-explicit |
| 11 | Kill switch at model-feature **or single orchestration stage** granularity, preserving manual workflows + audit | §8 GOV-07, §13 | PRD-explicit |
| 12 | Orchestration telemetry: workflow lifecycle, skill invocation chain, manual-stitch interventions; correlated telemetry | §10.2 TEL-08, §7 Observability | PRD-explicit |
| 13 | Zero provider retention/training (contractual + technical, verified at vendor review) | §8 GOV-02, §12 | PRD-explicit |
| 14 | Copilot Core skeleton ships with E1 alpha (Months 1–3) | §11 GATE-01 | PRD-explicit |
| 15 | Epics 4–5 delivered through the same copilot skills and client memory, not separate modules | §2.2, §5 Epic 4/5 | PRD-explicit |
| 16 | Orchestration quality measured by cross-skill completion and context reuse, NOT chat volume; no general-purpose chatbot surface | §3, §12 | PRD-explicit |
| 17 | Node-level entitlement filtering **inside copilot context assembly**; no cross-entity leakage in any AI artifact | §6 B-12, §5 FR-5.1, §11 GATE-03, §13 | PRD-explicit (pilot tier) |
| 18 | Copilot is a calculation/evidence assistant, never a fatwa issuer; SSB-reviewed configurable rule packs | §5 Epic 4 positioning, §12 | PRD-explicit (pilot tier) |

### 11.3 YES/NO qualification checklist (frozen contract for Phase 3)

Mark each **YES** or **NO** against the implementation. `M` = mandatory for the "is it THE AI Copilot?" verdict; `M*` = mandatory but derived by inference; `P` = pilot-tier.

| Check | Question to answer about the implementation | Type | Verdict |
|---|---|---|---|
| C-01 | Are ALL AI capabilities delivered as skills behind ONE orchestrating copilot, with no independent/standalone AI point features that require the RM to copy context between them? | M (§3, §1.1, §1.2) | ☐ YES ☐ NO |
| C-02 | Is a five-layer architecture present and identifiable — Experience, Orchestration, Context (D5), Skills, Trust? | M (§3, Fig. 1) | ☐ YES ☐ NO |
| C-03 | Is there a skill registry/catalog of invocable skills with versioned definitions (evidenced by a skill invocation chain and stage-level control)? | M* **[INFERENCE]** (§3, §10.2, §8) | ☐ YES ☐ NO |
| C-04 | Does D5 Client Memory & Relationship Graph exist as persistent per-client context + family/entity graph, available to orchestration (not a per-feature cache)? | M (§2.3, §3, §11 GATE-01) | ☐ YES ☐ NO |
| C-05 | Is the closed loop wired: meeting outcomes → ranking model → next briefs → briefs carrying latest preferences? | M (§3) | ☐ YES ☐ NO |
| C-06 | Is cross-skill task completion ≥85% without manual stitching, and is it actually measured (not just claimed)? | M (§3, M-06, TEL-08) | ☐ YES ☐ NO |
| C-07 | Are ≥70% of meeting-prep and outreach workflows completed through the copilot single entry point by GA, and is this measured? | M (§1.4, M-05) | ☐ YES ☐ NO |
| C-08 | Does every material AI output carry source records, data-as-of timestamps, material factors and confidence/limitations, with faithful explanations? | M (§8 GOV-03, FR-02, §7) | ☐ YES ☐ NO |
| C-09 | Is there an identifiable review state and approver on every AI-generated brief section, note, CRM write, message, recommendation and ticket handoff — with zero autonomous client actions or executions? | M (§8 GOV-01, §1.1, FR-20, §1.5) | ☐ YES ☐ NO |
| C-10 | Are models, prompts, templates, ranking policies and Shariah rule packs versioned, evaluated on approved representative test sets before release, and rollback-capable? | M (§8 GOV-05) | ☐ YES ☐ NO |
| C-11 | Can an authorized operator disable a model feature OR a single orchestration stage while preserving manual workflows and audit records? | M (§8 GOV-07, §13) | ☐ YES ☐ NO |
| C-12 | Are `copilot_workflow_started/stage_approved/completed/abandoned`, skill invocation chain and manual-stitch interventions emitted, with correlated technical/AI-quality/business telemetry? | M (§10.2 TEL-08, §7) | ☐ YES ☐ NO |
| C-13 | Are zero-retention/zero-training controls in place for LLM providers (contractual + technical, provider logging disabled, prompts minimized, verified at vendor/security review)? | M (§8 GOV-02, §12) | ☐ YES ☐ NO |
| C-14 | Did the Copilot Core skeleton ship with the E1 alpha in Months 1–3 (i.e. orchestration exists as a Q1 foundation, not bolted on after the point features)? | M (§11 GATE-01) | ☐ YES ☐ NO |
| C-15 | Are Epic 4 / Epic 5 capabilities executed through the same copilot skills and client memory rather than separate modules? | M (§2.2, §5) | ☐ YES ☐ NO |
| C-16 | Is orchestration quality measured by cross-skill completion and context reuse (not chat volume), and is there no general-purpose chatbot surface? | M (§3, §12) | ☐ YES ☐ NO |
| C-17 | Does copilot context assembly filter per-node entitlements, with no cross-entity leakage in any AI artifact? | P (pilot tier) (§6 B-12, FR-5.1, GATE-03) | ☐ YES ☐ NO |
| C-18 | Is the copilot a calculation/evidence assistant only (never a fatwa issuer), with SSB-reviewed configurable rule packs? | P (pilot tier) (§5 Epic 4, §12) | ☐ YES ☐ NO |

**Decision rule (unambiguous, no judgement calls):**

1. An implementation **legitimately qualifies as "the AI Copilot" of PRD v1.1 only if C-01 … C-16 are ALL YES.**
2. **ANY single NO in C-01…C-16 ⇒ the implementation is a collection of AI point features, not the PRD's copilot.** Extra features, a nicer chat UI, or more LLM calls do not compensate.
3. **Architecturally disqualifying on their own** (cannot be compensated by feature count): `C-01`, `C-04`, `C-05`, `C-12`. A NO on any of these means the required architecture is absent regardless of how many individual features exist.
4. `C-17` / `C-18` are **pilot-tier**: they are required to claim Epic 4/5 pilot compliance but are **NOT** a gap for a "V1 core GA (Epics 1–3)" claim (§11 GATE-04 rolls Epics 4–5 into V2).
5. `C-03` is **[INFERENCE]**. If a reviewer rejects the inference that a "skill registry" is mandated, reclassify it as supporting evidence rather than a hard gate; C-01, C-02, C-11 and C-12 still independently require skill-level identifiability and stage-level control.
6. **C-06 / C-07 are numeric targets, not functional features** (§1, A-02). For a *gap* verdict, check that the measurement path exists (TEL-08, M-05, M-06); do not mark a gap merely because the percentage has not yet been achieved.

---

## 12. Release policy, sequencing and gate scoping

### 12.1 PRD-declared release policy (§4.1 release-policy table, extraction line 108)

| Rule | PRD statement | Consequence for the gap audit |
|---|---|---|
| R-1 | "**Epic 1 and Epic 2 are P0 for V1**" | FR-01…FR-15 are non-negotiable for any "completed V1" claim. |
| R-2 | "**Epic 3 is P1 and must not delay P0 launch**" | FR-16…FR-19 are required for GA of Epics 1–3 but their absence cannot be used to block or reclassify the P0 launch. |
| R-3 | "**Delivery order is 1.1 → 1.2 → 1.3 → 2.1 → 2.2**" | Dependency order is contractual: 1.3 depends on 1.2 outputs and write mappings; 2.2 depends on 2.1's reason/evidence model. |
| R-4 | "**Epic 3 following compliance sign-off**" | Epic 3 is gated by GOV-06 / GATE-03, not by engineering readiness alone. |
| R-5 | "**Epics 4 and 5 (v1.1) are niche-differentiator pilots and must not delay core GA**" | FR-4.x / FR-5.x are pilot scope, feature-flagged in Q3, rolling into V2 (GATE-04) → **not core-GA gaps**. |
| R-6 | §4.1: "**Compliance dependencies and workflow order can override raw score order**" | RICE rank is not a delivery permission. |
| R-7 | §5 Epic 3 heading: "P1; **depends on D3**" | D3 is a hard prerequisite. |
| R-8 | §11 GATE-01: "**D5 memory/graph and Copilot Core skeleton ship with E1 alpha**" | Copilot orchestration is Q1 scope, not a V2 item. |
| R-9 | §11 GATE-04: "**GA for Epics 1–3; Epics 4–5 roll into V2**"; "no auto-send, auto-trade or bypass of RM approval **without a new PRD and approval**" | Expanded autonomy is explicitly out of V1 scope. |
| R-10 | §11 GATE-02: prioritization/outreach includes "**approved send via the copilot**" | Even Epic 2 must be routed through the copilot, not a standalone module. |

### 12.2 Gap-audit scoping tiers (requirements-side rule for Phases 2–3)

| Tier | What it contains | Does a missing item count as a GAP? |
|---|---|---|
| **Tier A — Core P0 / GA-blocking** | FR-01…FR-15, FR-20, FR-22; D0, D1, D2, D4, **D5**; B-01…B-07, B-10; NFR-01…NFR-07, NFR-09…NFR-11; GOV-01…GOV-05, GOV-07, GOV-08; INT-01…INT-06, INT-10, INT-11; M-01…M-06; TEL-01…TEL-06, TEL-08, TEL-10; GRD-01/02/03/05/08/09/10; GATE-01, GATE-02, GATE-X; C-01…C-16 | **YES — core gap.** |
| **Tier B — P1, GA for Epics 1–3 (Months 10–12)** | FR-16…FR-19; D3; B-08, B-09; NFR-08; GOV-06; INT-07; M-07, M-08; TEL-07; GRD-04; GATE-03, GATE-04 | **YES for a "GA of Epics 1–3" claim**, but explicitly "must not delay P0 launch" (R-2). |
| **Tier C — Pilot / feature-flagged / rolls into V2** | FR-4.1…FR-4.3, FR-5.1…FR-5.3; B-11, B-12; INT-08, INT-09; M-09, M-10; TEL-09; GRD-06, GRD-07; C-17, C-18 | **NOT a core-GA gap.** At most a roadmap/pilot gap. |
| **Tier D — Not requirements** | §12 out-of-scope; §1.5 non-goals; §14 open decisions; §13 risks; §4.1 RICE scores; §1.4 objectives; §2.2 workflows; §2.1 personas; Q4 expanded autonomy | **NEVER count as gaps.** |

---

## 13. Out of scope, non-goals and open decisions — DO NOT count as gaps

### 13.1 §12 Out of Scope for V1 (structure table idx 11, 7 data rows)

| ID | Excluded item | Reason / boundary in PRD |
|---|---|---|
| OOS-01 | Full financial planning | Integrate with MoneyGuide/eMoney rather than duplicate specialized planning capability. |
| OOS-02 | Alternative-investments marketplace | Different liquidity, due-diligence and distribution model; not needed to validate core workflows. |
| OOS-03 | Client portal | V1 focuses on RM productivity and engagement first. |
| OOS-04 | Autonomous advice, client sends or trade execution | Conflicts with V1 human-in-the-loop and regulatory risk posture. |
| OOS-05 | Issuing fatwas or authoritative religious rulings | Copilot is a calculation/evidence assistant; SSB and scholars retain authority. |
| OOS-06 | General-purpose chatbot unrelated to RM workflows | Avoid ungrounded surface area; ship only defined copilot-orchestrated tasks. |
| OOS-07 | Automatic model training on client/RM data | Prohibited by zero-retention/privacy principle; future learning programs require separate governance and consent review. |

### 13.2 §1.5 Explicit Non-Goals (8 items, partially overlapping §12)

NG-01 replace the system of record · NG-02 autonomous financial advice · NG-03 auto-send AI content · NG-04 auto-submit trades · NG-05 issue religious rulings (fatwas) · NG-06 full financial planning · NG-07 alternatives marketplace · NG-08 client portal.

> NG-01 ("does not replace the system of record") is a **positive architectural constraint** and appears only in §1.5. It is not a gap item; it bounds what the workbench may become.

### 13.3 §14 Decisions Required Before Build/Launch (8 open decisions — NOT requirements)

| ID | Decision | Blocks |
|---|---|---|
| DEC-01 | Supported meeting platforms/languages, jurisdiction-specific consent, audio/transcript retention and deletion rules (Legal/Security) | Before transcription build (FR-04…FR-06, D2) |
| DEC-02 | Target CRM/email/calendar systems, authoritative fields, write permissions and retry/reconciliation ownership (Engineering/Operations) | Before CRM automation (FR-08, INT-04) |
| DEC-03 | Ranking objective weights, signal freshness, DNC precedence and meaningful-touchpoint definition (Product/Data/Compliance) | Before prioritization pilot (FR-11…FR-13, M-03) |
| DEC-04 | Product universe, market-data entitlements, suitability rule owner, hard-stop/override matrix, KYC freshness threshold (Compliance/Product) | Before Epic 3 (FR-18/19, D3) |
| DEC-05 | Islamic design partner with engaged SSB; screening standard per market; zakat methodology; disclaimer wording | Before Epic 4 pilot |
| DEC-06 | Entity-type coverage, custodian feeds, intra-family entitlement matrix, document-extraction quality bar | Before Epic 5 pilot |
| DEC-07 | Retention observation window, client-vs-asset retention definition, matched comparison method, baseline sample | Before success claims (M-07) |
| DEC-08 | Supported OS/device policy, sensitive-data caching, mobile approval requirements | Before mobile release (FR-21, NFR-08) |

> These are **open decisions the PRD itself says are unresolved**. An implementation that has not resolved them is not automatically non-compliant; the audit should check whether the corresponding feature is *configurable* (FR-22) and whether the decision is documented, not whether a particular value was chosen.

### 13.4 §13 Risks and Mitigations (11 rows) — informative, not requirements

RM distrust or automation bias · Regulatory/recording non-compliance · Poor or fragmented source data · Transcription/extraction errors · Ranking optimizes wrong behavior · Integration/provider outage · Privacy leakage or provider retention · Model drift or change regression · Shariah ruling error presented as authoritative (v1.1) · Intra-family privacy leakage via AI (v1.1) · Orchestration errors compounding across skills (v1.1).

Three of these mitigations restate normative controls already inventoried and are **folded in, not double-counted**: "stage-level kill switches" → `C-11`/`GOV-07`; "leakage tests as hard release gate" and "node-level entitlements in copilot context assembly" → `C-17`/`GATE-03`/`B-12`; "end-to-end orchestration eval suite" → `GOV-05`/`C-10`.

---

## 14. Discrepancies with the task brief, and inference register

| ID | Issue | Resolution |
|---|---|---|
| D-1 | Brief says **11** boundary/exception behaviours in §6. The PRD §6 table has **12 data rows** (structure tree table idx 6: `row_count: 13` incl. header; extraction lines 169–180). | Enumerated **12** (`B-01…B-12`). Likely cause: v1.1 added two rows — `B-11` (Shariah-sensitive client / non-compliant candidate) and `B-12` (intra-family entitlement boundary) — on top of the original 10. Both are pilot-tier, so the brief's "11" may reflect an older count. **Use 12.** |
| D-2 | Brief says **11 integration systems** in §9. The PRD §9 table has **10 system rows** (structure tree table idx 8: `row_count: 11` incl. header; extraction lines 213–222). | Enumerated **10 systems** (`INT-01…INT-10`). The 11th discrete integration item is the **unnumbered closing paragraph** on freshness SLAs / API limits / authoritative-source ownership, inventoried as `INT-11`. So "11 integration items" is defensible as 10 systems + 1 cross-cutting control. **Use 10 systems + INT-11.** |
| D-3 | "Skill registry" requested in the brief is **not literally named** anywhere in the PRD. | Marked `C-03` as **[INFERENCE]** derived from §3 "skills", §1.1 "many skills", §10.2 "skill invocation chain", §8 "single orchestration stage", §13 "stage-level kill switches". Downgraded to supporting evidence if a reviewer rejects the inference. |
| D-4 | FR-20…FR-22 have no PRD-declared priority. | Assigned P0 (V1-wide) with **[INFERENCE]** tag and justification in §2.4. |
| D-5 | §10.3 guardrails are one unnumbered paragraph. | **[DECOMPOSED]** into 10 atomic controls `GRD-01…GRD-10`; alternative strict total (100) given in §10.1. |
| D-6 | §9 closing paragraph and §11 closing paragraph are unnumbered but normative. | Counted as `INT-11` and `GATE-X`; flagged in §10.1 so the total can be reconciled. |
| D-7 | §1.4 objectives / §2.2 workflows overlap FRs and the copilot checklist. | Listed in §15 as supplementary; not counted, to avoid duplicate implementations (Iron Law 1). |
| D-8 | §1.1 product principle and §5 Epic 4 positioning are normative, not numbered. | Folded into `C-09`, `C-18` and FR-4.x ACs; not counted separately. |
| D-9 | Epic 5 heading says "P1/P2 pilot" but only FR-5.3 is explicitly marked "(P2)". | FR-5.1 / FR-5.2 assigned P1 pilot **[INFERENCE]**; FR-5.3 P2 as declared. |
| D-10 | Metric M-07 / M-08 / M-10 and all NFR thresholds could be mistaken for functional gaps. | Classified as **[TARGET]** / **[ACCEPTANCE TARGET]** in §1.3; audit the measurement capability, not the achieved number. |
| D-11 | The brief calls the repo a "completed implementation"; PRD status is "**Proposed for engineering/design estimation**". | Noted as context only. No conclusion about the codebase is drawn here (out of my scope). |

---

## 15. Supplementary PRD content (definitional / not counted)

| ID | Item | Source |
|---|---|---|
| OBJ-01 | Reduce meeting preparation 45 → 10 min and post-meeting administration 20 → 5 min | §1.4 |
| OBJ-02 | Increase meaningful client touchpoints 4–6 → 8–12 per client per quarter without reducing compliance quality | §1.4 |
| OBJ-03 | 60% monthly brief adoption among enabled active RMs within six months of Meeting Intelligence launch | §1.4 |
| OBJ-04 | ≥70% of meeting-prep and outreach workflows through the copilot single entry point by GA | §1.4 |
| OBJ-05 | Shorten product research and make suitability conflicts visible before a recommendation or trade is initiated | §1.4 |
| WF-01 | Prepare → meet → follow up: calendar/client selection → sourced brief → consented transcription → reviewed notes/actions → approved CRM update, email draft and pre-filled ticket | §2.2 |
| WF-02 | Prioritize → converse: daily Top 10 → reason/evidence inspection → client detail → editable outreach → RM approval/send → outcome capture | §2.2 |
| WF-03 | Discover → assess: NL product request → interpreted filters → suitable results → Red/Yellow/Green assessment → RM decision and audit | §2.2 |
| WF-04 | Serve new needs (v1.1): Shariah-preference-aware advisory and family/household consolidation through the same copilot skills and client memory — not separate modules | §2.2 |
| PER-01 | Senior Private Wealth RM: 50–150 HNWI clients; $50M–$500M AUM → deeper briefs, complex history, explainable risk/suitability evidence | §2.1 |
| PER-02 | Mass Affluent RM: 100–300 clients; $20K–$2M per client → high-throughput ranking, fast reusable outreach, mobile access | §2.1 |
| RICE-01…07 | 1.1 (48.0, rank 1) · 1.2 (36.0, rank 2) · 1.3 (33.6, rank 3) · 2.1 (31.5, rank 4) · 2.2 (28.0, rank 5) · 3.2 (13.2, rank 6) · 3.1 (9.0, rank 7) | §4.1 |
| FIG-01 | Figure 1 — Five-layer AI copilot architecture (Mermaid, embedded as rendered image) | §3 |
| FIG-02 | Figure 2 — V1 rollout Gantt (Mermaid, embedded as rendered image) | §11 |
| SELF-CHECK | "Every numbered requirement has acceptance criteria or a testable policy; primary and exception flows are covered; dependencies and non-goals are explicit; research-derived statements are attributed to Phase 1, and RICE assumptions/targets are distinguished from observed facts." | §14 closing |

---

## 16. Hand-off notes for Phases 2–3

1. **Use these IDs verbatim.** They are the frozen contract (Iron Law 3). If a gap is found, report `FR-xx` / `D5` / `C-xx` etc.; do not invent new labels.
2. **Apply the tier rule in §12.2 before calling anything a gap.** The single biggest source of false positives in this audit will be Tier C pilot features (Epics 4–5), Tier D out-of-scope items, and unachieved numeric targets.
3. **The copilot question is architectural, not a feature count.** Use `C-01…C-16` (§11.3). A "NO" on `C-01`, `C-04`, `C-05` or `C-12` is decisive on its own.
4. **Do not penalise unresolved §14 decisions.** They are PRD-declared open items; check configurability (FR-22) and documentation instead.
5. **Evidence vs assumption:** do not report a missing numeric target as a functional gap. Verify the measurement path (§10.2 telemetry, §10.1 definitions, comparison method).
6. **Two count corrections:** §6 = **12** behaviours (not 11); §9 = **10** systems (not 11) plus one cross-cutting control. Canonical total = **111** discrete requirements/controls (strict PRD-native = 100).

---

*End of Deliverable 01. Prepared by Xu Qingchu (许清楚), Requirements Analyst. Requirements side only — no implementation claims, no technical selection, no UI design.*

# Requirements Specification — RM Workbench MVP (Leadership Demo)

**Phase 1 deliverable · Author:** Xu Qingchu (许清楚), Requirements Analyst, software-dev-team
**Consumers (verbatim hand-off):** Qi Huolin (team lead) → product-designer (Phase 2), solution-architect (Phase 3), feature-planner (Phase 4), Phase N assembly.
**Status:** For review. **Design only — no application code, no runnable scripts, no shipped system.**
**Language:** English.

---

## 0. Reading note, tag legend and evidence base

Sources actually read in full: `00_Shared_Design_Brief.md`; `RM_Workbench_PRD.md` (v1.1, 22 FRs, §§6/7/12/14); `RM_Workbench_Video_Treatment.md` (v2); `RM_Workbench_AI_Copilot_and_Niche_Expansions.md` (v1.1, Copilot Core / D5 / Epics 4–5); `RM_Workbench_Product_Strategy_Package.md` (RICE, NFR baseline). No external research was performed and no research findings are invented.

| Tag | Meaning |
|---|---|
| `[PRD]` | Verifiable in the source documents above. |
| `[INFERENCE]` | My reasoned derivation from those sources; challengeable, not a fact. |
| `[ASSUMPTION]` | Default adopted because user/PRD did not specify; requires Alan's confirmation (§9). |

**Scope of this document.** It freezes *what must be demonstrably true on stage*. It deliberately does **not** fix screens, visual design, components, technology selection, schema DDL or dataflow — those belong to Phase 2/3/4. §8 hands NFR *inputs* to the architect; the architect owns the final NFR spec. `[INFERENCE]`

---

## 1. Engagement framing

**Purpose.** Produce an MVP design package that lets Capco demonstrate, to senior leadership of a wealth-management client, a credible next-generation RM Workbench. `[PRD: brief §1, R7]` The deliverable is a *design*, not a system; all artefacts must land on disk. `[PRD: brief §8.4]`

**Audience.** Primary: Alan (Capco, CTO advisor) and the client's senior leadership — a banking audience that will probe provenance, consent, approval and compliance. Secondary: the downstream design team, who need unambiguous, testable requirements. `[PRD]`

**What "MVP" means here.** A **demonstrable slice**, not a production release and not "a small version of V1". The PRD is a 12-month V1 with 22 FRs, 5 epics and a 26–64 FTE envelope. `[PRD: §4.1, §11; strategy package]` An MVP cut on *feature count* (e.g. "briefs only") would fail the assignment because the PRD states the loop is the product: *"meeting outcomes feed ranking → ranking drives next briefs → briefs carry latest preferences. This loop is the product."* `[PRD: §3]` Therefore the MVP is cut on **depth, not breadth**: it contains the whole loop end-to-end, with every stage thinned to the minimum needed to be provable. `[INFERENCE]`

**Single headline claim the MVP must prove on stage:**

> **A genuine, unscripted live market event enters the workbench and, within seconds, propagates through the entire advisory loop — re-ranked priorities, a refreshed sourced brief, a grounded outreach draft — with every AI statement carrying a source/timestamp chip and every outbound action stopping at a human Approve.**

This is the brief's designated "single most persuasive proof point" (`§6.1`) `[PRD]`, extended by the user's live-market-data requirement `[PRD: brief §3 R4]`. The locked tagline remains *"AI orchestrates the workflow. You orchestrate the relationship. / Human-approved. Always."* `[PRD: video treatment §5]`

### 1.1 What is real, simulated and stubbed — and why that is honest

| Element | Posture | Why acceptable / honesty control |
|---|---|---|
| Live market feed in `live` mode | **REAL** | One genuinely external feed, real wall-clock `as_of`, real attribution. This is the proof point; faking it would destroy the claim. |
| Postgres store; file/database generator; flat files; provenance chips; audit writes; approval gates; re-rank; mode switch | **REAL** | The orchestration, provenance and trust claims must be genuinely executed, not animated. |
| All client / portfolio / household / preference / meeting / CRM / email / product / suitability / Shariah data | **SIMULATED — 100% synthetic, deterministic** | `[ASSUMPTION]` no real PII ever. Permanent on-screen label `SYNTHETIC DEMO DATA`. |
| `replay` mode | **SIMULATED — recorded tick stream, deterministic** | Guarantees a repeatable stage demo without network risk; carries an uncuttable `REPLAY — recorded <time>` chip. `[PRD: brief §6.2]` |
| Audio capture / ASR transcription | **STUBBED** | The consent gate and recording state are real; the transcript is a scripted injection. No microphone, no real ASR. Why: ASR accuracy is not what the demo proves, and real recording raises consent/retention exposure. |
| CRM / email / SMS external send | **STUBBED to a local demo sink** | Records exact final content + provider-style status; zero external egress; `DEMO SINK — not delivered` chip. |
| Trade execution | **HARD-BLOCKED (no stub at all)** | Pre-filled handoff only; execution path absent by construction. `[PRD: §12]` |
| LLM / multi-model router | **STUBBED — deterministic outputs with fixed version stamps** | The demo proves orchestration and provenance, not model quality. Every output still carries model/prompt/rule-pack version stamps (C-1/C-4). |
| SSO / identity / calendar / core banking / portfolio systems | **STUBBED** | Demo role switcher; book and node entitlements are still enforced server-side, not just in UI. |
| Product universe, KYC/suitability feeds, Shariah rule packs | **SEEDED SIMULATED** | No D3 certification or SSB sign-off needed for synthetic demo data. `[PRD: §14.4/§14.5]` |

**Why this is acceptable and honest:** the demo never claims vendor integrations, ASR accuracy, model quality, regulatory certification or production scale. Every non-real element is visibly labelled; switching `live`↔`replay` changes the label, not the story. A sceptical executive who asks "is that real?" gets a precise, non-defensive answer for every element. `[INFERENCE]` The claim being proved (live event → loop → sourced facts → human approval) is genuinely real where it matters.

---

## 2. MVP scope decision, argued

### 2.1 The cut line

Three forces set the cut: (i) the loop must close end-to-end `[PRD: §3]`; (ii) a live market event must be the **trigger**, not decoration `[PRD: brief §2, §6.1]`; (iii) at least one lightweight "range" moment must land, without sinking into Epic 3/4/5 depth `[PRD: brief §6.3]`. `[INFERENCE]`

**IN (depth-thinned):** E1.1 brief, E1.2 consent gate + scripted capture, E1.3 unified review/approval, E2.1 Top N, E2.2 grounded draft + approved send, D5 memory/graph, Copilot Core orchestration, Trust (provenance/audit/version stamps) — because removing any one of these breaks the loop or the trust story. **NEW, from the user, not in the PRD:** live market ingest + signal detection; demo data fabric / file–database generator; Postgres; live/replay demo operations. `[PRD: brief §3 R4/R5/R6]`

**OUT (deferred, not abandoned):** E3 NL product search, E3 Red/Yellow/Green suitability assessment, E4 depth (screening engine, zakat, purification, SSB evidence packs, hawl orchestration), E5 depth (multi-custodian consolidation, look-through, succession scenarios, capital calls), real integrations, mobile parity, full eval harness and multi-model routing, and all production-scale NFRs.

One deliberate nuance: **E3's suitability logic is OUT as a feature but its *hard-stop rule is retained as a boundary*** — "missing/expired suitability → Yellow at best and blocks ticket handoff" `[PRD: §6]`. A demo that lets a pre-filled trade ticket through without a suitability gate would be actively misleading to a banking audience. `[INFERENCE]`

### 2.2 Value / effort rationale (demo-adapted RICE)

The PRD's own RICE ranks 1.1 (48.0) > 1.2 (36.0) > 1.3 (33.6) > 2.1 (31.5) > 2.2 (28.0) >> 3.2 (13.2) > 3.1 (9.0), and explicitly labels these as planning assumptions, not research findings. `[PRD: §4.1]` For a stage demo, "reach" is meaningless; I substitute **Demo Value** (DV 1–5: does it carry the loop / the headline / the trust story?) and **Demo Effort & Risk** (DE 1–5). Scores are `[INFERENCE]`, challengeable, and deliberately coarse.

| Capability | DV | DE | DV/DE | Decision | One-line justification |
|---|---:|---:|---:|---|---|
| Live tick ingest + signal detection | 5 | 2 | 2.50 | **IN** | It is the user's explicit request and the on-stage trigger; without it there is no headline. |
| Copilot Core orchestration (thin) | 5 | 3 | 1.67 | **IN** | The anti-fragmentation claim; sequenced skills are the whole point. |
| D5 memory + graph (thin) | 5 | 3 | 1.67 | **IN** | Cross-skill context reuse is what makes the loop visible. |
| E1.3 unified review + approval | 5 | 3 | 1.67 | **IN** | "One review, one Approve" is the emotional centre of the narrative. `[PRD: video §4 Seq2]` |
| E2.1 Top N + reason codes | 5 | 3 | 1.67 | **IN** | The visible *output* of the loop and of the re-rank. |
| E1.1 five-section sourced brief | 5 | 3 | 1.67 | **IN** | Highest PRD RICE; the densest provenance surface. |
| Provenance chips + audit + version stamps | 5 | 2 | 2.50 | **IN** | Non-negotiable UI rule for a banking audience. `[PRD: video §7]` |
| E2.2 grounded outreach + approved send | 4 | 2 | 2.00 | **IN** | Closes "AI drafts / RM approves"; cheap via demo sink. |
| E1.2 consent gate + scripted capture | 4 | 2 | 2.00 | **IN (thin)** | Consent banner cannot be cut `[PRD: video §6]`; real ASR is not needed. |
| Demo data fabric + generator + Postgres | 5 | 3 | 1.67 | **IN** | User's explicit request; reproducibility is a demo acceptance gate. |
| Live/replay switch + reset + health panel | 5 | 2 | 2.50 | **IN** | Removes stage risk; the honest label is itself a trust proof. |
| Family entity graph + entitled pack versions | 3 | 2 | 1.50 | **IN (one range moment)** | Reuses D5 graph at marginal cost; proves node-level entitlement in context assembly. |
| Shariah preference propagation (thin) | 2 | 2 | 1.00 | **IN, P1, flag OFF** | Optional second beat; first to cut if scope tightens. No screening/zakat math. |
| E3.2 suitability pre-screen (full) | 2 | 4 | 0.50 | **OUT** | Needs validated rules/KYC; hard-stop boundary retained instead. |
| E3.1 NL product search | 1 | 4 | 0.25 | **OUT** | Needs a 500+ product universe + D3 sign-off `[PRD: §14.4]`; not on the loop's critical path. |
| E4 depth (screening/zakat/SSB packs) | 1 | 5 | 0.20 | **OUT** | Requires Islamic design partner + SSB sign-off `[PRD: §14.5]`; active compliance risk on stage. |
| E5 depth (consolidation/succession/calls) | 1 | 5 | 0.20 | **OUT** | Multi-custodian reconciliation and document intelligence are demo-invisible. |
| Real ASR / real CRM / real send / real SSO | 1 | 5 | 0.20 | **OUT → stub** | Vendor risk with zero DV gain. |
| Mobile parity (FR-21) | 1 | 3 | 0.33 | **OUT** | Single presenter screen; no observer value. |
| Production NFRs (1,000 users, 99.5%, SOC 2, residency, DR) | 1 | 5 | 0.20 | **OUT → deferred** | Claiming these for a demo would be dishonest (§7.3). |

### 2.3 Explicit Out of Scope

**(a) V1 capabilities deferred beyond the demo** — these are *not* product non-goals; they return in the 12-month plan.

| Capability | Deferred because | Returns |
|---|---|---|
| FR-16/17 NL product search & result comparison | Requires certified product universe, entitlements, current KYC `[PRD: §9/§14.4]` | Post-demo / PRD Q3 |
| FR-18/19 Red/Yellow/Green assessment, overrides, hard-stop matrix | Needs validated suitability rules and compliance ownership; only the *hard-stop rule* is retained as a boundary | Post-demo / PRD Q3 |
| FR-4.1.2–4.1.4 screening engine, Islamic product library, drift monitoring | SSB rule packs + design partner `[PRD: §14.5]` | PRD Q3 pilot |
| FR-4.2 zakat / purification / hawl orchestration; FR-4.3 evidence packs | Methodology sign-off; "estimate" labelling retained for the optional thin beat | PRD Q3 pilot |
| FR-5.1.2 multi-custodian consolidation & look-through; FR-5.2 succession; FR-5.3 capital calls | Demo-invisible depth; entity *graph + entitlements* retained as the range moment | PRD Q3/V2 |
| Real transcription, real CRM/email/SMS providers, real calendar/SSO, real trade execution | Vendor risk, zero demo value; replaced by labelled stubs/sink | Integration phase |
| FR-21 mobile parity; full eval harness; multi-model router | Single-screen demo; deterministic outputs suffice | Post-demo |
| Production NFRs and retention/adoption analytics | No longitudinal data, no production deployment | PRD GA gates |

**(b) Permanent non-goals carried over verbatim in substance from PRD §12 / §1.5** `[PRD]` — these are **never** in scope, including any future demo build:

| Non-goal | Boundary |
|---|---|
| Autonomous financial advice | Copilot prepares; RM decides. |
| Auto-send of AI content / autonomous client sends | Every outbound action needs a human tap (C-3). |
| Auto-trade / trade execution / auto-submit | Handoff only; execution path absent. |
| Issuing fatwas or authoritative religious rulings | Copilot is a calculation/evidence assistant; "not a fatwa" label mandatory. |
| Client-facing portal | RM productivity surface only. |
| General-purpose / open-ended chatbot | Only defined copilot-orchestrated tasks; no ungrounded chat. |
| Automatic model training on client/RM data | Zero-retention principle. |
| Full financial planning; alternatives marketplace | Integrate, do not duplicate. |
| Replacing the system of record | Workbench orchestrates; it does not become CRM/core banking. |

---

## 3. Roles and permissions

### 3.1 Demo roles

| Role | May see / do | May NOT do |
|---|---|---|
| **RM (presenter, "Sarah")** | Own entitled client book; My Day, briefs, D5 memory (entitled nodes), consent gate, capture, unified review, per-item accept/edit/reject, memory correction, draft editing, **approve** send/CRM write/trade-ticket handoff, request re-rank, pin/snooze/dismiss/contacted. | Bypass an approval gate; auto-send; execute/submit a trade; view another RM's book or unentitled family nodes; disable or edit audit events; alter feed attribution. |
| **RM Manager / Observer** | Read-only oversight: rankings, reason-code evidence, approval history, team-level view, audit trail. | Approve on the RM's behalf; edit client data or drafts; change config/mode. |
| **Compliance Viewer** | Read-only: full audit events, consent records, policy/rule-pack versions, blocked-send and blocked-handoff attempts, entitlement-leakage test results. | Modify any artefact or config; see content beyond what audit requires; approve actions. |
| **Demo Operator / Data Steward** | Select scenario; `live`/`replay` switch; one-click reset; generate/load seeded data; feature flags; health panel; stage-level kill switch. | Act as the RM approver on client-facing artefacts (separation preserves credibility); edit live feed attribution or audit records; silently change mode without the label updating. |
| **System / Copilot service identity** | Ingest ticks; assemble entitled context; generate drafts; stamp versions; run policy checks; write audit events; enforce gates; persist workflow state. | Execute any client-facing or system-writing action without a recorded approval token (C-3); read outside the entitled context; ignore a kill mask. |

### 3.2 Entitlement model (requirements level) `[PRD: §6, §9, FR-5.1.3, FR-11]`

- **Client book:** each RM has an entitled client set; authorisation enforced **server-side**, with prompt revocation on role/book change. `[PRD: §9]`
- **Household / node-level entitlements:** every family or entity node carries its own entitlement set; enforcement happens **in Copilot Core context assembly**, not only in the UI — a leaked fact must never reach a generated artefact. `[PRD]`
- **DNC:** do-not-contact / channel opt-out excludes a client from outreach and blocks send **even if ranked** for risk or retention. `[PRD: §6]`
- **Channel consent:** recording consent is per client, per session, with method + timestamp + withdrawal; marketing channel consent separate. Consent is never inferred from calendar acceptance. `[PRD: FR-04]`
- **Suitability state:** gates the trade-ticket handoff (FR-20); missing/expired → Yellow at best, handoff blocked. `[PRD: §6]`

### 3.3 Audit requirement on every role

Every read of client data, every mode switch, every approval/rejection, every blocked attempt, every config/flag change and every generated artefact emits an immutable audit event with actor, role, timestamp, target, outcome, version stamps and correlation ID (C-4). **Including observer/compliance reads** — read-access logging is an `[INFERENCE]` extension beyond PRD §7 (which emphasises writes/approvals), added because "who saw what" is exactly what a banking executive will ask on stage. All five roles, including the service identity, are subject to it.

---

## 4. Elaborated functional requirements (centrepiece)

### 4.0 Cross-cutting contracts (stated once, referenced by every FR)

These are **logical** contracts, not schema DDL. Per global rule 3 (contract freeze), the architect freezes the physical data model and interface contracts in Phase 3; any change routes through the architect and is synced to Phases 2/4. `[PRD: brief §8.3]`

| ID | Contract |
|---|---|
| **C-1 Provenance envelope** | Every stored fact/artefact carries `source_id`, `source_kind` (`live_feed` / `seeded` / `replay` / `rm_manual` / `derived`), `as_of`, `ingested_at`, `confidence`, `mode`, `version_stamp`. `[INFERENCE, derived from PRD §3 D5 + §9]` |
| **C-2 Artefact states** | `draft` → `pending_review` → one of `approved` / `edited` / `rejected` / `blocked` / `stale` / `superseded`. No artefact leaves `pending_review` without C-3. `[PRD: FR-20]` |
| **C-3 Approval token** | `approver_role`, `approver_id`, `approved_at`, `artefact_id`, `final_content_hash`. Mandatory for every client-facing or system-writing action. `[PRD: FR-07, FR-15]` |
| **C-4 Audit event** | Append-only, tamper-evident within demo scope: `event_id`, `actor`, `timestamp`, `action`, `target`, `outcome`, `version_stamps`, `correlation_id`. `[PRD: §7]` |
| **C-5 Workflow instance** | `workflow_id`, `intent`, `stage_sequence`, `current_stage`, `status`, `correlation_id`, `context_refs` (D5 pointers), `kill_mask`. `[INFERENCE from PRD §3]` |

### 4.1 Requirement summary

| Area | IDs | Capability | P0/P1 |
|---|---|---|---|
| A | FR-01…04 | Live market data ingest & signal detection | P0 |
| B | FR-05…07 | Client Memory & Relationship Graph (D5) | P0 |
| C | FR-08…10 | Copilot Core orchestration | P0 |
| D | FR-11…13 | My Day & prioritisation | P0 |
| E | FR-14…15 | Pre-meeting brief | P0 |
| F | FR-16…17 | Meeting capture (lightweight) | P0 |
| G | FR-18…21 | Post-meeting unified review & approval | P0 |
| H | FR-22…23 | Outreach draft & approved send | P0 |
| I | FR-24…25 | Range moment | FR-24 P0, FR-25 P1 |
| J | FR-26…28 | Provenance, audit & trust | P0 |
| K | FR-29…32 | Demo data fabric / file–database generator | P0 |
| L | FR-33…34 | Administration & demo operations | P0 |

**34 requirements.** Each below gives actor/trigger/preconditions, a numbered primary flow covering the orchestration stage sequence, input data with provenance, output artefact + review state, 2–4 testable ACs, and boundary/exception behaviour. Exception IDs `X-…` refer to §6.

### A — Live market data ingest & signal detection

**MVP-FR-01 · Live tick ingest with entitlement & provenance** — P0 · A
*Actor/trigger/pre:* System ingest identity; on each tick; entitlement map + source credentials loaded; a scenario is active.
*Flow:* ① receive tick → ② verify licence/entitlement and attribution tag → ③ normalise instrument ID, price, currency to the canonical form → ④ stamp `source_id`, feed `as_of`, wall-clock `ingested_at`, `mode` (C-1) → ⑤ append to tick store → ⑥ emit `tick.accepted` to signal detection.
*Input + provenance:* raw tick = `<source_id>`, feed timestamp, instrument, price, licence tag; freshness ≤2s ingest lag in `live`, exact recorded time in `replay`. `[ASSUMPTION]`
*Output / state:* `market_tick` record + `tick.accepted` event; state `ingested`; provenance by construction; no human review (it is evidence, not a client-facing artefact).
*AC:* (1) Given an entitled tick, when ingested, then `source_id`/`as_of`/`ingested_at`/`mode` are all non-null and match the source payload. (2) Given a tick for an instrument outside the licensed universe, when ingested, then it is rejected with a C-4 event and appears in no UI surface. (3) Given two ticks with identical feed timestamps, when ingested, then both are addressed by a stable event key — deduplicated or retained, never silently dropped.
*Boundary (X-02, X-06):* throttle/gap → emit `feed.stale` with last-tick age; **no interpolated or invented tick**; outage degrades only the market-related section of a brief, never unrelated sections.

**MVP-FR-02 · Normalisation, as-of/staleness and outage detection** — P0 · A
*Actor/trigger/pre:* ingest service; continuous; clock synchronised; staleness thresholds configured (FR-33).
*Flow:* ① map source symbols to canonical instrument IDs → ② convert currency/unit → ③ compute feed age = now − `as_of` → ④ compare to `warn`/`stale` thresholds → ⑤ publish `feed.stale` / `feed.outage` → ⑥ update health panel.
*Input + provenance:* canonical symbol map (versioned, `seeded`), NTP-aligned clock, C-1 envelope.
*Output / state:* normalised tick; `feed_status` record (state `fresh` / `stale` / `outage`) with last-tick age.
*AC:* (1) Given age > warn threshold, when evaluated, then every affected on-screen market fact shows an amber `STALE · as-of <time>` chip. (2) Given age > stale threshold, when evaluated, then the market section shows `unavailable` and no numeric value is rendered. (3) Given clock skew between feed time and wall clock beyond tolerance, when evaluated, then the event is flagged and the tick is not used for signal detection until resolved.
*Boundary (X-03, X-04):* never substitute the last known price as if current; stale ticks remain queryable but are labelled, never deleted.

**MVP-FR-03 · Signal detection and sourced news item** — P0 · A
*Actor/trigger/pre:* signal service; on `tick.accepted`; portfolio allocations, target weights and thresholds from seeded data; a client holding matches the instrument.
*Flow:* ① join tick to entitled client/household holdings → ② compute drift vs target, threshold breach, price shock, volatility → ③ attach any entitled news item with its own `source_id`/`as_of`/headline → ④ classify signal as `Risk` / `Opportunity` / `Retention` → ⑤ emit `signal.raised` carrying full C-1 provenance → ⑥ hand to Copilot Core (FR-08).
*Input + provenance:* normalised tick (FR-01/02), seeded allocation/target weights with `as_of`, versioned threshold rule pack, licensed news item with attribution.
*Output / state:* `market_signal` artefact, state `derived`; value e.g. "Wong portfolio drifted 6% from target"; no client-facing text is published before it passes the brief/ranking approval stage.
*AC:* (1) Given a tick that pushes drift past the configured threshold, when evaluated, then exactly one `signal.raised` is emitted with the triggering tick `as_of` and the rule-pack version. (2) Given a priced news item, when attached, then it renders with headline, source and timestamp; an unlicensed item is excluded. (3) Given no threshold is crossed, when evaluated, then no signal is emitted (no noise/padding). (4) Given two consecutive ticks crossing the same threshold, when evaluated, then one signal is emitted with an updated evidence set, not two duplicate ranks.
*Boundary (X-06):* missing allocation data → signal suppressed with a `insufficient evidence` status, never guessed.

**MVP-FR-04 · Live ↔ replay mode switch with honest audience labelling** — P0 · A
*Actor/trigger/pre:* Demo Operator; on operator command or on `feed.outage`; a recorded tick stream exists for the scenario.
*Flow:* ① operator selects mode → ② record C-4 event with actor + timestamp → ③ bind ingest to live feed or recorded stream → ④ rewrite `mode` on all subsequent events (C-1) → ⑤ update the persistent audience-visible mode chip → ⑥ continue the same workflow instance (C-5) without discarding RM edits.
*Input + provenance:* operator command; recorded stream with original `as_of` timestamps preserved, labelled `replay`.
*Output / state:* `demo_mode` state (`LIVE` / `REPLAY`) + chip; workflow state preserved.
*AC:* (1) Given `live` mode, when any AI statement renders, then the chip shows `LIVE · <source> · as-of <time>`. (2) Given a switch to `replay`, when the next artefact renders, then a `REPLAY — recorded <time>` chip is present and no artefact claims a live source. (3) Given a mode switch mid-workflow, when completed, then no approved artefact is invalidated and no pending RM edit is lost. (4) Given any mode, when an executive opens the health panel, then the stated mode matches the actual ingest binding.
*Boundary (X-01, X-07):* network loss in `live` → operator (or auto-fallback rule) switches to `replay`; the switch is **announced on screen**, never silent.

### B — Client Memory & Relationship Graph (D5)

**MVP-FR-05 · One canonical evidence-backed context per client** — P0 · B
*Actor/trigger/pre:* Copilot Core on any workflow start; authorised RM/viewer; client within entitled book.
*Flow:* ① resolve client/household identity (never auto-merge ambiguous attendees) → ② assemble one canonical context from entitled nodes → ③ attach C-1 envelope to every fact → ④ surface preferences, commitments, meeting history, consent state, suitability status, confidence → ⑤ expose `context_refs` to the workflow (C-5).
*Input + provenance:* seeded facts (`source_kind=seeded`, `as_of`, `confidence`), live signals (`live_feed`), RM corrections (`rm_manual`), prior approved artefacts (`derived`).
*Output / state:* `client_context` (state `canonical`); read-only to skills except through FR-07/FR-17.
*AC:* (1) Given two skills in one workflow, when they request the client's preference, then both resolve the **same** fact ID with the same `as_of` (context reuse, no re-query/re-explanation). (2) Given a fact with confidence below threshold, when assembled, then it is labelled and excluded from client-facing assertions until reviewed. (3) Given conflicting records on one attribute, when assembled, then both sources are linked and suitability/trade handoff is blocked (X-08). (4) Given an unentitled client, when requested, then access is denied with a C-4 event and no partial context is returned.
*Boundary (X-08, X-11):* never invent a missing fact; partial context is explicitly labelled per attribute.

**MVP-FR-06 · Household / entity graph with node-level entitlements in context assembly** — P0 · B
*Actor/trigger/pre:* Copilot Core when a household/family client is in scope; entitlement matrix seeded and versioned.
*Flow:* ① load graph nodes (members, trusts, holding entities) and edges with source documents → ② resolve the requesting role's entitlement per node → ③ filter context **before** any skill sees it → ④ assemble the entitled view → ⑤ record the entitlement decision in C-4.
*Input + provenance:* seeded entity graph, source-document refs, versioned entitlement matrix, `as_of`.
*Output / state:* `entitled_context` + `entitlement_decision` audit record; state `filtered`.
*AC:* (1) Given an RM whose mandate excludes a daughter's trust, when a brief/pack is assembled, then no fact from that node appears in any generated artefact, including drafts. (2) Given two attendee classes, when packs are produced (FR-24), then the artefacts differ exactly on the entitlement boundary and both cite the matrix version. (3) Given an entitlement matrix change, when applied, then a versioned C-4 event is written and previously generated packs are marked `superseded`.
*Boundary (X-11):* a leakage attempt must be blocked in assembly, not merely hidden in UI; leakage tests are a hard demo gate (§7.2).

**MVP-FR-07 · RM inspection and correction of memory** — P0 · B
*Actor/trigger/pre:* RM; on viewing a memory chip; entitled client.
*Flow:* ① RM opens fact → ② views source, `as_of`, confidence, history → ③ corrects/deletes with a structured reason → ④ new fact version written with `source_kind=rm_manual` + C-3-style attribution → ⑤ old version retained as `superseded` → ⑥ downstream skills re-read the canonical context.
*Input + provenance:* existing fact + RM input (`rm_manual`, timestamp, approver).
*Output / state:* versioned fact; state `canonical` for new version; C-4 event.
*AC:* (1) Given a correction, when saved, then both old and new versions remain queryable with distinct timestamps. (2) Given a deleted sensitive item, when a follow-up draft is generated, then the item is absent. (3) Given a low-confidence fact, when the RM confirms it, then confidence is updated and the review flag cleared, with audit.
*Boundary:* no silent overwrite; corrections never alter `live_feed` or `seeded` provenance.

### C — Copilot Core orchestration

**MVP-FR-08 · Orchestration pipeline: intent → decomposition → sequencing → policy → gate → verify** — P0 · C
*Actor/trigger/pre:* Copilot Core; on `signal.raised` (FR-03), a calendar event, or an approved outcome (FR-21); kill mask clear.
*Flow:* ① classify intent (bounded enum, no free-form chat) → ② decompose into an ordered skill sequence (e.g. `rank.clients` → `brief.generate` → `outreach.draft`) → ③ open a C-5 workflow instance → ④ for each stage: assemble entitled context → invoke skill → attach per-skill evidence/confidence/version → ⑤ run policy checks (DNC, consent, suitability, Shariah flag, entitlement) → ⑥ **pause at each approval gate** for client-facing or system-writing stages → ⑦ after approval, execute → ⑧ verify result against the intended state and write C-4.
*Input + provenance:* `signal.raised` / calendar trigger / approved artefact; C-1 envelope on every stage input.
*Output / state:* workflow instance + stage artefacts in `pending_review` at gates; `completed` only after verify.
*AC:* (1) Given a live signal, when the workflow completes, then the stage sequence is inspectable end-to-end with one `correlation_id`. (2) Given a client-facing stage, when reached, then it is `pending_review` and no write/send occurs without C-3. (3) Given a policy check failure (e.g. DNC), when reached, then the stage is `blocked` with a reason and downstream stages are skipped. (4) Given verify detects a mismatch, when detected, then the workflow is marked failed and no false success is displayed.
*Boundary (X-09, X-14):* model/service failure → manual fallback with status, preserving RM edits; stage-level kill switch (FR-10).

**MVP-FR-09 · Workflow instance state and cross-skill context reuse** — P0 · C
*Actor/trigger/pre:* Copilot Core; for every workflow; D5 available.
*Flow:* ① persist state after each stage transition → ② pass `context_refs` (not re-fetched copies) between skills → ③ reuse computed suitability/consent/preference state → ④ record reuse in telemetry → ⑤ allow resume after interruption without restarting.
*Input + provenance:* C-5 instance + FR-05 canonical context.
*Output / state:* persistent workflow state; `completed` / `approved` / `blocked` / `abandoned` / `failed`.
*AC:* (1) Given a 3-stage workflow, when inspected, then ≥2 stages cite the same `context_refs` fact ID (no manual stitching). (2) Given an interruption at stage 2, when resumed in `replay`, then stage 1 artefacts are not regenerated or duplicated. (3) Given every workflow, when queried, then state, current stage and `correlation_id` are retrievable.
*Boundary (X-12):* partial write → state rolled forward or explicitly `failed`, never an inconsistent "complete".

**MVP-FR-10 · Stage-level kill switch; no open-ended chatbot** — P0 · C
*Actor/trigger/pre:* Demo Operator or Compliance Viewer; on anomaly; manual workflows must remain available.
*Flow:* ① operator disables a stage or skill → ② `kill_mask` set on affected workflows → ③ affected stages fall back to manual/RM-authored content with visible status → ④ audit event written → ⑤ all other stages continue.
*Input + provenance:* operator command, role, timestamp, target stage.
*Output / state:* `kill_mask` + C-4; degraded-but-auditable workflow.
*AC:* (1) Given `outreach.draft` disabled, when the workflow reaches it, then an editable blank/manual draft appears with a `manual fallback` status and no fabricated text. (2) Given any input, when it is not a bounded intent, then the workbench offers only defined workflow actions — no free-form ungrounded chat surface. (3) Given a kill switch, when later cleared, then no queued artefact is auto-released without a fresh approval.
*Boundary:* kill switch never deletes audit records or approved artefacts.

### D — Daily "My Day" & prioritisation

**MVP-FR-11 · Top N with Risk / Opportunity / Retention reason codes** — P0 · D
*Actor/trigger/pre:* RM at local start of day, or Copilot Core on `signal.raised` / FR-21 re-rank; entitled book loaded.
*Flow:* ① gather eligible clients (book, permission, consent, DNC filters) → ② score against versioned ranking policy → ③ assign ≥1 reason code with main contributing signals → ④ sort, cap at N (`[ASSUMPTION]` N=10, PRD default) → ⑤ stamp last-updated + policy version → ⑥ render with per-item evidence chips.
*Input + provenance:* `market_signal` (live `as_of`), D5 facts, seeded interactions, DNC/consent state, versioned ranking policy.
*Output / state:* `priority_list` (state `derived`, reviewable but not an outbound action); each row links to evidence.
*AC:* (1) Given a material new signal, when received, then the list re-ranks within the loop-latency target (§8 NFR-1) and shows a changed `last-updated`. (2) Given the default view, when rendered, then ≤10 unique clients appear, each with rank, ≥1 reason code and timestamp. (3) Given a client under DNC or lacking permission, when ranking, then they are excluded. (4) Given no high-priority clients, when ranking, then an empty state with criteria + last-evaluation time is shown — **never padded with weak leads**.
*Boundary (X-08, X-13):* stale signals labelled; conflicts block only affected rows.

**MVP-FR-12 · Evidence drill-down, rank-change explanation, no protected attributes** — P0 · D
*Actor/trigger/pre:* RM/Observer/Compliance; on selecting a reason or rank change.
*Flow:* ① open reason → ② show contributing signals with `source_id`, `as_of`, confidence → ③ show rank-change explanation (old rank, new rank, triggering signal, policy version) → ④ one-click client detail → ⑤ record view in C-4.
*Input + provenance:* ranking inputs + their C-1 envelopes; prior list version.
*Output / state:* read-only evidence view; audit of access.
*AC:* (1) Given any reason code, when opened, then every contributing signal resolves to a source record with a timestamp. (2) Given a rank change, when inspected, then old rank, new rank and the triggering signal are shown. (3) Given the ranking policy, when inspected by Compliance, then the feature list contains no protected attribute `[PRD: §8.8]` and the policy version is visible. (4) Given a stale signal, when displayed, then it carries an explicit stale label.
*Boundary:* explanations are faithful summaries, not rationalisations; no private chain-of-thought. `[PRD: §7]`

**MVP-FR-13 · RM controls, DNC exclusion, no padding** — P0 · D
*Actor/trigger/pre:* RM; on snooze / dismiss-with-reason / pin / mark-contacted.
*Flow:* ① RM acts → ② record action + structured reason + C-3-style attribution → ③ apply published rule to next ranking → ④ preserve original evidence → ⑤ write C-4 distinguishing AI recommendation from RM action.
*Input + provenance:* RM action (`rm_manual`), prior list version, published control rules.
*Output / state:* persisted control state; updated next list.
*AC:* (1) Given a pin, when the next re-rank runs, then the pinned client retains its position per published rules. (2) Given a dismiss-with-reason, when logged, then it is not silently treated as negative client intent. (3) Given a DNC client, when "mark contacted" or outreach is attempted, then the send is blocked (FR-23). (4) Given fewer than N qualified clients, when rendered, then the list is short, not padded.
*Boundary:* original evidence remains reviewable after any control.

### E — Pre-meeting brief

**MVP-FR-14 · Five-section sourced brief; agenda distinct from recorded facts** — P0 · E
*Actor/trigger/pre:* RM on a client/meeting, or Copilot Core on an eligible calendar event; resolvable client; authorised book.
*Flow:* ① resolve client/household (ambiguous attendees → RM selection, never auto-merge) `[PRD: FR-01]` → ② assemble entitled context → ③ build the five sections: portfolio/AUM + allocation; material changes & risk alerts (incl. live signal); recent interactions & open actions; entitled market news; proposed agenda tied to context → ④ attach a source/timestamp chip to **every** material fact, alert and news item → ⑤ visibly distinguish generated agenda items from recorded facts → ⑥ stamp data-as-of + generating RM → ⑦ set state `pending_review`.
*Input + provenance:* portfolio/holdings (`seeded`, `as_of` prior close), live signal (`live_feed`, tick `as_of`), interactions (`seeded`), news (licensed, `as_of`), D5 preferences/consent/suitability.
*Output / state:* `meeting_brief` v_n, `pending_review`; RM approves (as in narrative) before use.
*AC:* (1) Given data exists for all five, when generated, then all five sections render and every material fact has a resolvable source chip. (2) Given a generated agenda item, when rendered, then it is labelled as proposed/AI-generated, distinct from a recorded fact. (3) Given an ambiguous calendar attendee, when generating, then client selection is required and no identities are merged. (4) Given an unauthorised client, when requested, then nothing is exposed and a C-4 event is written.
*Boundary (X-02):* a failed market-news feed does **not** block portfolio or agenda sections.

**MVP-FR-15 · Partial data, per-section status, regeneration/versioning, feedback** — P0 · E
*Actor/trigger/pre:* RM; on regeneration, retry, or helpful/not-helpful feedback.
*Flow:* ① mark each section `available` / `stale` / `unavailable` with its own `as_of` → ② preserve available sections on source failure → ③ allow retry/regeneration → ④ create a new audited brief version (no CRM duplication) → ⑤ capture feedback with structured reason.
*Input + provenance:* section-level source statuses; prior brief version.
*Output / state:* `meeting_brief` v_n+1, prior version `superseded`; C-4 events.
*AC:* (1) Given a failed news feed, when the brief renders, then portfolio and agenda still render and the news section shows `unavailable` with a reason — no inferred values. (2) Given two regenerations, when inspected, then two distinct versions exist and zero duplicate CRM records were created. (3) Given feedback, when captured, then it is attributable to RM + brief version.
*Boundary:* "unavailable" is an explicit state, never a blank that looks like zero.

### F — Meeting capture (lightweight)

**MVP-FR-16 · Consent gate and recording state** — P0 · F
*Actor/trigger/pre:* RM at meeting start; consent language configured (FR-33); no capture before consent.
*Flow:* ① show consent banner with language → ② RM records client decision (accept / decline / withdraw) with method + timestamp → ③ if accepted, show persistent recording indicator and enable the **scripted** transcript injection (stub) → ④ if declined/withdrawn, disable capture and switch to manual notes → ⑤ write C-4 consent events for every state change.
*Input + provenance:* consent decision (`rm_manual`, timestamp, method); scripted transcript (`seeded`); manual notes (`rm_manual`).
*Output / state:* `consent_state` + `capture_state`; audit record.
*AC:* (1) Given no consent decision, when the meeting opens, then no audio is captured or transmitted and no recording indicator is shown. (2) Given withdrawn consent mid-meeting, when it occurs, then capture stops immediately and manual notes are offered. (3) Given any state change, when it occurs, then a consent audit event with method and timestamp exists. (4) Given calendar acceptance only, when evaluated, then consent is **not** inferred. `[PRD: FR-04]`
*Boundary (X-05, X-15):* **Stub declaration:** no real microphone/ASR; transcript is a deterministic scripted injection. This must be stated in the demo's spoken/scripted narrative, not hidden.

**MVP-FR-17 · Extracted preferences / commitments / actions, low-confidence review, memory write-back** — P0 · F
*Actor/trigger/pre:* Copilot Core after a consented capture; transcript evidence available.
*Flow:* ① produce time-stamped, speaker-labelled transcript excerpts → ② extract decisions, actions (owner/due date only if spoken), preferences, commitments, follow-up topics → ③ link each item to its transcript evidence → ④ mark low-confidence items for explicit review and suppress them from client-facing assertions → ⑤ allow RM edit/delete/correct speaker → ⑥ write accepted items back to D5 (FR-05) with `source_kind` = transcript evidence + `as_of`.
*Input + provenance:* scripted transcript (`seeded`, `as_of`), confidence, transcript offsets; RM corrections (`rm_manual`).
*Output / state:* `extraction_set` in `pending_review`; accepted items become canonical memory facts.
*AC:* (1) Given "my daughter should join", when extracted, then a `Family: daughter added · preference noted` memory chip appears with transcript evidence + timestamp. `[PRD: video §4 Seq2]` (2) Given an item with no spoken owner or date, when extracted, then those fields are blank, not guessed. (3) Given a low-confidence item, when a follow-up draft is generated, then it is absent until RM review. (4) Given a deleted sensitive item, when memory is queried, then it is excluded from generated artefacts.
*Boundary (X-09, X-12):* audio loss / provider failure → last confirmed transcript position shown, retry never duplicates meetings/actions, and **no fabricated "complete" transcript**. `[PRD: FR-06]`

### G — Post-meeting unified review & approval

**MVP-FR-18 · One unified review surface with old/new preview and per-item disposition** — P0 · G
*Actor/trigger/pre:* RM at meeting end; capture/extraction complete or manual notes present.
*Flow:* ① assemble **one** review surface: notes, CRM field changes (old → proposed new), tasks, preferences, follow-up email draft, rebalancing proposal / trade-ticket fields, and tomorrow's re-ranked priorities → ② attach source evidence per item → ③ RM accepts / edits / rejects **each item** or rejects all → ④ record explicit `approver_role` + `approver_id` + `approved_at` (C-3) on the single **Approve** tap → ⑤ write C-4.
*Input + provenance:* accepted extraction items, current CRM seeded values, D5 memory, ranking output; all with C-1.
*Output / state:* `post_meeting_review` in `pending_review` → `approved` (nothing written/sent/submitted before the tap).
*AC:* (1) Given the review before Approve, when inspected, then zero CRM writes, zero sends and zero ticket submissions exist. (2) Given any item, when selected, then its source evidence is displayed. (3) Given the final review, when inspected, then approver identity and timestamp are recorded. (4) Given "reject all", when applied, then no downstream artefact is created.
*Boundary:* RM edits are preserved across any regeneration; old/new preview always shown for CRM changes. `[PRD: FR-07/08]`

**MVP-FR-19 · Idempotent CRM write; email draft never auto-sent** — P0 · G
*Actor/trigger/pre:* on approval of FR-18; CRM demo sink configured; email channel consent + DNC checked.
*Flow:* ① for each accepted CRM change, write via an idempotency key → ② show sync status (`succeeded` / `pending` / `failed`) → ③ on failure retain editable draft with visible status and safe retry → ④ place the follow-up email in the RM's editable workflow in state `draft` → ⑤ recipients confirmed by RM → ⑥ no send occurs.
*Input + provenance:* approved changes (C-3), configured field mapping (versioned, FR-33), email template + disclosure version.
*Output / state:* CRM records updated (sink) with old/new history; `email_draft` state `draft`; C-4 events.
*AC:* (1) Given the same approval retried, when processed, then exactly one CRM change exists (idempotency). (2) Given approval, when inspected, then the email is `draft`, not `sent`. (3) Given a rejected or withdrawn-consent extracted item, when drafts are built, then it is absent. (4) Given a sink failure, when it occurs, then status is `failed`/`pending` with safe retry — **never false success**.
*Boundary (X-09, X-12):* outage never reports success prematurely; edits preserved. `[PRD: §6]`

**MVP-FR-20 · Pre-filled trade-ticket handoff with hard blocks** — P0 · G
*Actor/trigger/pre:* only where explicitly discussed in the meeting and supported by seeded integration; current suitability status required.
*Flow:* ① pre-fill product, account, amount from approved meeting evidence → ② link back to evidence → ③ check mandatory fields + current suitability + conflicting records → ④ if any hard block, stop with a clear reason → ⑤ present as a **handoff only**.
*Input + provenance:* approved meeting evidence, suitability status (`as_of`), account data (`as_of`), conflict flags.
*Output / state:* `ticket_handoff` state `blocked` or `ready_for_manual_handoff`; **no submission path exists**.
*AC:* (1) Given missing/expired suitability, when evaluated, then the handoff is `blocked` with a reason and rating is Yellow at best. `[PRD: §6]` (2) Given conflicting records, when evaluated, then the handoff is blocked and both sources linked. (3) Given all mandatory fields present, when evaluated, then the ticket is pre-filled but the workbench offers no approve/execute/submit action. (4) Given any attempt to auto-submit, when attempted (X-16), then it is blocked, logged, and shown on the health panel.
*Boundary:* AI cannot submit, approve or execute a trade `[PRD: FR-10]`; execution is a permanent non-goal.

**MVP-FR-21 · Approved outcomes trigger re-rank (loop closure)** — P0 · G · **headline requirement**
*Actor/trigger/pre:* on FR-18 approval; new preference/commitment written to D5.
*Flow:* ① commit approved memory changes → ② emit `outcome.approved` with correlation ID → ③ Copilot Core opens a new workflow (FR-08) → ④ `rank.clients` re-runs with the new context → ⑤ next briefs are regenerated/re-versioned carrying the new preference → ⑥ display "tomorrow's re-ranked priorities" and the changed rank explanation → ⑦ write C-4.
*Input + provenance:* approved memory facts (`rm_manual` + transcript evidence), prior list version, live signals.
*Output / state:* new `priority_list` version + updated brief version; state `derived`; audit-linked to the approval.
*AC:* (1) Given an approved new preference, when the loop completes, then the re-ranked list is visibly different and the change is explained by that outcome. (2) Given the next brief, when generated, then it contains the newly approved preference with its source. (3) Given the whole loop, when inspected by `correlation_id`, then live signal → brief → review → approval → re-rank are all linked. (4) Given no approval, when the meeting ends, then no re-rank based on unapproved content occurs.
*Boundary:* the loop closes on **approved** facts only; unapproved/low-confidence facts never propagate.

### H — Outreach draft & approved send

**MVP-FR-22 · Grounded, editable outreach draft** — P0 · H
*Actor/trigger/pre:* RM from an approved reason code (FR-11/12); DNC + channel consent clear.
*Flow:* ① take the approved reason → ② assemble three required elements: reason for contact, permitted portfolio facts, client-relevant conversation opener → ③ apply selected channel/template + disclosures → ④ link every factual statement to evidence → ⑤ omit unavailable facts rather than invent → ⑥ present fully editable, state `draft`.
*Input + provenance:* approved reason code + evidence (`as_of`), D5 preferences, template/disclosure versions.
*Output / state:* `outreach_draft`, `pending_review`.
*AC:* (1) Given data exists, when generated, then all three content elements are present. (2) Given a factual statement, when inspected, then it links to evidence; no unlinked numeric claim appears. (3) Given a missing fact, when generated, then it is omitted, never invented. (4) Given the draft, when the RM edits it, then the edited text becomes the version subject to approval.
*Boundary:* draft cannot be scheduled or sent from this requirement.

**MVP-FR-23 · Policy checks, explicit approved send, full audit** — P0 · H
*Actor/trigger/pre:* RM on Approve & Send; FR-22 draft exists; demo sink active.
*Flow:* ① run DNC, channel-consent, disclosure and restricted-content checks → ② if any fails, `blocked` with reason (no bypass) → ③ RM explicitly approves (C-3) → ④ send to demo sink, record status → ⑤ log final content, approver, template version, model/prompt version, provider status → ⑥ on failure expose status + safe idempotent retry.
*Input + provenance:* final edited content, C-3 token, version stamps, sink status.
*Output / state:* `outreach_send` `approved`/`sent-to-demo-sink`/`blocked`/`failed`; C-4 event.
*AC:* (1) Given no explicit approval, when the demo runs, then zero sends occur. (2) Given a DNC client or opted-out channel, when send is attempted, then it is blocked and logged — even if ranked for risk. `[PRD: §6]` (3) Given a send, when audited, then final content + approver + timestamp + template/model version are retrievable. (4) Given a sink failure, when it occurs, then status is `failed` with safe retry and no false success.
*Boundary (X-16):* **no auto-send, ever**; the demo sink has zero external egress.

### I — Range moment

**MVP-FR-24 · Family entity graph with per-attendee entitled pack versions** — P0 · I
*Actor/trigger/pre:* RM on the Tan-family scenario; FR-06 entitlement matrix loaded.
*Flow:* ① unfold the seeded entity graph (patriarch → trusts → holding entities → daughter's trust) → ② assemble a consolidated family view → ③ generate a meeting pack → ④ split into per-attendee entitled versions using FR-06 context assembly → ⑤ label each version with its attendee class + matrix version.
*Input + provenance:* seeded entity graph + source-document refs, entitlement matrix (versioned), `as_of`.
*Output / state:* `family_pack` versions in `pending_review`; each `approved` before presentation.
*AC:* (1) Given two attendee classes, when packs are generated, then each contains only its entitled nodes (verified by a leakage test). (2) Given the daughter's version, when inspected, then no fact from the patriarch's excluded nodes appears in any field, including hidden/draft text. (3) Given every pack, when inspected, then the entitlement-matrix version and `as_of` are shown. (4) Given an RM confirmation step, when an AI-extracted structure is used, then it became canonical only after confirmation. `[PRD: FR-5.1.1]`
*Boundary (X-11):* enforcement in context assembly, not UI; any cross-node leakage fails the demo gate.

**MVP-FR-25 · Shariah preference propagation and labelling** — **P1, feature-flag OFF by default** · I
*Actor/trigger/pre:* operator enables the optional beat; a Shariah-sensitive flag exists in D5; a candidate product list is displayed.
*Flow:* ① read Shariah-sensitive preference from canonical memory → ② propagate to any displayed product/proposal surface → ③ **exclude non-compliant candidates by construction** (never surface with a disclaimer as a workaround) → ④ attach `Screened to client's stated standard · methodology disclosed` evidence → ⑤ label the giving/estimate summary `Estimate for discussion — confirm with your Shariah advisor` and `Not a fatwa`.
*Input + provenance:* D5 preference (`seeded`, `as_of`), seeded screening outcomes with per-criterion source + date, rule-pack version.
*Output / state:* filtered surface + labelled summary, `pending_review`.
*AC:* (1) Given a Shariah-sensitive client, when any product surface renders, then zero non-compliant candidates appear. (2) Given any estimate output, when rendered, then both `Estimate for discussion` and `Not a fatwa` labels are present and cannot be removed by config. `[PRD: FR-4.2.1]` (3) Given a product without current screening evidence, when evaluated, then it cannot be marked compliant.
*Boundary:* **no** screening engine, zakat math, purification, SSB sign-off or fatwa issuance in the MVP; this is a static seeded propagation beat. First to cut if scope tightens (§2.2).

### J — Provenance, audit and trust

**MVP-FR-26 · Evidence chip on every AI statement** — P0 · J
*Actor/trigger/pre:* any rendering surface, any workflow, any mode.
*Flow:* ① for each AI-generated statement, resolve C-1 envelope → ② render source + timestamp chip (`Portfolio, as of 09:58` / `Client preference, verified` / `Trust deed, reviewed by Sarah`) → ③ make the chip open the originating record or entitled source detail → ④ in `replay`, add the `REPLAY` label (FR-04).
*Input + provenance:* C-1 on the underlying artefact.
*Output / state:* chip + resolvable link; C-4 view event.
*AC:* (1) Given the golden path, when sampled, then 100% of AI statements have a non-empty source/timestamp chip. `[PRD: video §7]` (2) Given a chip click, when opened, then the originating record/source detail is shown. (3) Given a `replay` artefact, when rendered, then no chip claims a live source. (4) Given a low-confidence fact, when rendered, then it is labelled and not asserted client-facing.
*Boundary:* a statement with no provenance must not render — it is suppressed with a `insufficient evidence` status, never shown bare. `[INFERENCE]`

**MVP-FR-27 · Immutable audit events and version stamping** — P0 · J
*Actor/trigger/pre:* every role and the service identity; on every event defined in §3.3.
*Flow:* ① construct C-4 event → ② append (no update/delete path) → ③ stamp model, prompt, template, ranking-policy and rule-pack versions on generated artefacts → ④ expose a Compliance Viewer query by actor / time / correlation ID / target.
*Input + provenance:* all workflow events; version registry (FR-33).
*Output / state:* append-only audit log; tamper-evident within demo scope.
*AC:* (1) Given every approval, mode switch, config change, blocked attempt and generated artefact in a run, when queried, then a matching C-4 event exists. (2) Given any generated artefact, when inspected, then its model/prompt/template/rule-pack versions are present. (3) Given an attempt to modify an audit event, when attempted, then it is denied and the attempt is logged. (4) Given observer/compliance reads, when queried, then read-access events are present.
*Boundary:* kill switch and reset never erase the audit log of the completed run; reset archives it (FR-32).

**MVP-FR-28 · Explainability of material recommendations** — P0 · J
*Actor/trigger/pre:* any material recommendation (rank change, rebalancing proposal, outreach reason).
*Flow:* ① list source data + `as_of` → ② give a concise user-facing rationale → ③ state confidence/limitations → ④ suppress private chain-of-thought and unrelated client data. `[PRD: §7/§8.3]`
*Input + provenance:* the recommendation's C-1 evidence set.
*Output / state:* explanation attached to the artefact; state `pending_review` where client-facing.
*AC:* (1) Given a rebalancing proposal, when inspected, then the drift figure, its tick `as_of`, and the client preference it respects are shown. (2) Given any explanation, when rendered, then no chain-of-thought and no other client's data appear. (3) Given an unsupported claim, when detected, then it is flagged rather than rationalised.
*Boundary:* explanation must be a faithful summary of the evidence actually used, not a post-hoc justification. `[INFERENCE, from PRD §8.3]`

### K — Demo data fabric / file–database generator (REQUIREMENTS, not solution)

> These are requirements with acceptance criteria. The architect designs the implementation, including which Postgres extensions are used. No technical solution is specified here.

**MVP-FR-29 · Deterministic seed and manifest / schema contract** — P0 · K
*Actor/trigger/pre:* Demo Operator before a run; a single named seed value is supplied.
*Flow:* ① accept one seed → ② generate the full synthetic world (clients, books, households/entities, holdings, targets, interactions, consent, suitability, preferences, products, news, rule packs, scenario definitions) → ③ emit a **manifest** declaring every emitted file/table, row counts, schema version, field-level provenance rules, seed and generation timestamp → ④ freeze the schema contract (global rule 3).
*Input + provenance:* single seed + versioned schema contract; every generated fact is `source_kind=seeded` with `as_of` + `confidence` (C-1).
*Output / state:* manifest + schema contract + generated dataset; state `generated`.
*AC:* (1) Given the same seed and schema version, when generated twice, then the manifest checksum is identical. (2) Given the manifest, when inspected, then every emitted file/table and its row count is declared and matches the output. (3) Given any generated fact, when queried, then `source_kind`, `as_of` and `confidence` are non-null. (4) Given a schema version change, when applied, then it is recorded and routed through the architect before any downstream artefact is regenerated.
*Boundary:* a manifest/schema mismatch blocks the run (fail loud), never a partial silent load.

**MVP-FR-30 · `seed` / `replay` / `live` modes; flat-file emission + Postgres population** — P0 · K
*Actor/trigger/pre:* operator selects mode; Postgres target reachable; `[INFERENCE]` "postgres plugin" interpreted as Postgres extensions (candidate set: TimescaleDB for ticks, pgvector for memory retrieval, pg_cron for scheduled refresh, `file_fdw`/`postgres_fdw` for flat-file ingest) — **selection and justification belong to the architect (Phase 3)**; alternative reading = an IDE/WorkBuddy Postgres connector or a BI plugin, flagged in §9.
*Flow:* ① `seed`: emit flat files (CSV/JSON/Parquet) **and** load the same logical dataset into Postgres → ② `replay`: emit/load the recorded tick stream with original `as_of` → ③ `live`: leave the store seeded but bind ingest to the real feed → ④ verify flat-file and database views agree → ⑤ write C-4.
*Input + provenance:* seed, schema contract, recorded stream, live feed; C-1 on every row in all three modes.
*Output / state:* flat-file set + populated Postgres + manifest; state `loaded` / `live-bound`.
*AC:* (1) Given `seed`, when complete, then flat files **and** populated Postgres tables both exist and describe the same logical dataset (row counts + key checksums match). (2) Given `replay`, when loaded, then tick `as_of` values equal the recorded stream and `source_kind=replay`. (3) Given `live`, when bound, then ingest provenance points to the external `source_id`, not to `seeded`. (4) Given Postgres unavailable, when `seed` runs, then the run fails with a visible status — no half-loaded world presented as ready.
*Boundary:* **at least one Postgres extension must be used and justified** `[PRD: brief §3 R6]`; no extension is added without a stated purpose (global rule 1).

**MVP-FR-31 · Referential integrity, as-of + provenance on every fact, reproducibility** — P0 · K
*Actor/trigger/pre:* on every generation/load.
*Flow:* ① enforce referential integrity across clients ↔ books ↔ households ↔ nodes ↔ holdings ↔ signals ↔ artefacts ↔ audit → ② reject orphan references → ③ stamp C-1 on every fact → ④ compute a dataset checksum → ⑤ verify replay reproducibility from the single seed.
*Input + provenance:* generated dataset + schema contract.
*Output / state:* integrity report + checksum; state `verified` / `failed`.
*AC:* (1) Given a completed load, when validated, then zero orphan foreign keys and zero facts lacking provenance. (2) Given a deliberately broken reference in a test fixture, when validated, then the run fails loudly with the offending record. (3) Given one seed, when two independent runs complete, then checksums are equal. (4) Given any market tick, when queried, then `as_of` + `source_id` + `mode` are present in both the flat file and Postgres views.
*Boundary:* integrity failure blocks the demo start; never auto-repair by inventing a parent record.

**MVP-FR-32 · Reset / restore between demo runs; declared demo-data boundary** — P0 · K
*Actor/trigger/pre:* Demo Operator between runs or after a failed run; one command.
*Flow:* ① archive the completed run's audit log (FR-27) → ② restore the store and flat files to the exact seeded baseline for the chosen scenario → ③ clear workflow state, approvals, drafts and kill masks → ④ re-verify integrity + checksum → ⑤ show `READY` on the health panel.
*Input + provenance:* chosen scenario + seed; archived audit.
*Output / state:* clean baseline; state `ready`; C-4 reset event.
*AC:* (1) Given a reset, when complete, then the dataset checksum equals the seeded baseline and no artefact from the prior run is queryable except the archived audit. (2) Given a reset, when timed, then it completes within §8 NFR-9. (3) Given any generated artefact or UI label, when inspected, then it is identifiable as **demo data** — the generator is explicitly declared a *demo data* tool, **not a production data migration tool**. (4) Given an accidental attempt to point the generator at a real data source, when configured, then it is blocked by the no-real-data rule (§9 A4).
*Boundary:* reset never deletes the compliance archive; reproducibility survives repeated resets.

### L — Administration & demo operations

**MVP-FR-33 · Configuration without code deployment + feature flags** — P0 · L `[PRD: FR-22]`
*Actor/trigger/pre:* Demo Operator / authorised admin; at any time before or between runs.
*Flow:* ① edit config (thresholds, ranking/reason-code policy, templates/disclosures, consent language, field mappings, feature flags, scenario selection, source attribution) through the admin surface → ② version + validate → ③ write C-4 → ④ apply without rebuild/redeploy → ⑤ show active versions on the health panel.
*Input + provenance:* operator input with role + timestamp; version registry.
*Output / state:* active, versioned config; C-4 events.
*AC:* (1) Given a threshold change, when applied, then the next signal evaluation uses the new value with no redeploy. (2) Given any config change, when applied, then old and new versions are both queryable with actor/timestamp. (3) Given the Shariah flag (FR-25), when OFF, then no Shariah surface renders. (4) Given an invalid config, when applied, then it is rejected and the previous version stays active.
*Boundary:* config cannot disable provenance chips, approval gates, consent banner, the mode chip or the `Estimate for discussion` label — these are non-negotiable. `[PRD: video §6/§7]`

**MVP-FR-34 · Audience-visible mode switch, one-click reset, health panel, seeded scenario library** — P0 · L
*Actor/trigger/pre:* Demo Operator; before and during the run; ≥3 named scenarios seeded.
*Flow:* ① show a persistent, audience-visible status panel: `mode`, `source`, `last tick as-of`, `feed age`, `scenario`, `workflow stage`, `blocked-attempt count`, `integrity state` → ② expose `live`/`replay` switch (FR-04) and one-click reset (FR-32) → ③ load a named scenario → ④ keep the panel accurate within the demo loop.
*Input + provenance:* FR-02 feed status, FR-09 workflow state, FR-31 integrity, FR-27 audit, scenario definitions.
*Output / state:* health/status panel + scenario library; all changes audited.

| Scenario | Triggering market event | What it proves |
|---|---|---|
| **S1 "Wong Drift"** (golden path) | Live price move on a Wong holding → drift >6% from target `[PRD: video §4 Seq1]` | Live event → full loop → re-rank → approval. |
| **S2 "Rahman Review"** | Entitled news item + price tick on a faith-sensitive holding | Optional Shariah/estimate beat (FR-25), `replay`-safe. |
| **S3 "Tan Family Pack"** | Volatility/price-shock signal on a family holding | Entity graph + two entitled pack versions (FR-24), no cross-node leakage. |
| **S4 "Feed Outage"** (fallback) | `feed.outage` / network loss during the run | Honest stale state + labelled `replay` fallback (§5.2). |

*AC:* (1) Given any moment of the demo, when an executive looks at the panel, then `mode`, `last tick as-of` and `feed age` are visible and correct. (2) Given ≥3 named scenarios, when listed, then each declares its triggering market event. (3) Given one-click reset, when invoked, then the panel returns to `READY` and the integrity state is `verified`. (4) Given a blocked auto-send/auto-trade attempt, when it occurs, then the blocked-attempt count increments and is visible.
*Boundary:* the panel must never show `LIVE` while bound to `replay`; accuracy of this label is a demo acceptance gate (§7.2).

---

## 5. End-to-end demo scenario (golden path)

### 5.1 Timed walkthrough — "a live event becomes a re-ranked day"

Elapsed time is demo time, not wall-clock implementation time. `[INFERENCE]`

| T | Step | On-screen evidence | Human approval | FR |
|---|---|---|---|---|
| −00:30 | Operator loads **S1**, `live` mode, one seed; health panel `READY · LIVE · integrity verified`. | Mode chip, scenario name, integrity state. | — | 30, 31, 34 |
| +00:00 | A genuine live tick arrives (Wong holding). | `MARKET EVENT · <instrument> · <source> · as-of 09:58:14 SGT`; provenance chip. | — | 01, 02 |
| +00:02 | Signal detection fires. | `Wong portfolio drifted 6% from target · Risk/Opportunity · tick as-of 09:58:14 · rule-pack v1`. | — | 03, 26 |
| +00:04 | Copilot Core opens a workflow; intent = "material market signal → re-evaluate day". | Workflow stage trace with one `correlation_id`; context refs reused from D5. | — | 08, 09, 05 |
| +00:06 | **My Day re-ranks.** | Wong 4→1 with reason `Opportunity — rebalancing`; rank-change explanation; 2 retention-risk clients; no padding. | — | 11, 12, 13 |
| +00:08 | RM opens Wong's brief. | Five sections, each with source chips; drift alert carries the live tick `as-of`; one section honestly labelled `portfolio as-of prior close`; agenda items tagged "proposed". | RM edits one agenda line and approves the brief. | 14, 15, 26 |
| +00:10 | 10:00 meeting (compressed). | Consent banner → client agrees → persistent recording indicator → `Family: daughter added · preference noted` memory chip with transcript evidence + confidence. | **Consent is the first human gate.** | 16, 17 |
| +00:14 | Meeting ends → **one review screen**. | Notes, CRM old→new preview, follow-up email draft, rebalancing proposal, trade-ticket handoff showing `suitability current · execution disabled`, tomorrow's re-ranked priorities — all on one surface. | — | 18, 19, 20 |
| +00:16 | RM edits two lines, taps **Approve**. | `Approved by Sarah (RM) · 10:14:32`; CRM `succeeded` (sink, idempotent); email stays `draft · DEMO SINK — not delivered`; zero sends, zero trades. | **The single decisive human approval.** | 18, 19, 27 |
| +00:18 | **The loop closes.** | Approved preference propagates → new `priority_list` version with changed-rank explanation → tomorrow's brief already carries "daughter to join". Live signal → brief → review → approval → re-rank all linked by one `correlation_id`. | — | 21, 07, 27 |
| +00:20 | Range beat (optional, 30s). | Tan entity graph → two entitled pack versions (`Mr. Tan` / `Next-gen`); if S2 enabled, `Estimate for discussion · Not a fatwa` label and zero non-compliant candidates. | Pack versions approved before presentation. | 24, 25 |
| End | Tagline card. | *"AI orchestrates the workflow. You orchestrate the relationship. / Human-approved. Always."* | — | `[PRD]` |

**Every AI statement in this path has a source/timestamp chip; every outbound action has a human tap.** `[PRD: video §7]`

### 5.2 Alternative / fallback scenarios

**F1 — Feed outage or network loss during the demo.** At +00:03 the feed drops. Audience sees: an amber `FEED STALE · last tick 09:58:14 · age 47s` chip on every affected fact; the brief's market section switches to `unavailable` while portfolio/agenda sections remain; **no invented tick and no last-price substitution**; the health panel shows `feed age` climbing. The RM's pending edits are preserved. The operator flips to `replay` and the permanent chip changes to `REPLAY — recorded 09:58`, with a C-4 event and a spoken line that this is intentional. The loop then completes deterministically. *What leadership should conclude:* the system degrades honestly and never claims a success it did not have — arguably a stronger trust proof than the happy path. `[INFERENCE]` (FR-02, FR-04, FR-15, FR-34; X-01, X-02)

**F2 — Consent declined / withdrawn.** At +00:10 the client declines (or withdraws mid-meeting). Audience sees: consent banner, `Declined` recorded with method + timestamp, **no recording indicator, no audio captured**, immediate switch to `MANUAL NOTES`. No transcript evidence exists; memory write-back comes only from RM-typed notes labelled `source_kind=rm_manual`. The unified review still assembles (notes, CRM preview, email draft, re-rank) but every derived fact is marked low-confidence and requires explicit review before it can propagate. *What leadership should conclude:* the gate is real, not decorative, and the loop still closes — with lower-confidence, human-reviewed facts. `[INFERENCE]` (FR-16, FR-17, FR-21; X-05, X-15)

---

## 6. Consolidated exception & boundary requirements

`X-01…X-08`, `X-15`, `X-16` are demo-specific; the remainder are derived from PRD §6. `[PRD]` / `[INFERENCE]` tags apply to the *source*, not to the required behaviour.

| ID | Scenario | Required observable behaviour |
|---|---|---|
| X-01 | Network loss / feed outage mid-demo | Amber `STALE` chip with last-tick age; unrelated sections unaffected; pending drafts/edits preserved; explicit, labelled switch to `replay`; no false success. `[PRD]` |
| X-02 | Source unavailable or stale | Partial output with per-section status + `as-of`; **never invent, interpolate or silently substitute** data. `[PRD]` |
| X-03 | Stale tick beyond threshold | Numeric value removed, section `unavailable`; stale record stays queryable but labelled. |
| X-04 | Clock skew (feed vs wall clock) | Event flagged; tick withheld from signal detection until resolved; no fabricated `as_of`. `[INFERENCE]` |
| X-05 | Client declines / withdraws recording consent | No capture (or immediate stop); manual notes offered; consent audit preserved. `[PRD]` |
| X-06 | Provider throttle / rate limit | Backoff + visible `pending` status; no duplicate tick or duplicate signal; loop resumes or falls back to `replay`. `[INFERENCE]` |
| X-07 | Mode switch mid-workflow | Label updates before the next artefact; workflow state, approvals and RM edits preserved. |
| X-08 | Conflicting client / portfolio records | Both sources linked; suitability assessment and trade-ticket handoff blocked until authoritative resolution. `[PRD]` |
| X-09 | CRM / email / SMS provider (sink) outage | Editable draft retained; `pending`/`failed` status visible; idempotent retry; **never premature success**. `[PRD]` |
| X-10 | Low AI confidence / insufficient evidence | Item labelled, explicit review required, client-facing assertion suppressed. `[PRD]` |
| X-11 | Intra-family entitlement boundary | Filtered in **context assembly**; zero cross-entity leakage in any artefact including drafts; leakage test is a hard gate. `[PRD]` |
| X-12 | Duplicate event / partial write | Stable event key; no duplicate meetings/actions/CRM writes; inconsistent state shown as `failed`, never `complete`. `[PRD: FR-06/08]` |
| X-13 | No high-priority clients | Empty state with criteria + last-evaluation time; **never pad** Top N with weak leads. `[PRD]` |
| X-14 | Model / service failure | Manual fallback with visible status; RM edits preserved; audit intact; stage-level kill switch available. `[PRD]` |
| X-15 | Real recording/ASR attempted on stage | Blocked by stub declaration; no microphone capture; stated in the demo narrative. `[ASSUMPTION]` |
| X-16 | Accidental auto-send / auto-trade attempt | Blocked by construction (no execution path); C-4 event; blocked-attempt counter increments on the health panel. `[PRD: §12 + INFERENCE]` |
| X-17 | DNC / channel opt-out | Excluded from outreach; send blocked even if ranked for Risk/Retention. `[PRD]` |
| X-18 | No suitable product / hard filter | No-result explanation; **never auto-relax a hard filter**; for Shariah-sensitive clients non-compliant candidates excluded by construction. `[PRD]` |
| X-19 | Suitability missing / expired | Yellow at best; trade-ticket handoff blocked with a clear reason. `[PRD]` |
| X-20 | Generator integrity / schema mismatch | Fail loud, block demo start; never auto-repair by inventing a parent record. `[INFERENCE]` |

**Non-negotiable prohibitions (apply to every requirement above):** ❌ no fabricated data; ❌ no false success; ❌ no auto-send; ❌ no auto-trade/auto-execute; ❌ no unlabelled `replay` presented as `live`; ❌ no removal of provenance chips, consent banner, approval taps or the "estimate for discussion" label.

---

## 7. Measurable acceptance criteria for the MVP as a whole

### 7.1 Demo success criteria — what leadership must be able to verify

| # | Verifiable claim | How an executive verifies it on stage |
|---|---|---|
| D1 | A real live event enters and changes the UI within seconds | Watch the `as-of` timestamp on the tick chip match a wall clock; see the re-rank appear within the loop target (§8 NFR-1). |
| D2 | Every AI statement is sourced | Click any chip; it opens an originating record with a timestamp. Sample any 10 statements: 10/10 resolve. |
| D3 | Every outbound action is human-approved | Observe the single Approve tap; confirm CRM `succeeded` but email `draft`, zero sends, zero trades; open the audit entry to see approver + timestamp. |
| D4 | The loop closes | The approved "daughter to join" preference appears in the re-ranked list **and** in tomorrow's brief within the same session. |
| D5 | Provenance survives a mode switch | The `REPLAY` chip is present and accurate; no artefact claims a live source. |
| D6 | Deterministic reproducibility | Run S1 twice from one seed; manifest checksums and artefact sequences are identical. |
| D7 | One-click recovery | Reset returns the panel to `READY` with `integrity verified` within the reset target. |
| D8 | Range moment respects entitlements | The two pack versions differ exactly on the entitlement boundary; no excluded-node fact appears. |
| D9 | Honest degradation | Trigger F1: stale/unavailable labels appear; no fabricated number; the fallback is announced. |
| D10 | Honest scope | Ask "what is real?" — the operator answers precisely for every element using §1.1, and the `SYNTHETIC DEMO DATA` label is visible. |

### 7.2 Pass/fail gate list (binary — any failure blocks the demo)

| Gate | Pass condition |
|---|---|
| G1 | 100% of golden-path AI statements have a resolvable source/timestamp chip (FR-26). |
| G2 | Zero auto-sends, zero auto-trades, zero submissions without a C-3 approval token (FR-19/20/23). |
| G3 | Live tick → visible re-rank completes within NFR-1 in `live` mode; identical sequence in `replay` (FR-03/11/21). |
| G4 | Single-seed reproducibility: manifest checksums equal across two runs (FR-29/31). |
| G5 | Flat-file and Postgres views agree on row counts + key checksums; ≥1 Postgres extension used with a stated purpose (FR-30). |
| G6 | Referential integrity: zero orphan references, zero facts without provenance (FR-31). |
| G7 | Entitlement leakage test passes: zero cross-node facts in any artefact (FR-06/24). |
| G8 | Mode label accuracy: `LIVE` never shown while bound to `replay` (FR-04/34). |
| G9 | Outage fallback (F1) and consent decline (F2) each complete with labelled, honest states and no fabricated data. |
| G10 | One-click reset archives audit, restores baseline checksum, completes within NFR-9 (FR-32). |
| G11 | Non-negotiable labels (consent banner, approval taps, `Estimate for discussion` when enabled) cannot be disabled by config (FR-33). |

### 7.3 Demo acceptance ≠ production-grade acceptance

The following are **explicitly NOT claimed** by this MVP. Claiming them would be dishonest. `[INFERENCE]`

| Not claimed | Why | Disposition |
|---|---|---|
| SOC 2 / attestation, enterprise RBAC certification | Synthetic data, no production deployment, stubbed SSO | Deferred to PRD GA gates |
| 1,000 concurrent users; 99.5% monthly uptime; tenant workload isolation at scale | One presenter + ≤5 observers · `[ASSUMPTION]` | Relaxed to demo-window availability (NFR-4) |
| EU/US/APAC/GCC residency, cross-border flow documentation | No real PII, single local environment | Deferred |
| Real vendor integrations (core banking, CRM, email, calendar, market-data licence in production) | Stubbed / one demo feed | Deferred |
| Real ASR accuracy, multi-model quality, eval harness / hallucination-rate claims | Deterministic canned outputs | Deferred |
| Retention lift, adoption, 4–6 hrs/week saved, touchpoint growth | Longitudinal outcome; cannot be measured in a 20-minute demo `[PRD: §10/§14.7]` | **Never** claim on stage |
| Backup/DR objectives, zero provider retention attestation | No production data and no real provider egress | Retained as *design posture* only |

**Gate philosophy:** a demo passes when the *orchestration, provenance, approval and closed-loop* claims are visibly true and reproducible — not when production NFRs are met. `[INFERENCE]`

---

## 8. NFR inputs for the architect (not the final NFR spec)

Prioritised concerns with proposed measurable targets **suitable for an MVP demo**. The architect owns the final NFR specification, component design and dataflow; this is a feed, not a duplicate. `[INFERENCE]`

| # | Concern | Proposed MVP demo target | Priority |
|---|---|---|---|
| NFR-1 | Live-event → UI loop latency | From tick ingest to visible re-ranked card ≤10s p95; tick ingest-to-store ≤2s p95. Retains the *spirit* of PRD brief <10s p95, re-targeted to the loop. | P0 |
| NFR-2 | Freshness / staleness | `warn` at 30s feed age, `stale/outage` at 120s; every affected fact labelled. `[ASSUMPTION]` | P0 |
| NFR-3 | Determinism | Same seed + same mode → identical manifest checksum and artefact sequence; `replay` bit-reproducible. | P0 |
| NFR-4 | Availability during the demo | 100% over the ~20-minute demo window via `replay` fallback; golden path has **no dependency** on external LLM/CRM/network in `replay`. | P0 |
| NFR-5 | Auditability | 100% of approvals, mode switches, config changes, blocked attempts, generated artefacts and client-data reads carry actor/role/timestamp/version stamps; append-only within demo scope. | P0 |
| NFR-6 | Security / privacy minimums (even for synthetic data) | No real PII; book + node entitlements enforced server-side; no secrets in the repo; demo sink has zero external egress; TLS on any live feed hop. | P0 |
| NFR-7 | Accessibility | WCAG 2.1 AA on the presenter surface; keyboard-operable approval; non-colour-only status indicators (amber/text labels). | P1 |
| NFR-8 | Observability | Health panel with `mode`, `source`, `last tick as-of`, `feed age`, `scenario`, `workflow stage`, `blocked-attempt count`, `integrity state`; one `correlation_id` per workflow. | P0 |
| NFR-9 | Recoverability / reset | One-click reset to clean seeded baseline ≤60s `[ASSUMPTION]`, with audit archived and integrity re-verified. | P0 |
| NFR-10 | Scale | 1 presenter session + ≤5 observer sessions. | P1 |

### 8.1 Disposition of PRD §7 targets

| PRD §7 area | Disposition | Justification |
|---|---|---|
| Brief <10s p95 | **Retained / re-targeted** | Folded into NFR-1 as loop latency; brief is generated inside the loop, so this is the honest measurement. |
| Product search <5s p95 | **N/A — deferred** | E3 search is out of MVP scope. |
| 1,000 concurrent users | **Relaxed** → NFR-10 | Single-screen demo; load testing adds zero demo value. |
| 99.5% monthly uptime | **Relaxed** → NFR-4 | Replaced by a demo-window availability guarantee via `replay`. |
| SOC 2, TLS + strong encryption at rest, enterprise RBAC/secrets management | **Relaxed (retained as posture)** → NFR-6 | No production data or deployment; minimum controls kept for credibility. |
| EU/US/APAC (+GCC/MY/ID) residency | **Deferred** | Synthetic data, single local environment. |
| Immutable tamper-evident audit | **Retained** → NFR-5 / FR-27 | Central to the trust story; cheap to keep. |
| AI explainability (no private CoT) | **Retained** → FR-28 | Non-negotiable for a banking audience. |
| Mobile parity | **Deferred** | Single presenter screen. |
| WCAG 2.1 AA | **Retained** → NFR-7 | Cheap, and leadership may test keyboard use. |
| Correlated telemetry with PII minimisation | **Retained (trimmed)** → NFR-8 | Health panel + correlation ID; PII minimisation trivially satisfied by synthetic data. |
| Backup / restore & DR | **Relaxed** → NFR-9 | Replaced by one-click reset; no production data to lose. |
| Zero provider retention | **Retained as posture** | Trivially satisfied in `replay` (no real LLM egress); in `live`, no client data leaves to a provider. |

---

## 9. Assumptions, open questions and decisions required from Alan

### 9.1 Default assumptions (adopted; confirm or override)

| ID | Assumption | Impact if wrong |
|---|---|---|
| A1 | **No real client data, ever** — 100% synthetic, seeded, labelled. | Any real/PII data changes the entire compliance, consent and residency posture; NFR-6 and §1.1 must be rewritten. |
| A2 | Single presenter-driven session, ~15–20 min, one RM identity ("Sarah"), Singapore/SGT, English, one desktop 16:9 screen, ≤5 observers. | Multi-presenter/mobile/multilingual raises scope and effort. |
| A3 | "MVP" = demonstrable slice, not a production release; no build/deploy beyond the design package. | If a working prototype is expected, Phases 2–4 must become build specs. |
| A4 | Staleness thresholds 30s/120s; loop ≤10s; reset ≤60s; N=10; ≥3 scenarios. `[ASSUMPTION]` numbers. | Re-tune if the feed's real latency differs. |
| A5 | Consent wording is illustrative, not legally approved; no real microphone/ASR. | A real recording changes FR-16/17 and requires legal sign-off. |
| A6 | "Live" = one genuine external feed with real wall-clock `as_of` + attribution; a delayed/sandbox feed is acceptable **only if** explicitly labelled as such (see Q6). | A sceptical executive may reject delayed feeds as "not live". |
| A7 | Primary range moment = family entity graph (FR-24); Shariah beat (FR-25) optional, flag OFF. | If leadership wants the faith-based beat, swap flag and keep depth unchanged. |

### 9.2 Open questions / decisions required from Alan — being explicit and critical

| # | Question | Why it is critical | My default recommendation |
|---|---|---|---|
| **Q1** | **Which live market data source and entitlement?** Licensed vendor sandbox (LSEG/Refinitiv, Bloomberg, Wind), exchange/delayed public feed, or vendor demo stream? Is on-screen attribution legally permitted? | The source name, `as_of` and attribution chip are on stage in front of a client's executives; unlicensed display is a real exposure. Also sets NFR-1/NFR-2. `[PRD: brief §7]` | Primary = vendor sandbox or delayed public feed with explicit attribution + a recorded fallback stream; confirm licensing **before** Phase 3 freezes the feed contract. |
| **Q2** | **What does "postgres plugin" mean?** (a) Postgres **extensions** (TimescaleDB / pgvector / pg_cron / `file_fdw` / `postgres_fdw`), (b) a WorkBuddy/IDE **Postgres connector**, or (c) a **BI/visualisation** plugin? | Determines whether Phase 3 designs schema extensions or an integration/BI layer. I have interpreted (a) as primary `[INFERENCE]`, and expressed it as a requirement (FR-30) rather than a solution. | (a), with the architect choosing a **minimal justified set**; if Alan meant (b)/(c), say so now — it changes Phase 3 materially. |
| **Q3** | **What does "generator of file / database" mean?** A one-off seed script, or a repeatable **operator tool used live on stage** that emits flat files + manifest + loads Postgres across `seed`/`replay`/`live`? | Drives FR-29…32 and the whole reproducibility gate (G4/G5/G6). | Repeatable operator tool with `seed`/`replay`/`live`, flat files (CSV/JSON/Parquet) + manifest/schema contract + Postgres population. Explicitly a **demo data generator, not a production migration tool**. |
| **Q4** | **Is real client data ever used?** Including anonymised production extracts? | Single largest compliance determinant. | **No.** Synthetic only, labelled. If "yes", this spec must be re-opened before Phase 2. |
| **Q5** | **Recording/consent posture for the demo?** Is a real microphone/ASR expected, or is a scripted consent gate + injected transcript acceptable? Who signs the demo consent wording? | A real recording invokes PRD §14.1 (platforms, languages, jurisdiction consent, retention/deletion) — a scope and legal escalation. | Scripted gate + injected transcript, clearly declared on stage; illustrative wording, no legal sign-off needed. |
| **Q6** | **What must "live" demonstrably mean to a sceptical executive?** Minimum bar: (i) real external source name + cross-checkable wall-clock `as_of`, (ii) an event not pre-scripted, or a clearly-labelled replay if scripted, (iii) a permanent mode chip. | This is the headline claim; if the bar is "genuine licensed real-time feed", cost/entitlement work must start now; if "clearly-labelled delayed feed" is acceptable, scope shrinks. | Define the bar explicitly; prefer (i)+(iii) with a genuine feed, and keep `replay` as an honest, announced fallback. |
| **Q7** | **Scope trade-offs to ratify** (see below). | Each is a deliberate cut that leadership may contest. | Ratify or override each. |

### 9.3 Scope trade-offs I made (ratify or override)

1. **Cut Epic 3 entirely.** NL search and full suitability assessment need a certified product universe, entitlements and compliance-owned rules `[PRD: §14.4]`. I retained only the *hard-stop boundary* (FR-20) so the trade-ticket moment cannot mislead. Risk: an executive may ask "can it recommend products?" — answer honestly: not in this MVP.
2. **Thinned meeting capture to a consent gate + scripted transcript.** Real ASR is expensive and legally loaded; the demo proves memory write-back, not transcription accuracy. Risk: "is that real transcription?" — answer: no, declared.
3. **Stubbed every external write/send** to a local sink. Risk: "did the email actually go?" — answer: no, and that is the point (human-approved, never auto-sent).
4. **One range moment, not two depth dives.** Epic 4/5 depth would consume the demo and add SSB/entity-sign-off risk `[PRD: §14.5/§14.6]`. Shariah is P1/flag-OFF and first to cut.
5. **Relaxed all production NFRs** and explicitly refused SOC 2 / 1,000-user / 99.5% / retention-lift claims (§7.3).
6. **No mobile, no real multi-model router, no eval harness, no analytics.** These add cost with zero stage value.
7. **Interpreted "MVP" as depth-thinned full loop, not feature-count reduction**, because the PRD says the loop is the product. `[PRD: §3]`

### 9.4 PRD §14 decisions carried forward as demo assumptions

Transcription platforms/languages/consent → A5/Q5; CRM/email/calendar targets & write ownership → demo sink, no real write ownership; ranking objective weights & meaningful-touchpoint definition → seeded, versioned, FR-33-configurable; product universe / market-data entitlements / suitability rule owner / hard-stop matrix → Q1 + seeded rules; Shariah design partner / methodology → out of MVP (FR-25 static); entity coverage / entitlement matrix → seeded 4–6 nodes (FR-24); retention measurement method → never claimed (§7.3); mobile policy → deferred. `[PRD: §14]`

---

## 10. Four global rules — compliance note

**Simplicity over redundancy:** 34 requirements share five cross-cutting contracts (C-1…C-5) instead of repeating provenance/approval/audit definitions 34 times; one Postgres store, one generator, one Copilot Core, one primary range moment; the Out-of-Scope table is as deliberate as the In-Scope one; no duplicate pipelines or unused components are specified. **Annotation discipline:** explanatory notes appear only at non-obvious decisions (the cut line, the stub/ honesty boundary, the hard-stop nuance, the "generator is requirements not solution" boundary) and state *why*; no line-by-line filler; every non-obvious claim is tagged `[PRD]` / `[INFERENCE]` / `[ASSUMPTION]`. **Contract freeze:** C-1…C-5 plus FR-29's schema/manifest contract are declared frozen logical contracts before any build; FR-29 AC-4 and FR-33 require changes to route through the architect and be synced to Phases 2/4 — the architect freezes the physical data model and interface contracts in Phase 3. **On-disk delivery:** this document is persisted at `deliverables/01_Requirements_Specification.md`; it contains no application code, no runnable scripts and no shipped system, and it stops before any build work.

---

*End of Phase 1 deliverable. Hand-off: full verbatim text to team-lead for Phase 2/3/4 consumption. Requirements IDs `MVP-FR-01…34`, contracts `C-1…5`, exceptions `X-01…20`, gates `G1…G11`, NFR inputs `NFR-1…10`, assumptions `A1…A7`, questions `Q1…Q7` are the stable references downstream phases should cite.*

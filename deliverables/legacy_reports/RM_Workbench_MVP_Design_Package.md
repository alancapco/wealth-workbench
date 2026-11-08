# Next-Generation RM Workbench — MVP Design Package

**For:** Alan Young (Capco, CTO advisor) and client senior leadership
**Date:** 5 November 2026
**Status:** **DESIGN ONLY — no code has been written, no schema executed, no system built.**
**Basis:** `RM_Workbench_PRD.md` v1.1 (and its .docx equivalent), plus the enhancement pack, product strategy package and "The Future RM" video treatment.

> **Addendum (6 Nov 2026) — read this too.** Alan subsequently asked for the *demo data itself*, diagrams at architecture / component / systems level, a very lightweight CRM, a sampled relationship graph, and meeting / booking / email system context — and then specified **HubSpot Free** as the demo CRM and **Retell AI** as an optional voice agent. That work is delivered as a separate **addendum**: start at `15_Enhancement_Executive_Summary.md`. It adds concrete synthetic data (`13_Demo_Seed_Pack.md` + `demo_data/`), eight validated Mermaid diagrams and a 6-table CRM adapter (`12_Demo_Data_and_Systems_Architecture_Enhancement.md`), a data-intake request list (`11_Demo_Data_Requirements_and_Intake.md`), and the ratified vendor ruling `E-9…E-16` (`14_Vendor_Adapter_Ruling_HubSpot_Retell.md`). **This base package is the frozen baseline; nothing in Phase 1–4 is reopened.** The addendum is DESIGN ONLY as well.

---

## 1. What this package is

You asked for **design first**: an MVP carved from the draft PRD, integrating **live market data**, with a planned **file / database generator**, using **Postgres and a Postgres plugin**, and — before any code — an elaborated **functional specification**, **non-functional requirements**, **components** and **dataflow**. This package delivers exactly those four artefacts, at design depth, for a senior-leadership demo.

It is the output of a four-phase delivery process (requirements → product design → technical solution → feature plan), with a gate at each phase. **It stops deliberately before any build work.** Phase 4 is a plan for a *future, separately authorised* build, not an instruction to build now.

### Where each of your four asks is answered

| Your ask | Primary document | Section |
|---|---|---|
| **Functional specification** (elaborated) | `01_Requirements_Specification.md` | §4 — 34 numbered requirements, each with actor/trigger, numbered orchestration flow, input provenance, output + review state, 2–4 testable ACs, exception behaviour |
| **Non-functional requirements** | `03_Technical_Solution.md` | §9 — NFR-1…18 with measurable targets, measurement method, verification gate, and disposition vs PRD §7 |
| **Components** | `03_Technical_Solution.md` | §2 — 18 logical system components, C4-style Mermaid container diagram, L1–L5 copilot mapping, UI/system boundary table |
| **Dataflow** | `03_Technical_Solution.md` | §3 — six numbered Mermaid flows (DF-01…06) plus a dataflow table and an Approve sequence diagram |

Your three additional constraints are covered in dedicated sections: **live market data** (`03` §6), **file/database generator** (`03` §7, UX in `02` §8), **Postgres + plugin** (`03` §4 and §5).

### Document index

| # | File | Words | What it is |
|---|---|---:|---|
| 00 | `00_Shared_Design_Brief.md` | 1.8k | Your verbatim request, PRD digest, demo narrative, assumptions, global rules |
| 01 | `01_Requirements_Specification.md` | 13.7k | MVP scope cut, 34 FRs, 5 logical contracts, 20 exceptions, 11 gates, golden path, NFR inputs, 7 open questions |
| 02 | `02_Product_Design_Specification.md` | 14.5k | IA, 4 Mermaid flows, 14 screens with field-level state-complete specs, 16 shared UI components, generator console UX, copy standard, G1–G11 + 34-FR traceability |
| 03 | `03_Technical_Solution.md` | 24.7k | **Freeze line**: 8 ADRs, 18 components, 6 dataflows, 40 `CREATE TABLE` specs, extension decision, feed contract, generator design, 22 interface contracts, 20 events, 18 NFRs, full traceability |
| 04 | `04_Feature_Unit_Plan.md` | 15.1k | 24 self-contained future-build cards, batch/dependency diagram, parallel schedule, demo run-of-show, executive Q&A, risk register |

---

## 2. The leadership story

**Single headline claim the MVP proves on stage:**

> A genuine, unscripted live market event enters the workbench and, within seconds, propagates through the entire advisory loop — re-ranked priorities, a refreshed sourced brief, a grounded outreach draft — with **every AI statement carrying a source/timestamp chip** and **every outbound action stopping at a human Approve**.

This is an extension of the PRD's own claim that *"this loop is the product"* (`PRD §3`), with live market data as the trigger. The locked tagline from the video treatment is preserved: **"AI orchestrates the workflow. You orchestrate the relationship. / Human-approved. Always."**

### The 20-minute run-of-show (scenario S1 "Wong Drift")

| T | What the room sees | Human gate |
|---|---|---|
| +00:00 | Real tick: `MARKET EVENT · <instrument> · <source> · as-of 09:58:14 SGT` | — |
| +00:02 | `Wong portfolio drifted 6% from target · Risk/Opportunity · rule-pack v1` with source chip | — |
| +00:04 | Copilot Core opens a workflow; stage trace shows **one** `correlation_id`; D5 context reused | — |
| +00:06 | My Day re-ranks Wong 4→1 with a rank-change explanation; no padded leads | — |
| +00:08 | Five-section brief, every material fact chipped, agenda items tagged `PROPOSED` | RM edits one line, **approves brief** |
| +00:10 | Consent banner → recording indicator → `Family: daughter added · preference noted` memory chip | **Consent is the first human gate** |
| +00:14 | **ONE** review surface: notes, CRM old→new, email draft, rebalancing proposal, ticket with `execution disabled`, tomorrow's re-ranked priorities | — |
| +00:16 | RM edits two lines, taps **Approve** → CRM `succeeded`, email stays `draft · DEMO SINK — not delivered`, zero sends, zero trades | **The single decisive approval** |
| +00:18 | **Loop closes** — the approved preference appears in the new priority list *and* tomorrow's brief, all linked by one `correlation_id` | — |
| +00:20 | Optional 30s range beat: Tan family entity graph → two per-attendee entitled pack versions | Packs approved before presentation |
| End | Tagline card; honesty chrome persists to the last frame | — |

Two fallback drills are rehearsed: **F1** feed outage (amber `STALE`, market section `unavailable`, no invented tick, announced `REPLAY — recorded 09:58`) and **F2** consent declined (`MANUAL NOTES`, low-confidence facts requiring explicit review). Both are designed as *stronger* trust proofs than the happy path.

### What is real, simulated, stubbed — and why that is honest

| Posture | Elements |
|---|---|
| **REAL** | The live market feed in `live` mode (real wall-clock `as_of`, real attribution); Postgres store; the file/database generator; provenance chips; audit writes; approval gates; the re-rank; the mode switch. |
| **SIMULATED** | 100% synthetic client / portfolio / household / CRM / product / suitability data, deterministic from one seed; the recorded `replay` tick stream. Permanent `SYNTHETIC DEMO DATA` label. |
| **STUBBED** | ASR (scripted transcript — no microphone); LLM / multi-model router (deterministic outputs with fixed version stamps); CRM / email / SMS (local demo sink, zero egress); SSO / calendar / core banking. |
| **HARD-BLOCKED** | Trade execution — **no table, no endpoint, no code path exists**. |

The demo never claims vendor integrations, ASR accuracy, model quality, regulatory certification or production scale. Every non-real element is visibly labelled, so a sceptical executive asking "is that real?" gets a precise, non-defensive answer. Ten such awkward questions, with sourced answers, are pre-scripted in `04` §5(e).

### Explicitly **NOT** claimed

SOC 2 / attestation · 1,000 concurrent users · 99.5% uptime · data residency / cross-border compliance · real vendor integrations · real ASR or model-quality metrics · retention lift, adoption or "4–6 hours saved" · backup/DR objectives · mobile parity · autonomous advice, client sends or trade execution. Claiming any of these on stage would be dishonest (`01` §7.3, `03` §9.2).

---

## 3. MVP scope decision

The PRD is a 12-month V1 with 22 FRs, 5 epics and a 26–64 FTE envelope. Cutting the MVP by **feature count** ("briefs only") would fail, because the PRD states the loop is the product. The MVP is therefore cut by **depth, not breadth**: the whole loop end-to-end, each stage thinned to the minimum needed to be provable.

| IN (depth-thinned) | OUT (deferred, not abandoned) |
|---|---|
| Live tick ingest, normalisation, signal detection, live↔replay switch | Epic 3 NL product search & full Red/Yellow/Green suitability assessment |
| D5 client memory + household/entity graph with node-level entitlements | Epic 4 depth (screening engine, zakat, purification, SSB packs) |
| Copilot Core orchestration, workflow state, stage-level kill switch | Epic 5 depth (multi-custodian consolidation, succession, capital calls) |
| My Day Top 10 with Risk/Opportunity/Retention reason codes | Real integrations, real ASR, real sends, mobile parity |
| Five-section sourced brief; consent gate; scripted capture | Full eval harness, multi-model routing, production NFRs |
| **One** unified post-meeting review with a single Approve | |
| Grounded outreach draft + approved send to demo sink | |
| Family entity graph with per-attendee entitled pack versions (P0 range moment) | |
| Provenance chips, append-only audit, version stamps, explainability | |
| **NEW (from your brief):** live market data, file/database generator, Postgres, demo operations | |

One deliberate nuance: **Epic 3's suitability logic is out as a feature, but its hard-stop boundary is retained** — "missing/expired suitability → blocks ticket handoff". A demo that lets a pre-filled trade ticket through without a suitability gate would actively mislead a banking audience. Shariah preference propagation (FR-25) is P1 and flag-OFF by default — the first thing to cut if the window tightens.

**Cut-line rationale** is a demo-adapted value/effort table in `01` §2.2; the seven scope trade-offs are listed critically in `01` §9.3.

---

## 4. Functional specification — what was elaborated

`01` §4 is the centrepiece: **34 numbered MVP-FRs** across 12 capability areas, each with actor/trigger/preconditions, a numbered orchestration flow, input data with provenance, output artefact + review state, 2–4 testable acceptance criteria, and exception behaviour. Five cross-cutting logical contracts (C-1…C-5) are stated once and referenced by every FR rather than repeated 34 times.

| Area | FRs | Capability |
|---|---|---|
| A | 01–04 | Live market data ingest & signal detection, live↔replay mode |
| B | 05–07 | Client Memory & Relationship Graph, node entitlements, RM correction |
| C | 08–10 | Copilot Core orchestration, workflow state, kill switch, no open chatbot |
| D | 11–13 | My Day Top 10, reason codes, evidence drill-down, RM controls |
| E | 14–15 | Five-section sourced brief, partial data, regeneration/versioning |
| F | 16–17 | Consent gate, scripted capture, extraction, memory write-back |
| G | 18–21 | Unified review, idempotent CRM, email draft, ticket handoff, **loop closure** |
| H | 22–23 | Grounded outreach draft, policy checks, approved send |
| I | 24–25 | Range moment: family graph + entitled packs; optional Shariah beat |
| J | 26–28 | Evidence chip on every statement, immutable audit, explainability |
| K | 29–32 | **Demo data fabric / file–database generator** (as requirements, not solution) |
| L | 33–34 | Admin without redeploy, mode switch, health panel, scenario library |

**FR-21 is the headline requirement**: approved outcomes trigger a re-rank, and the next brief carries the newly approved preference. The loop closes on **approved facts only** — unapproved or low-confidence facts never propagate.

Supporting artefacts: 20 exception cases (X-01…20), 11 binary pass/fail gates (G1…G11), 10 demo success criteria (D1…D10), and four named scenarios (S1 Wong Drift, S2 Rahman Review, S3 Tan Family Pack, S4 Feed Outage).

---

## 5. Non-functional requirements — the measurable spec

`03` §9 is the architect-owned final spec: **NFR-1…18**, each with a measurable requirement, target, measurement method, verification gate, priority, and an explicit disposition against PRD §7 (retained / re-targeted / relaxed / new, with justification). Highlights:

| ID | Target | Disposition vs PRD §7 |
|---|---|---|
| NFR-1 | Live tick → visible re-rank **≤10s p95**; ingest-to-store ≤2s p95 | Retained / re-targeted from "brief <10s" into the honest loop measurement |
| NFR-2 | `warn` at 30s feed age, `stale/outage` at 120s; 100% of affected facts labelled | Re-targeted to concrete demo thresholds |
| NFR-3 | Same seed + schema + mode → identical manifest checksum and artefact sequence | **New** — demo-specific determinism |
| NFR-4 | 100% over the ~20-min window; golden path completes **offline in replay** with 0 external calls | Relaxed from 99.5% monthly uptime |
| NFR-5 | 100% of approvals, mode switches, config changes, blocked attempts, artefacts **and reads** audited; verifiable SHA-256 hash chain | Retained |
| NFR-6 | 0 real PII; server-side entitlements; 0 egress from demo sink; TLS 1.2+ on the live feed hop | Relaxed, retained as posture |
| NFR-9 | One-click reset with audit archived, **≤60s** | Relaxed from backup/DR |
| NFR-10 | 1 presenter + ≤5 observers | Relaxed from 1,000 concurrent users |
| NFR-13 | **0 cross-node facts in any artefact**, including drafts/hidden `jsonb`; entitlements in context assembly *and* RLS | Retained — hard gate G7 |
| NFR-17 | 0 orphan FKs; 0 facts without provenance; flat-file ↔ Postgres row counts + key checksums agree | **New** — generator-specific |
| NFR-18 | Duplicate tick / event / retried approval → exactly one effect | Retained |

A nine-procedure **NFR verification plan** (`03` §9.3) specifies how each would be tested at demo acceptance — without writing tests now.

---

## 6. Components

`03` §2 defines **18 logical system components** (the minimum viable count), with six justified mergings. These are **not** the 16 UI components from `02` §7 — the boundary is drawn explicitly so nothing is implemented twice.

| Group | Components |
|---|---|
| Ingest | SVC-01 Feed Adapter · SVC-02 Normaliser + Staleness · SVC-03 Signal Detector |
| Core state | SVC-04 Outbox / Event Bus · SVC-05 Postgres · SVC-06 D5 Memory & Graph |
| Orchestration | SVC-07 Copilot Core · SVC-08 Skill Runtime (12 typed skills, one dispatcher) |
| Trust | SVC-09 Policy & Approval Gate · SVC-10 Provenance / Evidence · SVC-11 Audit · SVC-14 Demo Sink · SVC-15 Health / Telemetry |
| Data & ops | SVC-12 **Generator / Demo Data Fabric** · SVC-13 Mode / Scenario / Config / Flags / Kill Switch |
| Edges | SVC-16 Presenter BFF (**READ-ONLY**) · SVC-17 Operator BFF (**SOLE WRITER**) · SVC-18 UI Shell |

The five-layer copilot architecture maps cleanly: L1→SVC-18/16, L2→SVC-07+04, L3→SVC-06, L4→SVC-08, L5→SVC-09/10/11/13/14/15.

**Three structural decisions worth flagging to a CTO audience:**
1. **Two BFFs, deliberately not merged** — the read/write split makes gate G8 (never show `LIVE` while bound to replay) a *structural* property, not operator discipline. The operator console has **no Approve control**; the presenter frame has **no mode control**.
2. **Transactional outbox in Postgres, no broker** — atomic row+event writes, built-in dedup, one fewer moving part on a demo laptop.
3. **Single Postgres instance holds ALL state** — one transaction boundary, one reset target.

---

## 7. Dataflow

`03` §3 contains **six numbered Mermaid diagrams** plus a dataflow table with latency budgets, failure behaviour, X-IDs and FR-IDs:

- **DF-01** Live tick → normalise → store → signal → orchestrator → D5 context → rank → brief → UI chip, with a step-by-step timing budget summing to **10.0s p95** (ingest-to-store 1.6s).
- **DF-02** Closed loop: unified review → single Approve → C-3 token → idempotent CRM sink write → email stays `draft` → memory write-back → re-rank → next brief. **No auto-send / auto-trade path exists.**
- **DF-03** Generator pipeline: seed → deterministic world → flat files + manifest → staging → one-transaction Postgres load → integrity/provenance validation → checksum → `READY` or **fail-loud X-20** → reset/archive.
- **DF-04** Live↔replay binding and F1 outage fallback, including the sole-writer/read-only mode state projection.
- **DF-05** Provenance & audit fan-out (C-1 on every fact, C-4 append-only, version stamps, read-access events).
- **DF-06** / sequence diagram for the single Approve tap.

`02` §3 adds four product-level Mermaid flows (golden path with human gates, mode switch, consent, generator/reset).

---

## 8. Postgres and the "plugin" decision

### Data model (`03` §4)

**PostgreSQL 16, one instance, 8 schemas** (`demo_meta`, `market`, `client`, `graph`, `workflow`, `artefact`, `audit`, `staging`), **40 `CREATE TABLE` specifications** with an ER diagram. Every fact table carries the **7-column C-1 provenance envelope** (`source_id`, `source_kind`, `as_of`, `ingested_at`, `confidence`, `mode`, `version_stamp`) as explicit columns — deliberately not a composite type, because a NULL composite would hide partial envelopes and break integrity gate G6.

Also specified: `timestamptz` / `uuid` keys, explicit and deferrable FKs, unique idempotency keys, RLS for book + node entitlements (with a critical note that **RLS alone is insufficient** — FR-06/G7 require filtering in context assembly *before* any skill sees the context), append-only audit enforced by revoked privileges plus a SHA-256 hash chain, immutable approval tokens, version registry, and a demo-scale volume estimate (~10⁴ rows, tens of MB).

### The extension / "plugin" decision (`03` §5)

Nine candidates evaluated. **ADOPT = exactly two:**

| Extension | Role | Purpose (tied to a gate) |
|---|---|---|
| **TimescaleDB** | **PRIMARY** | `market.market_tick` hypertable + `tick_1m` continuous aggregate. The live tick stream is genuinely time-series; this makes the FR-03 drift query and NFR-2 staleness computation fit the ≤10s loop (G3 / NFR-1). |
| **`file_fdw`** | SUPPORTING | Foreign tables over the generator's CSV twins let **flat-file ↔ Postgres agreement be proven *inside Postgres*** via SQL `EXCEPT` — the most literal answer to "generator of file / database" (G5). |

**DEFER:** pgvector — grounding here is exact-key `context_refs`, not similarity search; an embedding model would break determinism (NFR-3) and offline replay (NFR-4). **REJECT** with one-line reasons: pg_cron (duplicate scheduler — TimescaleDB policies already cover it), postgres_fdw (no second server), pgaudit (wrong granularity), pgcrypto (PG16 core suffices), ltree (4–6 node graph, recursive CTE suffices), pg_stat_statements (unused diagnostic). **Nothing is adopted "for completeness".**

**Three readings of "Postgres plugin" are documented explicitly**, because the phrase is ambiguous:
- **(a) Postgres extensions** — adopted as primary; this is what the DDL and G5 verification use.
- **(b) A WorkBuddy / IDE Postgres connector** — design-time tooling; changes no frozen contract; recommended as complementary, not primary.
- **(c) A BI / visualisation plugin** — would add a second rendering stack and a second auth path, weakening G8 and the single-frame IA; **rejected for the MVP**.

If you meant (b) or (c), say so — it changes §5, the freeze statement and the console's "extension in use" display field, but **not** the DDL or the 22 interface contracts.

**Honest limitation:** `file_fdw` reads TEXT/CSV only. A CSV twin is therefore authoritative for FDW verification; the design does **not** claim Parquet or JSON are read by a Postgres plugin.

---

## 9. Live market data

`03` §6 designs a **pluggable feed adapter** (SVC-01) behind one normalised `feed.contract/v1` — WebSocket streaming primary, REST polling fallback, vendor SDK internal — with entitlement/licence checks before append, canonical symbol mapping, ±2s clock-skew gate (X-04), staleness computed on read (30s/120s), token-bucket backoff (X-06), `tick_key` dedup, heartbeat-gap outage detection (X-01), and TLS 1.2+ on the only external hop. **No client data leaves to the feed.**

**No vendor was invented as decided.** Three option categories were evaluated on entitlement, on-screen attribution permission, latency, cost and demo risk for a HK/Singapore banking audience:

| Option | Role | Condition |
|---|---|---|
| **A** — licensed vendor sandbox / demo-entitled real-time feed | **Recommended primary** | Only with **written on-screen display clearance** |
| **B** — exchange / delayed public feed | Fallback 2 | Must be explicitly labelled "delayed"; you must ratify the "live" bar (OD-5) |
| **C** — vendor demo / recorded stream | Fallback 1 = mandatory `replay` | Guaranteed continuity; carries `REPLAY — recorded <time>` |

`source_id`, `source_attribution` and `licence_tag` are **versioned config values**; the UI keeps a `<source>` placeholder until cleared. Recorded streams preserve the original `feed_as_of` and set `source_kind=replay`.

**The three-bar "live" test** (OD-5) defines the headline claim: (i) a real external `source_id` + cross-checkable wall-clock `as_of`, (ii) an event that is not pre-scripted — or an explicitly labelled replay if it is, (iii) a permanent audience-visible `ModeChip`. A DB `CHECK` constraint makes it impossible to show `LIVE` while bound to `replay_stream` (G8).

---

## 10. The file / database generator

`03` §7 (implementation design) and `02` §8 (operator UX) answer your "generator of file / database" requirement. It is designed as a **repeatable operator tool**, not a one-off script, and explicitly declared a **demo data generator, NOT a production data migration tool**.

| Stage | Design |
|---|---|
| **Input** | One seed + frozen `schema_contract.json v1.3` + scenario S1…S4 + mode (`seed` / `replay` / `live`) |
| **Determinism** | `splitmix64(seed_hash, domain)` namespaced sub-seeds → order-independent row derivation; child keys derived from parent keys → **FK-clean by construction**, so "invent a parent record" is never needed; deterministic `as_of` offsets; `ingested_at` excluded from checksums (else G4 fails) |
| **Flat files** | `<NN>_<schema>_<table>.<ext>` in CSV / JSON / Parquet, plus `manifest.json`, `schema_contract.json`, `checksums.sha256`, `replay_stream.parquet`; a CSV twin for every relational table |
| **Postgres load** | **ONE transaction**, `SET CONSTRAINTS ALL DEFERRED`, staging → `COPY` / FDW → validated core tables in FK order; ROLLBACK on any failure — no half-loaded world presented as `READY` |
| **Manifest v1.3** | Declared file/table list, row counts, field-level provenance rules, `extension_set` with purposes, `dataset_checksum`, verdict, `offending_record` |
| **Validation** | 0 orphan FKs, 0 provenance gaps, `as_of` on every fact, bidirectional `EXCEPT` cross-view row-count + key-checksum agreement, regenerate-to-scratch reproducibility |
| **Fail loud (X-20)** | `SCHEMA MISMATCH · <offending record> · demo start BLOCKED · no auto-repair` |
| **No-real-data guard** | Local `demo_*` DSN allow-list, `synthetic_marker`, manifest file allow-list, no code path to a production source |
| **Reset** | Archive audit by `run_id` (never delete) → TRUNCATE mutable tables only → reload frozen baseline → re-verify checksum + integrity → `READY` in **≤60s**. Truncate-and-reload recommended over `pg_dump`/templates (reuses one load path, re-verifies, keeps the archive) |

The **Demo Operator Console** (SCR-11, off-camera) exposes all of this: seed input, frozen schema/manifest version read-only, mode control, `generate → validate → load` progress with per-table counters, flat-file listing with row counts, Postgres load status, extension-in-use display, integrity report (SCR-13), scenario library, config versions, feature flags, kill switch, one-click reset with archive confirmation, and a permanent **what-is-real legend**. The on-camera frame shows only the read-only `ModeChip`, health bar and switch announcements.

---

## 11. Design governance and coverage

**Four global rules applied throughout:** (1) simplicity over redundancy — no duplicate implementations or over-abstraction; (2) annotations only at non-obvious WHY points (SQL comments in Chinese); (3) **contract freeze** — the DDL, `IF-01…22`, `EV-01…20`, `manifest v1.3`, `feed.contract/v1`, the extension set and `NFR-1…18` are frozen; changes route through the architect and sync to all affected phases; (4) everything delivered lands on disk.

**Coverage is complete and honestly stated:** 34/34 MVP-FRs, 11/11 gates, 18/18 components, 14/14 screens, 22/22 interface contracts. Four FRs are **intentionally partial by frozen scope, not gaps**: FR-16/17 (ASR is a declared stub), FR-20 (execution path deliberately absent — that *is* the requirement), FR-24 (optional 30s beat), FR-25 (P1, flag OFF).

**Phase 4** (`04`) turns this into 24 self-contained future-build cards: Batch 0 foundation (8 cards) → five parallel tracks A–E (13 cards) → integration → acceptance. Cards are independently assignable to a developer who has read nothing but that card plus the frozen IDs it cites. It also contains the pre-flight checklist, run-of-show, G1–G11 observations, ten awkward executive Q&As, a 12-item risk/rollback register, and an explicit **first-to-cut** list.

---

## 12. Decisions required from you

Three ambiguities in your brief were **not silently guessed** — they are surfaced with options and recommendations:

| # | Decision | Recommendation | What it blocks |
|---|---|---|---|
| **Q1 / OD-1** | **Which live market data source and entitlement?** | Licensed vendor sandbox (Option A) **only with written display clearance**; `replay` as guaranteed fallback; delayed public feed as explicitly-labelled second fallback | A genuine-`live` stage rehearsal and the demo date — **not** the feed adapter's contract, which can be built with `<source>` placeholder |
| **Q2 / OD-2** | **What does "Postgres plugin" mean?** | (a) Postgres extensions — TimescaleDB + `file_fdw`, with pgvector deferred | §5 and the console display field if you meant (b) IDE connector or (c) BI plugin — **not** the DDL or interface contracts |
| **Q3** | **What does "generator of file / database" mean?** | A repeatable operator tool: flat files + manifest + Postgres load, `seed`/`replay`/`live`, deterministic from one seed, one-click reset | Nothing — this is the designed interpretation |

Eight further decisions (`OD-3…11`) are listed in `03` §14.1 and go/no-go mapped in `04` §5(f). The most consequential:

- **OD-5 / Q6 — what must "live" demonstrably mean?** The three-bar test is recommended; a sceptical executive may reject a delayed feed.
- **OD-6 — dual-output hardware.** The off-camera operator console + on-camera mode chip cannot both hold on one physical output. Dual-output is the design baseline; a presenter-safe hotkey overlay is the degraded single-output fallback.
- **OD-3 / Q4 — no real client data, ever** (already resolved "No" by assumption). A "yes" reopens the entire compliance posture.
- **OD-4 / Q5 — scripted consent gate vs real microphone/ASR.** Real recording invokes PRD §14.1 legal work.
- **OD-7 / OD-8 — the `<source>` placeholder and whether any licensed vendor name may appear on stage.**

**One assumption to watch:** `AS-1` — there are three distinct "mode" concepts (audience `demo_mode`, generator mode, and the per-fact C-1 `mode`). The architect flagged this as the single most likely design-changing misinterpretation; it is resolved explicitly in `03` §4.1.

---

## 13. Next steps

1. **Review this package and ratify or override** the scope cuts (`01` §9.3) and the open decisions above — Q1, Q2 and Q3 first.
2. **Start the feed entitlement/attribution conversation now** — it has the longest lead time and is the only item that can collapse the headline claim. `replay` is a fully designed, honest fallback.
3. **Confirm the demo environment**: dual-output hardware, and Postgres 16 with TimescaleDB + `file_fdw` available on the actual host (`04` pre-flight P2/P4).
4. **Only then** consider authorising a build. Phase 4's cards are ready, but executing any of them requires a new decision — **no code exists today**.

---

*Design package assembled by Qi Huolin (Delivery Director), software-dev-team. All five source documents are in `deliverables/`. Design only — no application code, no executed DDL, no scaffold, no build commands.*

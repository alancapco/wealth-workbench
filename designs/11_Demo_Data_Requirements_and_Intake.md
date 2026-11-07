# Demo Data Requirements & Data Intake Specification — RM Workbench MVP (Leadership Journey Demo)

**Phase A deliverable (addendum) · Author:** Xu Qingchu (许清楚), Requirements Analyst, software-dev-team
**Consumer (verbatim hand-off):** Qi Huolin (team lead) → solution-architect (Phase B). Self-contained; the architect consumes this text in full.
**Status:** DESIGN ONLY — no application code, no runnable scripts, no scaffold, no executed DDL. Sample CSV/JSON rows are the *specified output shape* of the generator (H2) and are **Phase B's seed pack**; Phase A contains none.
**Language:** English.
**Evidence base read in full:** `10_Data_Enhancement_Brief.md` (Alan's verbatim request, gap analysis, H1–H6, ratified decisions E-1…E-8), `RM_Workbench_MVP_Design_Package.md`, `01_Requirements_Specification.md` (MVP-FR-01…34, C-1…5, X-01…20, G1…G11, D1…D10, A1…A7, Q1…Q7, S1…S4, F1/F2, §1.1, §5.1), `04_Feature_Unit_Plan.md` §5 / §8 / §9, `03_Technical_Solution.md` §4.1 / §7 / §12 / §14 (OD-1…11). Frozen IDs are referenced, never re-derived.

| Tag | Meaning |
|---|---|
| `[PRD]` | Verifiable in the frozen package. |
| `[INFERENCE]` | My reasoned derivation; challengeable, not a fact. |
| `[ASSUMPTION]` | Default adopted because not specified; needs Alan's confirmation (§9). All proposed volumes/defaults below are `[ASSUMPTION]` and demo-scale (E-6). |

**Boundary.** This addendum adds *concrete demo-data requirements and the surrounding-system / data-intake view only*. It does **not** reopen Phase 2 product design (E-1), introduce screens or components, or alter frozen artefacts (E-7: 8 schemas / 40 tables, IF-01…22, EV-01…20, `manifest v1.3`, `schema v1.3`, extension set {TimescaleDB, `file_fdw`}, NFR-1…18). Any additive schema change is architect-authored and synced to Phase 4; `manifest v1.3` is **not** silently bumped. Requirements below govern **data**, not components or screens.

---

## 1. Why data is the MVP for a leadership demo

The room is being shown a **journey they must believe**, not a feature list. A leadership demo fails when all it can display is an architecture diagram plus a claim ("live event → loop → sourced facts → human approval"): an abstract diagram carries no belief because nothing in it is at stake. What makes the closed loop *visible* is a named client, a holding that genuinely drifts 6%, a tick with a wall-clock `as_of`, a brief whose every line resolves to a source, a memory chip that appears only after consent and reappears in tomorrow's priorities. `[INFERENCE]` Data is the only thing on stage an executive can actually probe: click a chip, ask "who approved that", kill the feed and check that no number was invented. Without credible rows, the honesty posture (`01` §1.1) is a slogan; with them, it is verifiable. The gap analysis (`10` §2) is correct that the frozen design specifies the generator as a *mechanism* but never makes the *data* visible; this document closes that at requirements level.

Two distinctions must stay explicit. **(a) Data as demo content vs data as production asset.** `[PRD]` These rows exist to be read on a projector for ~20 minutes and reset in ≤60s (NFR-9/G10). They are 100% synthetic, deterministic from one seed, carry the 7-column C-1 envelope and a permanent `SYNTHETIC DEMO DATA` label; they are not a customer master, not a migration, not licensed data for redistribution. The generator is explicitly *not a production migration tool* (`03` §7.10). Judging them by production completeness (full KYC, a 500-product universe, real ASR) is a category error that would sink the demo. **(b) Believability is a requirement, not decoration.** `[INFERENCE]` A few dozen well-formed clients beat a million rows: leaders must recognise a plausible HNWI/mass-affluent book, SGD/HKD/USD denominations, prior-close `as_of` and a real-looking five-section brief. The hard test is **traceability at every beat** (G1): a statement with no provenance is suppressed as `insufficient evidence`, never rendered bare (FR-26). Data must be credible, legible and chip-traceable at every beat (H5) — nothing more.

---

## 2. Demo data requirements by journey beat

Row counts = rows **on screen**, not table totals. Entities use frozen table IDs (`03` §4.1); `crm.*` is Phase B additive (E-4/E-7). Timing/beats from `01` §5.1 and `04` §5(b). Volumes `[ASSUMPTION]`.

| Beat | Data entities that must exist | Rows on screen | Provenance / `as_of` | Source chip text that renders | FR / Gate / NFR |
|---|---|---|---|---|---|
| **−00:30** pre-flight | `demo_meta.scenario` (S1–S4 = 4), `generator_manifest` (1), `integrity_report` (1), `demo_run` (1), `demo_mode_state` (LIVE), `config_version` + `version_registry` (~10), `health_snapshot_mv` | 1 scenario name + 8 health fields + manifest line | `seeded`, `mode=seed`, `version_stamp='schema v1.3'`, `world_as_of` anchor; `dataset_checksum` | `READY · LIVE · integrity verified · SYNTHETIC DEMO DATA · manifest v1.3 · checksum 9f3a…` | FR-29/30/31/34 · G4/G5/G6/G8 |
| **+00:00** real tick | `market.instrument` (~30–60 canonical), `market.market_tick` (1 arriving tick + baseline stream) | 1 tick chip, held ≥2.5s | `live_feed`, real wall-clock `as_of 09:58:14 SGT`, `source_id=<source>`, `mode=live`, `licence_tag` | `MARKET EVENT · <instrument> · <source> · as-of 09:58:14 SGT` + `LIVE` | FR-01/02 · G3/G8 · D1 |
| **+00:02** signal | `market.market_signal` (1), `client.holding` (Wong ~8–15), `client.allocation_target` (~5), `demo_meta.config_version` (rule-pack v1, 6% threshold), `market_tick.tick_key` | 1 signal line + rule-pack version | `derived`, triggering tick `as_of 09:58:14`, rule-pack v1, exactly one `signal.raised` | `Wong portfolio drifted 6% from target · Risk/Opportunity · tick as-of 09:58:14 · rule-pack v1` | FR-03/26 · G1/G3 · D1 |
| **+00:04** workflow | `workflow.workflow_instance` (1), `workflow.workflow_stage` (3–5), `graph.memory_fact` (Wong context ~10–20), `context_refs` | 1 stage trace, one `correlation_id` | `seeded` memory (`as_of` prior close) + `derived` workflow state | `context reused from D5 · fact <id> · as-of prior close` | FR-05/08/09 |
| **+00:06** My Day re-rank | `artefact.artefact` (priority_list v1→v2), `client.client` (book ~42; ≤10 rendered), `market.market_signal` (1), `consent_state`/DNC flags, ranking-policy version | 10 rows + 2 retention-risk + rank-change explanation | `derived`, live signal `as_of`, prior list version; no padded leads (X-13) | `Opportunity — rebalancing · as-of 09:58:14 · ↑3 (from 4)` | FR-11/12/13 · X-13 |
| **+00:08** five-section brief | `artefact.artefact/artefact_version` (meeting_brief v1), `client.account`, `client.holding`, `client.interaction` (~3–6), `market.news_item` (~2–4 entitled), `graph.memory_fact`, `market.market_signal` | 5 sections, ~20–30 chipped facts, ~3 `PROPOSED` agenda items | portfolio `seeded · as-of prior close`; drift `live_feed · tick as_of`; news licensed `as_of`; preferences `verified` | `Portfolio, as of prior close` / `Client preference, verified` / `Market · <source> · as-of …` | FR-14/15/26 · G1 · Gate 1 |
| **+00:10** consent + capture | `client.consent_state` (1 accept), seeded scripted transcript (~10–20 utterances), `artefact.extraction_item` (~4–8), `graph.memory_fact` (new fact) | consent banner + `● RECORDING (scripted)` + 1 memory chip | consent `rm_manual` (method+timestamp); transcript `seeded` with offsets; new fact `confidence 0.94` | `Family: daughter added · preference noted · transcript 00:03:12 · confidence 0.94` + `STUB · declared` | FR-16/17 · X-15 · Gate 2 |
| **+00:14** one review | `artefact.artefact` (post_meeting_review), `client.crm_record` (old values ~5–8), `artefact.demo_sink_message` (email draft), `client.product`, `client.suitability_state`, `extraction_item`, next `priority_list` | ~6–10 items on ONE surface | old CRM `seeded · as_of`; suitability `as_of`; every item evidence-linked | `ticket · suitability current · execution disabled` / `CRM old → new` | FR-18/19/20 · G2 |
| **+00:16** single Approve | `artefact.approval_token` (1, C-3), `client.crm_record` (new values), `artefact.demo_sink_message` (state `draft`), `audit.audit_event` (several) | 1 approval line + CRM `succeeded` + email `draft` | `rm_manual` C-3 token (`approver_role`, `approver_id`, `approved_at`, `final_content_hash`); C-4 | `Approved by Sarah (RM) · 10:14:32 · CRM succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades` | FR-18/19/23/27 · G2 · D3 · NFR-18 |
| **+00:18** loop closes | `artefact.artefact` (priority_list v3 + tomorrow's brief v2), `graph.memory_fact` (approved preference now canonical), `workflow.workflow_instance` (new), one `correlation_id` | changed-rank explanation + brief carrying "daughter to join" | `rm_manual` + transcript evidence; `derived` re-rank; all linked by one `correlation_id` | `Client preference, verified · approved 10:14:32` | FR-21/07/27 · D4 |
| **+00:20** range beat | `graph.graph_node` (6–7), `graph.graph_edge` (~6–10), `entitlement_rule`/`entitlement_decision`, source-doc refs, `artefact.artefact` (family_pack ×2), `client.client.shariah_sensitive` (flag-OFF pointer) | 6–7 nodes + 2 entitled pack views | `seeded` graph + source-doc refs `as_of`; matrix version + `as_of` on each pack | `Trust deed, reviewed by Sarah · pack v_n · matrix v1 · as-of …` | FR-24 (FR-25 off) · G7 · D8 · Gate 4 |
| **End** card | honesty chrome only (no new facts) | tagline + persistent labels | n/a | `SYNTHETIC DEMO DATA · DEMO SINK — not delivered · ModeChip` | FR-34 · D10 · G11 |
| **F1** feed outage (+00:03) | `demo_meta.feed_status` (stale/outage), `market.market_tick` (last tick 09:58:14, age 47s — **no new tick**), `replay_stream.parquet` + CSV twin, `artefact.artefact.section_status` (market `unavailable`) | amber `STALE` chips on affected facts; market section `unavailable` | stale labelled, never substituted; `source_kind=replay`, `mode=replay`, original `feed_as_of` preserved | `FEED STALE · last tick 09:58:14 · age 47s` → `REPLAY — recorded 09:58` | FR-02/04/15/34 · X-01/02/03 · G8/G9 · D9 · NFR-2 |
| **F2** consent declined (+00:10) | `client.consent_state` (declined/withdrawn, method+timestamp); **no** transcript, **no** extraction evidence; `rm_manual` notes (~3–5) | `MANUAL NOTES`; every derived fact `low-confidence` + review flag | `rm_manual` only; zero `seeded` transcript facts | `rm_manual · low-confidence · review required` / `STUB · declared` | FR-16/17/21 · X-05/15 · G9 |

**Bridge to the seed pack.** `[INFERENCE]` Each row above is a *minimum pre-condition* for its beat: Phase B must be able to generate it from one seed, in `seed`/`replay`/`live`, with C-1 on every fact. A beat whose entities are absent cannot be rehearsed, so §3 turns each into a numbered, testable requirement.

---

## 3. Elaborated demo-data requirements (DDR-01…DDR-26)

Each DDR: short name · governed dataset · what must be generated · 2–4 testable ACs · FR/Gate/NFR served. Requirements are about **data**, not components/screens. All generated rows are 100% synthetic with C-1 on every fact.

### 3.1 Client & book

**DDR-01 · Synthetic client master** — `client.client`, `client.rm_book`. Generate a believable mix of HNWI and mass-affluent clients (~30–50), each with synthetic name, segment/tier, jurisdiction, base currency (SGD primary; HKD/USD minority), plausible AUM, DNC/marketing-consent flag, and an entitled RM book mapping. Enough history to make a brief look real. **AC:** (1) 0 real PII — names/emails/IDs match no real-world identifier pattern (A1/NFR-6); (2) ≥2 wealth tiers and ≥3 currencies present; (3) every row has all 7 C-1 columns non-null with `as_of` at prior close; (4) every `client` FK-resolves to an `rm_book` row (G6). **Serves:** FR-05/11/29, A1, NFR-6.

**DDR-02 · Accounts, holdings, allocation targets & AUM** — `client.account`, `client.holding`, `client.allocation_target`. Generate ~200–400 holdings across accounts; target weights summing to 1.0 per account; Wong holds an instrument whose price move can breach the 6% drift threshold (S1). **AC:** (1) target weights per account sum to 1.0 ±0.001; (2) every holding FK-resolves to an account **and** an instrument; (3) Wong has ≥8 holdings with a distinct prior-close `as_of`; (4) drift is computable from holding value vs target for the +00:02 signal. **Serves:** FR-03/14/31, G6, S1, NFR-17.

**DDR-03 · Consent & suitability state** — `client.consent_state`, `client.suitability_state`. Generate per-client/per-session consent states (accept / decline / withdraw, method + timestamp) and suitability states (current / expired / missing, `as_of`), covering Wong's S1 accept and an F2 declined/withdrawn variant. **AC:** (1) both an accepted and a declined/withdrawn state exist for Wong; (2) suitability `as_of` is present and can gate FR-20; (3) consent is never derived from calendar acceptance (FR-16 AC-4); (4) C-1 complete. **Serves:** FR-16/20, X-05/X-19, G2.

**DDR-04 · Product universe & Shariah-sensitivity attribute** — `client.product`, `client.client.shariah_sensitive`. Generate a small seeded universe (~20–40) with asset class, currency, risk rating and a **screened-status placeholder only**; carry the Shariah-sensitive flag but no screening, zakat, purification or SSB rule-pack data (E-3). **AC:** (1) ≥1 product supports a pre-filled handoff (FR-20); (2) the flag exists with `as_of` but `0` screening-status computations are generated; (3) products are versioned; (4) C-1 complete. **Serves:** FR-20/25, E-3, A7.

**DDR-05 · Client interaction & memory history volume** — `client.interaction`, `graph.memory_fact` (seeded baseline). Generate recent interactions (calls/meetings/emails) with distinct `as_of` and seeded memory facts (preferences, commitments, confidence). **AC:** (1) ≥3 recent interactions for Wong with distinct `as_of`; (2) every memory fact has `confidence` + `as_of`; (3) enough history that all five brief sections render with ≥1 resolvable chip each; (4) 100% synthetic. **Serves:** FR-05/14, G1.

### 3.2 Market & signals

**DDR-06 · Canonical instrument universe** — `market.instrument`. Generate ~30–60 instruments with canonical IDs, source-symbol map, currency/unit, entitlement/licence tag (versioned). **AC:** (1) every holding resolves to exactly one instrument; (2) symbol map is versioned; (3) `licence_tag` present per instrument; (4) C-1 complete. **Serves:** FR-01/02/03, G6.

**DDR-07 · Tick stream (live + replay)** — `market.market_tick`, `replay_stream.parquet` + CSV twin. Generate a baseline recorded stream (~1,200 frames per `manifest v1.3` example) with original `feed_as_of` preserved, plus the +00:00 live-tick slot bound to a real `as_of`. **AC:** (1) replay frames `source_kind=replay`, `mode=replay`, original `as_of`; (2) live tick `source_kind=live_feed`, real wall-clock `as_of`; (3) zero invented/interpolated ticks and no last-price substitution (X-02/X-03); (4) stable `tick_key` dedup (NFR-18). **Serves:** FR-01/02/04/30, G3/G8, NFR-2/3/18.

**DDR-08 · Entitled news items** — `market.news_item`. Generate ~40–60 news items with headline, `source_id`, `as_of`, attribution and licence flag; ≥1 item attachable to Wong and ≥1 for S2. **AC:** (1) each item has non-null `source_id`/`as_of`/licence; (2) an unlicensed item is excluded from the brief; (3) the brief market section has ≥1 chipped news item; (4) C-1 complete. **Serves:** FR-03/14/15.

**DDR-09 · Signal rules, thresholds, entitlement & attribution config** — `demo_meta.config_version`, `version_registry`. Generate versioned config values: drift threshold 6%, rule-pack v1, warn 30s / stale 120s, ranking policy, `source_attribution` / `licence_tag` with `<source>` placeholder (OD-1/7/8). **AC:** (1) one tick crossing 6% yields exactly one signal stamped with rule-pack version; (2) config values are versioned and queryable with actor/timestamp; (3) `<source>` stays a placeholder until cleared; (4) config cannot disable non-negotiable labels (G11). **Serves:** FR-03/33/34, G11, OD-1/7/8.

### 3.3 Client Memory & Relationship Graph

**DDR-10 · Memory facts with provenance, confidence & versioning** — `graph.memory_fact`. Generate preferences, commitments, transcript-derived facts and RM corrections (`rm_manual`), with old versions retained as `superseded`. **AC:** (1) old + new versions of a corrected fact are both queryable with distinct timestamps; (2) low-confidence facts are flagged and suppressed from client-facing assertions (X-10); (3) the "daughter should join" fact carries a transcript evidence offset + confidence; (4) C-1 complete. **Serves:** FR-05/07/17/21, X-10.

**DDR-11 · Relationship graph sample (topology closure)** — `graph.graph_node`, `graph.graph_edge`, source-document refs. Generate a **concrete** 6–7-node synthetic seed (E-5) with typed node classes, typed edges and a source-document ref per node/edge. This closes the gap flagged at Phase 2 §13.5(b) and Phase 4 §9; the actual node list is Phase B's job (§5). **AC:** (1) 6–7 nodes with ≥3 typed classes and ≥3 typed edges; (2) every node/edge has a source-doc ref + `as_of`; (3) labelled a synthetic seed, not "canonical Tan family" research (E-5); (4) FK-clean. **Serves:** FR-06/24, E-5, G7.

**DDR-12 · Entitlement matrix & decisions** — `graph.entitlement_rule`, `graph.entitlement_decision`. Generate a versioned node-level matrix with ≥2 attendee classes and audited entitlement decisions. **AC:** (1) matrix version is stamped on every pack; (2) ≥2 attendee classes have distinct entitled node sets; (3) a matrix change writes a versioned C-4 event and marks prior packs `superseded`; (4) enforcement is in context assembly, not UI (FR-06). **Serves:** FR-06/24, G7, NFR-13.

**DDR-13 · Two per-attendee entitled pack versions** — `artefact.artefact` (family_pack ×2). Generate `Mr. Tan` and `Next-gen` versions differing **exactly** on the entitlement boundary. **AC:** (1) a diff including hidden/draft `jsonb` text yields 0 cross-node facts (G7/NFR-13); (2) each pack cites matrix version + `as_of`; (3) both packs are `approved` (C-3) before presentation; (4) a direct unentitled read is denied with a C-4 event. **Serves:** FR-24, G7, D8, NFR-13.

**DDR-14 · Shariah-sensitivity as node attribute pointing to the external project** — `graph.graph_node` attribute / `client.client.shariah_sensitive`. Generate a preference flag **only**, with a pointer to the external project, flag OFF; no screening outcomes, rule packs or estimates. **AC:** (1) the attribute carries `as_of` + an external-project reference id; (2) with flag OFF, no Shariah surface renders; (3) zero screening/zakat/SSB records generated; (4) C-1 complete. **Serves:** FR-25, E-3.

### 3.4 Lightweight CRM (DEMO CRM, additive)

**DDR-15 · `DEMO CRM (lightweight)` stand-in schema** — new `crm.*` (5–7 tables: contacts, interactions, tasks, opportunities, sync log, field mapping; each with a stated purpose). **AC:** (1) 5–7 tables, every one with a stated purpose (E-4); (2) every on-stage reference is visibly labelled `DEMO CRM (lightweight)`; (3) it lives inside the single Postgres instance in a **distinct schema**; (4) it is flagged architect-authored additive, synced to Phase 4, and `manifest v1.3` is not silently bumped (E-7). **Serves:** FR-18/19, E-4/E-7, global rule 3.

**DDR-16 · CRM old→new values, field mapping, sync log & idempotent write-back** — `client.crm_record`, `crm.*`, `demo_meta.config_version`, `artefact.demo_sink_message`. Generate seeded old values for the Wong record, a versioned field mapping, and a sync log with `succeeded`/`pending`/`failed` states. **AC:** (1) ≥5 CRM fields have seeded old values with `as_of`; (2) an old→new preview exists for every accepted change; (3) field mapping is versioned (FR-33); (4) a retried approval produces exactly one CRM change (NFR-18/G2); (5) a sink failure keeps an editable draft with safe retry, never false success (X-09). **Serves:** FR-18/19/33, X-09, G2, NFR-18.

### 3.5 Meeting / booking / email

**DDR-17 · Calendar events, appointment bookings & attendees** — calendar/CRM stub datasets. Generate `.ics`-shaped events, appointment bookings (primary reading of "booking", E-2) and attendee lists including ≥1 deliberately ambiguous attendee. **AC:** (1) ≥1 Wong event with attendees + `as_of` + time in SGT; (2) ≥1 ambiguous attendee triggers RM selection, never auto-merge (FR-14 AC-3); (3) consent is not inferred from calendar acceptance; (4) C-1 complete. **Serves:** FR-14/16, E-2 reading (i).

**DDR-18 · Scripted transcript / dialogue & extraction items** — seeded transcript, `artefact.extraction_item`. Generate speaker-labelled, time-stamped scripted dialogue (~10–20 utterances) with extractable decisions/preferences/commitments. **AC:** (1) every utterance has a speaker label + timestamp offset; (2) each extraction item links to a transcript evidence offset; (3) owner/due date are blank unless spoken (FR-17 AC-2); (4) the STUB declaration is present (X-15). **Serves:** FR-16/17, X-15, G9/F2.

**DDR-19 · Email threads, templates, disclosure wording & demo-sink messages** — `artefact.demo_sink_message`, config templates. Generate follow-up thread samples, a template + disclosure version, and demo-sink status records. **AC:** (1) template/disclosure versions are stamped on the draft; (2) the email state is `draft`, **no** `sent` state exists; (3) every factual statement links to evidence, a missing fact is omitted not invented (FR-22); (4) sink messages record exact content + provider-style status with zero egress (NFR-6). **Serves:** FR-19/22/23, G2, NFR-6, X-16.

### 3.6 Workflow & trust

**DDR-20 · Workflow instances, stages & one correlation_id** — `workflow.*`, `artefact.artefact`. Generate a blank seeded workflow state; the golden path yields 1 instance with an inspectable stage trace and one `correlation_id` linking signal → brief → review → approval → re-rank. **AC:** (1) one `correlation_id` spans the whole loop; (2) ≥2 stages cite the same `context_refs` fact ID; (3) state/current-stage/`correlation_id` are retrievable; (4) C-1 on every stage input. **Serves:** FR-08/09/21, D4.

**DDR-21 · Artefacts, versions & approval tokens** — `artefact.artefact/artefact_version/approval_token`. Generate `priority_list` v1..n, `meeting_brief` v1..n, `post_meeting_review`, `family_pack` ×2, and one immutable C-3 token (approver "Sarah", timestamp, `final_content_hash`). **AC:** (1) C-2 states run `draft → pending_review → approved`; (2) regenerations produce distinct versions with 0 duplicate CRM records (FR-15 AC-2); (3) the token is immutable; (4) before Approve: 0 writes / 0 sends / 0 submissions (G2). **Serves:** FR-15/18/19/21/27, C-2/C-3, G2, D3.

**DDR-22 · Audit events & read-access** — `audit.audit_event`, `audit.audit_archive`. Generate append-only events for every approval, mode switch, config change, blocked attempt, artefact **and read** (incl. observer/compliance reads), hash-chained; archive by `run_id` on reset. **AC:** (1) 100% of defined events present for a run; (2) read-access events present for observer/compliance; (3) reset never deletes the audit log; (4) the chain recomputes cleanly at acceptance. **Serves:** FR-27/32, NFR-5, G10, D3.

**DDR-23 · Scenarios, config versions, manifest & integrity report** — `demo_meta.scenario/generator_manifest/integrity_report/config_version/version_registry`. Generate S1–S4 overlays on one base world, `manifest v1.3` (read-only), `schema v1.3`, `dataset_checksum`, `extension_set` {TimescaleDB, `file_fdw`}, and a verdict. **AC:** (1) 4 scenarios, each declaring its triggering market event (FR-34); (2) same seed → identical manifest checksum (G4); (3) the manifest declares every file/table + row count and matches output; (4) a mismatch fails loud, blocks start, no auto-repair (X-20). **Serves:** FR-29/31/34, G4/G5/G6, NFR-3, X-20, E-7.

### 3.7 Data quality & integrity

**DDR-24 · Referential integrity & provenance completeness** — all fact tables. **AC:** (1) 0 orphan FKs and 0 facts missing any C-1 column (G6); (2) `as_of` + `source_id` + `mode` present on every tick in **both** flat-file and Postgres views (FR-31 AC-4); (3) a deliberately broken fixture names the offending record, returns `FAILED` and blocks start; (4) no auto-repair by inventing a parent row (X-20). **Serves:** FR-31, G6, NFR-17, X-20.

**DDR-25 · Determinism & no-real-data guard** — `demo_meta.generator_manifest`, all emitted files. **AC:** (1) two runs from one seed produce byte-identical files + checksum + artefact sequence (G4/NFR-3); (2) `ingested_at` is excluded from checksums; (3) a non-`demo_*` DSN or non-manifest file → `BLOCKED` + C-4 (FR-32 AC-4); (4) 0 real PII, `synthetic_marker` on every row. **Serves:** FR-29/31/32, G4, NFR-3/6, A1, OD-3.

**DDR-26 · Reset & demo-data boundary** — mutable tables + `audit_archive`. **AC:** (1) after reset the dataset checksum equals the seeded baseline; (2) reset completes ≤60s ×3 with audit archived (NFR-9/G10); (3) the prior run's audit is still queryable, no prior artefact is; (4) every artefact/UI label is identifiable as `SYNTHETIC DEMO DATA` and the tool is declared a demo-data generator, not a production migration tool. **Serves:** FR-32, G10, NFR-9, G11.

---

## 4. The surrounding systems Alan named — what each must supply

`[PRD]` Postures from `01` §1.1; E-3/E-4 ratify the Shariah boundary and the CRM stand-in. "Flow" is data direction relative to the workbench.

| System | Role in the journey | Posture | Minimum datasets it must expose | Flow | Human-approval boundary | One-line honesty label on stage |
|---|---|---|---|---|---|---|
| **(a) Lightweight CRM** | Source of seeded old values for the old→new preview (+00:14) and target of the idempotent write-back (+00:16); makes "how does the workbench interact with CRM?" visible | **SIMULATED / STUBBED** — `DEMO CRM (lightweight)` stand-in (E-4); real CRM remains a sink | 5–7 tables: contacts, interactions, tasks, opportunities, sync log, field mapping (`crm.*`) | **Bidirectional** — seeded values inbound; approved changes outbound to sink | Single Approve (C-3) before any write; idempotency key; no write before the tap (G2) | `DEMO CRM (lightweight) · SYNTHETIC DEMO DATA · writes to demo sink only` |
| **(b) Meeting** | Delivers the calendar trigger, consent gate, scripted capture and the "daughter should join" memory chip (+00:08/+00:10) | **STUBBED** (ASR/calendar) + **SIMULATED** (scripted transcript) | Calendar events, attendee lists, scripted transcript/dialogue, extraction items | **Inbound** (transcript/calendar → capture → memory) | Consent gate is the first human gate; memory write-back on approved items only (FR-16/17) | `STUB · scripted transcript · no microphone / no real ASR` |
| **(c) Booking** | Feeds the appointment → calendar event → brief trigger; primary reading = appointment/meeting booking (E-2) | **STUBBED / SIMULATED** | Booking records (id, client, start/end, channel, status, attendees) | **Inbound** | No approval to read; ambiguous attendees require RM selection, never auto-merge | `Appointment booking (DEMO) · synthetic` |
| **(d) Email** | Carries the follow-up email draft in the one review (+00:14) and the approved-send-to-sink moment (+00:16) | **STUBBED** (demo sink, zero egress) | Email threads, templates/disclosures, demo-sink messages | **Outbound** (draft → demo sink) | Explicit Approve & Send (C-3/FR-23), DNC + channel-consent checks; **no `sent` state** | `DEMO SINK — not delivered · draft · 0 sends` |
| **(e) Live market feed** | Supplies the +00:00 genuine tick — the on-stage trigger and headline proof (D1) | **REAL** in `live`; **SIMULATED** in `replay` | `market.instrument`, `market_tick` (live + recorded stream), `news_item`, entitlement/attribution config | **Inbound** | None — ticks are evidence, not client-facing artefacts (FR-01); licence/entitlement checked before append | `LIVE · <source> · as-of 09:58:14 SGT` **or** `REPLAY — recorded 09:58` |
| **(f) External Shariah project** | Optional boundary only; a node-attribute pointer, no screening/zakat/SSB rebuilt here (E-3) | **EXTERNAL** (flag-OFF, FR-25 P1/flag-OFF) | Screening status per instrument (or "not available"), rule-pack version, preference flag, API/file schema | **Inbound-only** (optional), pointer only | Nothing on stage by default; if enabled, `Estimate for discussion` + `Not a fatwa` are non-removable (G11) | `External Shariah project — preference flag only · not screened here · Not a fatwa` |

### 4.1 The three readings of "booking" (E-2) — do not silently pick one

`[PRD]` E-2 mandates all three be documented; the primary design assumes **(i)**.

- **(i) Appointment / meeting booking (calendar) — PRIMARY.** It sits on the meeting journey (FR-14/16), feeds the calendar trigger and the +00:08/+00:10 beats. Dataset = booking id, client ref, start/end (SGT), channel, status, attendee refs. No approval needed to read; no new gate.
- **(ii) Trade / order booking (back office).** Would add an order-record dataset. **But** FR-20 keeps trade execution HARD-BLOCKED — no table, no endpoint, no code path — and execution is a permanent non-goal (`01` §2.3). If confirmed, it may appear **only** as a `ready_for_manual_handoff` / `blocked` artefact with `execution disabled`, never a submission path; an actual order-booking table would need an architect-authored additive change plus an explicit on-stage statement that no order was placed. `[INFERENCE]` Recommendation: do not adopt; it implies a capability the frozen design refuses.
- **(iii) Booking entity / booking centre (where an account is booked).** Adds a small reference dataset (`centre_code`, jurisdiction, currency) and one attribute on `client.account`. Inbound-only, no workflow, no approval; it strengthens the jurisdiction/currency and entitlement answer (DI-04) but changes no beat or gate. `[INFERENCE]` Cheap to add if confirmed.

**What changes under (ii) vs (iii):** (ii) alters the honesty posture and risks an execution claim — it must be refused or reduced to reference-only; (iii) alters only reference data and account attributes, not the loop. Both sit on the intake list (DI-01/DI-08) for Alan to confirm. `[ASSUMPTION]` Until confirmed, Phase B builds (i) only.

---

## 5. The relationship graph sample — requirements level

`[PRD]` This closes the gap flagged at **Phase 2 §13.5(b)** ("A7 says seeded 4–6 nodes but no node list/topology is frozen") and **Phase 4 §9** ("entity graph topology is the clearest gap between design and a buildable card"). **E-5** mandates 6–7 nodes max, a synthetic seed, source-document refs, an entitlement matrix and two per-attendee entitled pack views. **Critical flag:** A7 says 4–6 nodes, E-5 says 6–7 — the counts are inconsistent; the architect must reconcile (§9 OQ-6) rather than silently pick one. `[INFERENCE]` The frozen FR-24 flow already names patriarch, trusts, holding entities and daughter's trust as *context*, and the run-of-show names `Mr. Tan` / `Next-gen` attendee classes; those are references, not a frozen topology. **The actual node list, edges and topology are Phase B's job — this section states acceptance criteria only.**

| What a concrete sample must specify | Requirements-level content (NOT the node list) |
|---|---|
| Node classes | ≥3 typed classes drawn from person / trust / holding-entity / advisor / account; 6–7 nodes total (E-5); labelled a synthetic seed |
| Edge types | ≥3 typed, directed relations with a stated meaning per type |
| Source-document refs | One per node **and** per edge: doc id, type, excerpt, `reviewed_by`, `as_of` — 100% synthetic |
| Entitlement classes | ≥2 attendee classes (per run-of-show: `Mr. Tan` / `Next-gen`) with distinct entitled node sets; versioned matrix |
| Two pack versions | `family_pack` ×2 in `pending_review` → `approved`, each labelled with attendee class + matrix version + `as_of` |
| Leakage-test expectation | 0 cross-node facts including hidden/draft `jsonb` text; direct unentitled read denied with C-4 |

**Acceptance criteria the sample must satisfy (architect-owned detail, requirements-owned pass conditions):**

1. 6–7 nodes, ≥3 node classes, ≥3 directed edge types; every node/edge has a synthetic source-document ref + `as_of` (DDR-11).
2. A versioned entitlement matrix with ≥2 attendee classes; every pack cites matrix version + `as_of` (DDR-12, FR-24 AC-3).
3. Two pack versions differ **exactly** on the entitlement boundary; a diff including hidden/draft `jsonb` text yields **0 cross-node facts** (G7, NFR-13, FR-24 AC-1/AC-2).
4. Both packs are `approved` (C-3) before presentation; a direct unentitled read is denied and logged (C-4).
5. Enforcement occurs in context assembly, not UI (FR-06 / X-11); the matrix is the single source of truth for RLS + assembly.
6. The seed is labelled `SYNTHETIC DEMO DATA` and **not** presented as research on a "canonical Tan family" (E-5).
7. FK-clean, C-1 complete on every node/edge/fact (G6/NFR-17).
8. No Shariah screening/zakat/SSB data on any node; at most a preference-flag attribute pointing to the external project (DDR-14, E-3).

---

## 6. THE DATA INTAKE REQUEST LIST FOR ALAN (centrepiece)

Alan said: *"you may be able to show meeting, and also booking, or email, which i can provide later, but you have to suggest to me what you need."* Here is the specific, actionable answer — not a restatement of his question. **Priority A** = genuinely necessary (blocks design freeze or the seed pack, or is a decision that changes dataset shape); **B** = materially improves realism, has a working synthetic stand-in; **C** = nice-to-have / optional. `"When needed"` uses four fixed windows. Every item defaults to a synthetic stand-in (§6.2). `[ASSUMPTION]` volumes.

### 6.1 Request table

| ID | Item | System / dataset | Why (beat / FR) | Exact minimum fields | Preferred format | Volume | Anonymisation | When needed | Default synthetic stand-in if absent | Pri |
|---|---|---|---|---|---|---|---|---|---|---|
| **DI-01** | **Decision: which reading of "booking" applies (E-2)** — i appointment / ii trade-order / iii booking entity | Booking | Unblocks CRM/calendar/order dataset shape; +00:08/+00:10, FR-14/16/18 | One of {i, ii, iii} + one-line confirmation | Plain text reply | 1 decision | n/a | **Before design freeze** | (i) appointment booking; (ii)/(iii) documented as alternates, no tables built | **A** |
| **DI-02** | **Market feed entitlement + attribution clearance (OD-1 restated as a data item — not resolved)** | Live market feed | +00:00 tick chip `<source>`, FR-01/02, G3/G8, headline D1 | `source_id`, `source_attribution`, `licence_tag`, written on-screen display clearance (y/n), Option A/B/C, delayed/real flag, TLS endpoint schema | API schema + written confirmation | 1 feed config | n/a (no client data); `[LICENSING-RISK]` if an unlicensed vendor name is shown | **Before rehearsal** (replay config before seed pack) | `<source>` versioned placeholder + recorded `replay` stream with `REPLAY — recorded 09:58`; no vendor invented | **A** |
| **DI-03** | **Decision: may any real client data / production extracts (even anonymised) be used? (OD-3 restated)** | Global | Compliance posture, A1, NFR-6; all beats | Yes/No + scope of any extract | Plain text decision | 1 | `[COMPLIANCE-RISK]` — highest-risk item; a "yes" reopens Phase 1 | **Before design freeze** | **No** — 100% synthetic, labelled | **A** |
| **DI-04** | **Jurisdiction + currency default (SGD / Singapore assumed)** | Client / portfolio / branding | Names, AUM, `as_of SGT` on +00:00; FR-01/14 | Base currency, jurisdiction, timezone, language, regulatory framing | Plain text | 1 | n/a | **Before seed pack** | SGD / Singapore / SGT / English; HKD + USD as minority currencies | **A** |
| **DI-05** | **Meeting transcript / scripted dialogue samples (speaker labels + timestamps)** | Meeting / ASR stub | +00:10 consent/capture, FR-16/17, memory chip "daughter should join" | `utterance_id`, `speaker_label`, `timestamp_offset` (HH:MM:SS), `text` | Plain text / .srt / .vtt / JSON | 1–3 dialogues × 10–20 utterances | `[COMPLIANCE-RISK]` — MUST be synthetic or fully redacted; no real client PII | **Before seed pack** | Fully synthetic scripted dialogue with declared `STUB` | **A** |
| **DI-06** | **CRM field mapping + write permissions** | Lightweight CRM | +00:14 old→new preview, +00:16 idempotent write-back, FR-18/19/33, G2, NFR-18 | `source_field`, `target_crm_field`, `writable` (y/n), `idempotency_key`, transform rule, version | CSV / JSON schema | 5–12 mappings | Field names only, no data | **Before seed pack** | Synthetic 5–8 field mapping with idempotency key; sink-only writes | **A** |
| **DI-07** | **Meeting metadata / calendar export (.ics) + attendee lists (incl. ≥1 ambiguous attendee)** | Meeting / calendar | Brief trigger, +00:08, FR-14 (no auto-merge), +00:20 packs | `event_id`, `subject`, `start`/`end` (SGT), channel, organiser, `attendee_refs`, `as_of`; attendee: `id`, `display_name`, `client_ref`, `role`, `entitlement_class`, `ambiguity_flag` | .ics / CSV / JSON | 3–8 events; 2–4 lists × 2–6 attendees | `[COMPLIANCE-RISK]` — synthetic only; no real names | **Before seed pack** | Synthetic calendar incl. one Wong 10:00 meeting + 1 ambiguous attendee | **B** |
| **DI-08** | **Booking records** (reading-dependent, see DI-01) | Booking | Appointment → calendar → brief; +00:08/+00:10 | (i) `booking_id`, `client_ref`, `start`/`end`, `channel`, `status`, `attendee_refs`, `source`; (ii) `order_id`, `account`, `instrument`, `qty`, `status` (no execution); (iii) `centre_code`, `jurisdiction`, `account_ref` | CSV / .ics / JSON / API schema | 3–8 records | `[COMPLIANCE-RISK]` — synthetic only | **Before seed pack** (after DI-01) | (i) synthetic appointment bookings; (ii)/(iii) reference-only, no execution path | **B** |
| **DI-09** | **Email thread samples** | Email | +00:14 follow-up draft, recent-interactions brief section, FR-19/22 | `thread_id`, `message_id`, `from`/`to` (synthetic), `sent_at`, `subject`, `body`, `direction`, `client_ref` | .eml / JSON / plain text | 2–4 threads × 2–5 messages | `[COMPLIANCE-RISK]` — MUST be synthetic or redacted; no real addresses | **Before seed pack** | Synthetic threads on a demo domain | **B** |
| **DI-10** | **Disclosure / template / consent wording (OD-4 restated as data)** | Email / consent / config | +00:10 banner, F2, FR-16/22/23/33 | `template_id`, `version`, body with placeholders, disclosure text, consent accept/decline/withdraw wording, signer/approver | Plain text / JSON / PDF | 2–3 templates + 1–2 disclosures + 1 consent wording | Template text only; no client data | **Before rehearsal** (copy before seed pack) | Illustrative wording flagged "not legally approved" (A5/OD-4) + `STUB` | **B** |
| **DI-11** | **CRM sample interaction / task / opportunity records** | Lightweight CRM | +00:14 old→new preview, FR-18, seeded interactions for brief | `record_id`, `type` (interaction/task/opportunity), `client_ref`, `occurred_at`/`as_of`, `subject`, `status`, `owner`, `old_value(s)`, `notes` | CSV / JSON | 10–30 records | `[COMPLIANCE-RISK]` — synthetic only | **Before seed pack** | Fully synthetic records in `DEMO CRM (lightweight)` | **B** |
| **DI-12** | **Portfolio & holdings samples + product universe + suitability/KYC field list** | Client / account / holding / product | +00:02 drift, +00:08 brief, FR-03/14/20, FR-25 flag-off | `client_ref`, `account_id`, `instrument_id`, `qty`, `market_value`, `currency`, `as_of`, `target_weight`, `cost_basis`; product: `id`, `name`, `asset_class`, `risk_rating`, `shariah_screened` placeholder; KYC: list of suitability attribute names | CSV / JSON / API schema / field-list doc | 30–50 clients × 5–12 holdings, 3–6 accounts; 20–40 products | `[COMPLIANCE-RISK]` — synthetic only; no real positions/KYC | **Before seed pack** | Fully synthetic portfolio with Wong's >6%-drift-capable holding; hard-stop suitability boundary only | **B** |
| **DI-13** | **Household / entity documents for the graph sample (trust deed, entity structure)** | Graph | +00:20 range beat, FR-24, source-document refs, G7 gap closure | `doc_id`, `doc_type`, `node_ref(s)`, `excerpt`/text, `reviewed_by`, `as_of`, `entitlement_class` | PDF (synthetic) / plain text / JSON | 3–6 docs for 6–7 nodes | `[COMPLIANCE-RISK]` — MUST be synthetic; no real trust deeds | **Before seed pack** | Synthetic source-document refs labelled `SYNTHETIC DEMO DATA` | **B** |
| **DI-14** | **Shariah project: what it exposes + whether any may appear on stage (E-3 boundary)** | External Shariah project | FR-25 flag-off, node-attribute pointer, §4(f) | Screening status per instrument (or "not available"), `rule_pack_version`, `preference_flag`, API/file schema, on-stage permission (y/n) | API schema / JSON / plain text | 1 schema + optional 20–40 status rows | `[COMPLIANCE-RISK]` — synthetic; no real rulings / "not a fatwa" | **Optional** / before rehearsal if on stage | Preference-flag attribute only, pointing to the project; **zero** screening/zakat/SSB data generated | **C** |
| **DI-15** | **Branding / naming / leader audience profile** | Global / copy | Credibility of names on chips/brief; which beats to emphasise | Firm name, RM display name, client name style, product naming convention, logo usage permission; audience roles/seniority, likely probes, language | Plain text / brand guide / sample screenshot | 1 set | `[LICENSING-RISK]` — confirm no real client names; logo permission | **Before rehearsal** | "Sarah (RM)", synthetic client names, generic senior-banking-leadership profile | **C** |
| **DI-16** | **Real screenshots of the existing RM Workbench / surrounding systems to echo + any API schema / field mapping** | Global / UI / systems | Optional visual echo of the current system; systems-view realism | Screen name, image, elements to echo (labels, chips, layout), usage permission; optional API schema / entity names | PNG / PDF sample screenshot / API schema / plain text | 1–5 screenshots | `[COMPLIANCE-RISK]` — must be redacted of all real client data / PII | **Optional** | No echo; use frozen SCR-01…14 / CMP-01…16 + `DEMO CRM (lightweight)` + labelled stubs | **C** |
| **DI-17** | **Live market feed sample schema / recorded tick stream (if one exists)** | Live market feed | Replay-stream realism, `replay_stream.parquet` shape, FR-01/30 | Instrument symbols, tick fields (`price`, `currency`, `as_of`, `source_id`, `licence_tag`), timestamp format, sample frames | API schema / CSV / Parquet sample | 1 schema + ~100 sample frames | n/a (no client data); `[LICENSING-RISK]` if redistributed | **Before seed pack** | Fully synthetic recorded tick stream with original `as_of` preserved | **B** |

### 6.2 If you provide nothing

`[ASSUMPTION]` The demo still works **entirely on generated synthetic data**. Phase B generates one deterministic world from one seed: SGD/Singapore, "Sarah (RM)", Wong's 6% drift, a 6–7-node synthetic Tan graph, a `<source>` placeholder with a `REPLAY — recorded 09:58` fallback, illustrative (non-legal) consent/template wording, a `DEMO CRM (lightweight)` with 5–7 tables, and appointment bookings only. Every beat, gate G1–G11, F1/F2 and the reset still run. What is **less convincing**, precisely: (1) the +00:00 tick cannot claim a genuinely licensed `LIVE` source, so D1 leans on the honest replay fallback — the headline is weaker; (2) scripted dialogue, email and CRM wording sound generic rather than matching the firm's real tone of voice; (3) no real-screen echo, so the UI will not visually match the existing workbench; (4) jurisdiction/currency may be wrong for the actual audience, making AUM and `as_of` look imported; (5) "booking" shows only appointment booking and we must say so on stage; (6) the Shariah beat stays a labelled pointer with no on-stage content. None of these block the loop; all reduce the "this is *our* world" credibility that a leadership audience responds to.

### 6.3 Critical triage — necessary vs nice-to-have vs risky

- **Genuinely necessary (send first):** DI-01 (a decision that changes dataset shape), DI-02 (the only item that can collapse the headline claim — OD-1, **unresolved by design**), DI-03 (single largest compliance determinant), DI-04 (realism baseline), DI-05 (the capture beat has no content without it), DI-06 (old→new preview + idempotent write-back need a mapping). These are **A**.
- **Nice-to-have, safe stand-ins:** DI-07…DI-13, DI-17 are **B** — they improve legibility but Phase B can synthesise all of them. DI-14/15/16 are **C** — deferrable without touching a gate.
- **Would create compliance / licensing risk if real data were sent:** DI-03 (any real PII or production extract — **highest**), DI-05 (real transcript), DI-07/08/09/11/12/13 (real names, addresses, positions, KYC, trust deeds), DI-16 (real screenshots carrying PII), DI-02/DI-17 (unlicensed vendor attribution or redistributed ticks shown on stage), DI-14 (real religious rulings → "not a fatwa" / SSB exposure), DI-15 (real client names / unauthorised logo). `[PRD]` A1/OD-3 default = **No real data, ever**; if Alan sends any of these as real data, the intake must be refused or redacted before it reaches the seed pack, and DI-03 must be re-decided.

---

## 7. Data sensitivity & honesty rules (binding on every fact)

`[PRD]` Non-negotiable, derived from A1, OD-3, C-1, FR-26/27/32/33, X-02/X-03/X-16, G2/G8/G11, NFR-6.

1. **No real PII.** 0 real client data; every name, ID, address, position and document is synthetic or fully redacted. `[ASSUMPTION]` no production extracts even anonymised without an explicit OD-3 decision (DI-03).
2. **C-1 on every fact.** All 7 columns (`source_id`, `source_kind`, `as_of`, `ingested_at`, `confidence`, `mode`, `version_stamp`) non-null on every stored fact (G6/NFR-17).
3. **Permanent `SYNTHETIC DEMO DATA`.** Present to the last frame; not removable by config (G11). The generator is a demo-data tool, not a production migration tool.
4. **No bare statements.** A statement with no provenance is suppressed as `insufficient evidence` with a C-4 suppression event — never rendered as unlabelled text (FR-26, G1).
5. **No invented ticks or last-price substitution.** F1 degrades to `STALE`/`unavailable`; stale rows stay queryable but labelled; a switch to `replay` is announced (X-01/02/03, G8/G9).
6. **No `sent` state.** The demo sink records exact final content + provider-style status with zero egress; email stays `draft · DEMO SINK — not delivered`; 0 sends (FR-19/23, NFR-6, X-16).
7. **No trade execution path.** No table, endpoint or code path; ticket handoff only, `execution disabled` (FR-20, HARD-BLOCKED).
8. **No silent `LIVE` on replay.** `LIVE` is impossible while bound to `replay_stream` (G8, DB `CHECK`).

---

## 8. Traceability & coverage

### 8.1 DDR → MVP-FR / Gate / NFR

| DDR | FR / Gate / NFR | DDR | FR / Gate / NFR | DDR | FR / Gate / NFR |
|---|---|---|---|---|---|
| 01 | FR-05/11/29 · A1/NFR-6 | 10 | FR-05/07/17/21 · X-10 | 19 | FR-19/22/23 · G2/NFR-6 · X-16 |
| 02 | FR-03/14/31 · G6 · NFR-17 | 11 | FR-06/24 · E-5 · G7 | 20 | FR-08/09/21 · D4 |
| 03 | FR-16/20 · X-05/X-19 · G2 | 12 | FR-06/24 · G7 · NFR-13 | 21 | FR-15/18/19/21/27 · C-2/C-3 · G2 · D3 |
| 04 | FR-20/25 · E-3 · A7 | 13 | FR-24 · G7 · D8 · NFR-13 | 22 | FR-27/32 · NFR-5 · G10 · D3 |
| 05 | FR-05/14 · G1 | 14 | FR-25 · E-3 | 23 | FR-29/31/34 · G4/G5/G6 · NFR-3 · X-20 · E-7 |
| 06 | FR-01/02/03 · G6 | 15 | FR-18/19 · E-4/E-7 · rule 3 | 24 | FR-31 · G6 · NFR-17 · X-20 |
| 07 | FR-01/02/04/30 · G3/G8 · NFR-2/3/18 | 16 | FR-18/19/33 · X-09 · G2 · NFR-18 | 25 | FR-29/31/32 · G4 · NFR-3/6 · A1 · OD-3 |
| 08 | FR-03/14/15 | 17 | FR-14/16 · E-2(i) | 26 | FR-32 · G10 · NFR-9 · G11 |
| 09 | FR-03/33/34 · G11 · OD-1/7/8 | 18 | FR-16/17 · X-15 · G9 | | |

### 8.2 DI → journey beat / system

| DI | Beat / system | DI | Beat / system | DI | Beat / system |
|---|---|---|---|---|---|
| 01 | +00:08/+00:10 · booking (E-2) | 07 | +00:08/+00:20 · meeting/calendar | 13 | +00:20 · graph / source-doc refs |
| 02 | +00:00 / F1 · live market feed | 08 | +00:08/+00:10 · booking | 14 | +00:20 (flag-off) · external Shariah |
| 03 | all beats · global compliance | 09 | +00:08/+00:14 · email | 15 | all beats · branding/audience |
| 04 | +00:00/+00:08 · client/portfolio | 10 | +00:10/F2 · consent/email/config | 16 | all beats · UI/systems echo |
| 05 | +00:10 · meeting/ASR stub | 11 | +00:14 · lightweight CRM | 17 | +00:00/F1 · market feed |
| 06 | +00:14/+00:16 · lightweight CRM | 12 | +00:02/+00:08 · portfolio/product | | |

**Coverage statement — honest.** All 14 beats (incl. F1, F2, end card) in §2 map to at least one DDR; all 26 DDRs map to a frozen FR/Gate/NFR; all six surrounding systems and all three booking readings have an intake item. **Deliberately not covered here (not gaps):** (i) the actual graph node list/edges/topology → Phase B (E-5, §5); (ii) concrete sample CSV/JSON rows → Phase B seed pack; (iii) component/screen/DDL/interface design → frozen, unchanged (E-1/E-7); (iv) numeric realism calibration (AUM bands, drift magnitude, name sets) is `[ASSUMPTION]` pending DI-04/DI-12; (v) OD-1/7/8 feed values and OD-3/OD-4 remain **open by design** — restated as data items, not resolved (E-8); (vi) FR-25 stays P1/flag-OFF; (vii) no decision is invented for the A7 (4–6) vs E-5 (6–7) node-count inconsistency — escalated to §9. One genuine dependency: DI-08 cannot be specified until DI-01 is answered.

---

## 9. Open questions for Alan (critical; answer with the DI IDs)

| # | Question | Why critical | Default if unanswered |
|---|---|---|---|
| **OQ-1** | **Which of the three readings of "booking" applies?** (E-2 / DI-01) | It changes the CRM/calendar/order dataset shape and, under reading (ii), collides with the HARD-BLOCKED trade-execution non-goal. | (i) appointment booking; (ii)/(iii) documented only. |
| **OQ-2** | **Where exactly is the Shariah project boundary?** (E-3 / DI-14) — what may it expose, and may any of it appear on stage? | Rebuilding screening/zakat/SSB here is forbidden; a real ruling on stage triggers "not a fatwa"/SSB exposure. | Preference-flag pointer only, flag OFF, nothing on stage. |
| **OQ-3** | **May any real screenshots or real branding/naming be used?** (DI-15/DI-16) — with what permission and redaction? | Real screenshots often carry client PII; real names/logos carry licensing risk; "may appear on stage" is an OD-7/OD-8-class decision. | No echo; frozen SCR/CMP + synthetic names; generic framing. |
| **OQ-4** | **Currency / jurisdiction default SGD / Singapore — confirm or override?** (A2 / DI-04) | It sets every AUM figure, `as_of SGT` chip and the +00:00 tick label; a wrong default makes the whole book look imported. | SGD / Singapore / SGT / English; HKD + USD minority. |
| **OQ-5** | **Does the leader audience want the family-graph range beat at all?** (OD-9 / DI-13) | A tight 20-minute window (loop + F1 + F2 + Q&A + tagline) may cut +00:20; cutting it removes the G7 proof but not the loop. | Keep FR-24 as the single range moment, one-click jump; FR-25 first-to-cut. |
| **OQ-6** | **Reconcile the node-count inconsistency: A7 says 4–6, E-5 says 6–7.** | Both are frozen-ish statements; the architect must not silently pick one for the graph sample. | 6–7 (E-5), flagged as an additive reconciliation note, not a silent choice. |
| **OQ-7** | **Confirm no real client data ever, including anonymised production extracts?** (OD-3 / DI-03) | Single largest compliance determinant; a "yes" reopens Phase 1. | **No** — 100% synthetic (A1). |
| **OQ-8** | **Should the demo echo the real meeting/booking/email/CRM system schemas, or use labelled stubs?** (DI-16) | Echoing real systems improves realism but risks implying real integrations that are STUBBED. | `DEMO CRM (lightweight)` + labelled stubs; no implied vendor integration. |

`[PRD]` Q1/Q2/Q3 and OD-1…11 remain open per E-8; this addendum does not resolve them, it only restates OD-1/OD-3/OD-4/OD-9 as *data intake items*.

---

## 10. Global-rules compliance note

**Rule 1 (simplicity / no re-run):** no new product-design phase, no new screens/components, no re-derivation of frozen FRs/gates/NFRs — frozen IDs are cited, and 26 DDRs reference C-1/C-2/C-3/C-4 instead of restating them; the Out-of-Scope boundary is as deliberate as the In-Scope one. **Rule 2 (annotation discipline):** `[PRD]` / `[INFERENCE]` / `[ASSUMPTION]` mark every non-factual claim; no filler, no essay on AI in wealth management; any future code comments would be Chinese. **Rule 3 (contract freeze):** nothing here changes 8 schemas / 40 tables, IF-01…22, EV-01…20, `manifest v1.3`, `schema v1.3`, the extension set or NFR-1…18; the new `crm` schema is flagged architect-authored additive, synced to Phase 4, and `manifest v1.3` is not silently bumped (E-7). **Rule 4 (on-disk):** this deliverable is persisted at `deliverables/11_Demo_Data_Requirements_and_Intake.md`; it contains no application code, no runnable scripts, no executed DDL, no scaffold — only requirements, tables and prose. Sample CSV/JSON rows, diagrams and the concrete node list are Phase B's job. **Design only — no code has been written.**

---

*End of Phase A deliverable. Stable IDs introduced: `DDR-01…26`, `DI-01…17`, `OQ-1…8`. All Phase 1–4 IDs referenced, never renumbered. Hand-off: full verbatim text to team-lead → solution-architect (Phase B).*

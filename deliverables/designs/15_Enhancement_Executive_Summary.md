# Next-Generation RM Workbench — MVP Enhancement Addendum
## Demo data, surrounding systems, diagrams and vendor adapters

**Audience:** Company senior leadership demo of the *envisioned RM journey*; internal design team.
**Owner:** Qi Huolin (Delivery Director), software-dev-team.
**Date:** 6 November 2026.
**Status:** **DESIGN ONLY.** No application code, no runnable generator, no scaffold, no executed DDL, no vendor account opened, no credentials created.
**Language:** English. All final user-facing deliverables are in English.
**Relationship to the base package:** This is an **addendum**, not a rewrite. `RM_Workbench_MVP_Design_Package.md` and `00`–`04` remain the frozen design baseline. Nothing in Phase 1–4 is reopened.

**Positioning (Alan, 6 Nov 2026):** The purpose of this solution is to demonstrate a **next-generation Relationship Manager workbench and how it uses AI**. The **only human user is the Relationship Manager** — there is no client-facing UI; the client is represented by synthetic data / simulation only. This is why the demo is single-screen (OD-6) and RM-centric, and why Retell (a client voice agent) is deferred to MVP2.

---

## 1. Why this addendum exists

Alan's enhancement request (verbatim):

> "i think you need to enhance, as i said, i need to use a generator to generate some fake data to populate for a demo, the firtst MVP should be demo to our company's leader aboutt he journey that we envision, so data is important, i need you to show me diagram as well on archicture and also on coponent and systesm, for example CRM, you may need to have a very lightweight CRM built with a few table, so i can visualize how the workbench interact with it, i do have another project that that sharia , you also need to sample the relationship graph too , you may be able to show meeting , and also booking , or email, which i can provide later, but you have to suggest to me what you need"

A later instruction (verbatim):

> "for CRM, i plan to use hubspot free as the demo, i may use retell.ai as an agent , please plan this in"

**The gap, stated critically.** The base package designed the generator as a *mechanism* — one deterministic seed → flat files → one-transaction Postgres load → integrity validation → reset. It never showed the *data*. For a leadership journey demo that is a material defect: the audience cannot see the world the copilot is reasoning over, and "how does the workbench interact with CRM?" had no visual answer. The base package also left the entity-graph topology explicitly flagged as *the clearest gap* (`02` §13.5(b), `04` §9).

**This addendum makes the data and the surrounding systems visible.** It adds concrete synthetic rows, a lightweight CRM, a sampled relationship graph, meeting/booking/email system context, an external Shariah boundary, eight diagram families, and an evidence-based vendor adapter ruling. It does not add screens, components, or new product design (E-1).

---

## 2. The seven gaps and where each is closed

| # | Gap in the base package | Closed by |
|---|---|---|
| 1 | No concrete fake records — the journey was abstract | `13_Demo_Seed_Pack.md` + `demo_data/` — 57 files, 43 CSV / 1,277 rows, 12 JSON |
| 2 | No lightweight CRM as a *system* with its own few tables | `12_…` §4 — exactly 6 `crm.*` tables, each with stated purpose, DDL spec, sample rows |
| 3 | Relationship graph topology not frozen (flagged as clearest gap) | `12_…` §6 — exactly 6 nodes, 8 edges, 8 source docs, entitlement matrix, two entitled packs |
| 4 | Meeting / booking / email absent as external systems | `12_…` §3 D-F, §7 + seed rows `bk_01…bk_06`, `evt_01…evt_06`, `thr_01…thr_04` |
| 5 | Shariah project was an out-of-scope flag only | `12_…` §8 — inbound-only external boundary, flag OFF, preference pointer, zero screening/zakat/SSB records |
| 6 | No system-context / component / data-landscape diagrams | `12_…` §3 — eight validated Mermaid diagrams D-A…D-H |
| 7 | No explicit "what Alan must provide" list | `11_…` §6 `DI-01…17`, plus `14_…` §8 `DI-18…25` |

---

## 3. Deliverable index (everything on disk under `deliverables/`)

### 3.1 Frozen baseline — unchanged

| File | What it holds |
|---|---|
| `00_Shared_Design_Brief.md` | Base brief, PRD digest, demo narrative, hard requirements |
| `01_Requirements_Specification.md` | `MVP-FR-01…34`, `C-1…5`, `X-01…20`, `G1…G11`, `D1…D10`, NFR inputs |
| `02_Product_Design_Specification.md` | `SCR-01…14`, `CMP-01…16`, 8 states, generator UX, §13.5(b) graph gap |
| `03_Technical_Solution.md` | **THE FREEZE LINE**: 8 schemas / 40 tables, `SVC-01…18`, `DF-01…06`, `IF-01…22`, `EV-01…20`, `NFR-1…18`, TimescaleDB + `file_fdw`, §7 generator |
| `04_Feature_Unit_Plan.md` | `FU-01…24`, batches, critical path, run-of-show, §9 graph gap |
| `RM_Workbench_MVP_Design_Package.md` | Executive entry point for the baseline; now carries a pointer to this addendum |

### 3.2 This enhancement

| File | Lines | What it holds |
|---|---|---|
| `10_Data_Enhancement_Brief.md` | 99 | Verbatim request, gap analysis, `H1…H6`, ratified `E-1…E-8`, plus §8 amendment `E-9…E-14` |
| `11_Demo_Data_Requirements_and_Intake.md` | 282 / 7,953 w | Phase A: 14-beat journey map, `DDR-01…26`, six surrounding systems, three booking readings, graph ACs, **`DI-01…17`**, `OQ-1…8` |
| `12_Demo_Data_and_Systems_Architecture_Enhancement.md` | 1,253 / 14,664 w | Phase B architecture: **8 Mermaid diagrams**, 6-table CRM DDL spec, sampled graph, Shariah boundary, journey→data map, generator spec, Phase 4 sync, §14 vendor amendment |
| `13_Demo_Seed_Pack.md` | 563 / 7,622 w | Phase B data guide: file inventory, FK map, C-1 conventions, beat→row map, entitled packs, DI stand-ins, validation, deviations |
| `14_Vendor_Adapter_Ruling_HubSpot_Retell.md` | — | **Lead ruling** `E-9…E-16`: evidence register (HubSpot Free / Retell AI), HK/SG governance context, architecture delta, `DI-18…25`, `OQ-9…13`, cost/go-no-go, contract-freeze note |
| `15_Enhancement_Executive_Summary.md` | — | This document — the single entry point |

### 3.3 The seeded world — `demo_data/` (57 files)

- **Control (6):** `README.md`, `checksums.sha256` (52 lines), `schema_contract.json` (35 FK rules + `uuid_resolution`), `integrity_report.json` (verdict PASS, 31 checks), `manifest_v1.3.json` (frozen, read-only, 51-file scope), `manifest_addendum_crm.json` (additive declarations, Phase-4 sync).
- **Client / portfolio / market:** 42 clients, 65 accounts, 48 instruments, 342 holdings, 325 allocation targets, 24 products, plus live tick (1), replay ticks (120 representative frames; full 1,200 generator-emitted, not padded), 1 signal, 8 news items, 2 feed-status rows.
- **Graph / memory:** 19 memory facts, exactly 6 nodes, 8 edges, 8 source docs, 12 entitlement-matrix rows, 6 decisions, 2 family packs.
- **CRM (exactly 6 tables):** `crm_contacts`, `crm_interactions`, `crm_tasks`, `crm_opportunities`, `crm_field_mapping`, `crm_sync_log`; plus `crm_old_new_preview.csv` as a review artefact (not a 7th table).
- **Meeting / booking / email:** 6 bookings, 6 calendar events, 14 attendees, 16 utterances, 6 extraction items, 4 threads, 4 messages (`draft` only), 3 templates.
- **Workflow / trust:** 8 artefacts, 1 immutable approval token, 1 workflow instance, 6 stages, 18 audit events, 20 config versions, 10 version-registry rows, **5 scenarios** (`S1` golden path, `S1-R` opt-in Retell complete-run variant, `S2`, `S3`, `S4`), 3 demo-sink messages.
- **Vendor adapters:** `hubspot_portal_seed.json`, `hubspot_api_exchange.json` (placeholder token only), `retell_call.json`, `adapter_bindings.csv`, `vendor_health.csv`.

Every CSV row carries the full 7-column C-1 provenance envelope plus `synthetic_marker = 'SYNTHETIC DEMO DATA'`; every JSON has a top-level `synthetic_marker`.

---

## 4. The eight diagram families (the visual answer to "show me diagrams")

All eight are validated Mermaid blocks in `12_…` §3, short-labelled and projector-legible, each followed by "what a leader should notice" and the applicable honesty label. Posture colours are consistent: green REAL, teal `REAL (SANDBOXED)`, blue SIMULATED, amber STUBBED, purple EXTERNAL, red HARD-BLOCKED.

| ID | Diagram | What leadership sees |
|---|---|---|
| **D-A** | System / context architecture | One demo host, Postgres 16 (8 frozen schemas / 40 tables + additive 6-table `crm` projection), live feed, HubSpot sandbox, optional Retell, Shariah external pointer, and three red hard-blocked paths |
| **D-B** | Component / systems view | `SVC-01…18` grouped, `IF-A01` / `IF-A02` adapter bindings, and the unbroken separation boundary: `SVC-16` Presenter READ-ONLY / `SVC-17` Operator SOLE WRITER |
| **D-C** | CRM interaction | The real interaction: seeded old values → old→new preview (+00:14) → **single Approve** → REST PATCH → read-after-write GET verify → `crm_sync_log.succeeded` → email `draft` to demo sink; plus `local_stub` fallback and a crossed-out Retell auto-write |
| **D-D** | Sampled relationship graph | 6 typed nodes, 8 directed edges, `doc_*` refs, and the two entitled pack views with hidden nodes marked |
| **D-E** | Demo-data entity landscape | Tables by schema with FK arrows and row counts; HubSpot/Retell drawn as dashed **external references, not Postgres tables** |
| **D-F** | Meeting / booking / email | `bk_*` → `evt_*` → brief trigger → consent gate → `utt_*` → extraction → `thr_*` draft → demo sink; `retell_test` branch and `scripted_stub` fallback |
| **D-G** | Journey sequence (optional) | Beat timings −00:30 → +00:20 with F1/F2 branches |
| **D-H** | Adapter binding state (new, E-11) | 2 adapters × 3 bindings, announced switch + C-4 event on every **between-run** transition (**E-15**: no mid-call switch) |

---

## 5. The leadership journey, now backed by exact rows

The demo remains a **depth-thinned full loop**, not a feature count. One live market tick closes the loop end-to-end in ~20 minutes.

| Beat | Concrete rows | On-stage chip | Posture |
|---|---|---|---|
| −00:30 | seed `20261105`, `RM-WB-DEMO-v1.3`, `manifest v1.3`, `integrity_report` PASS, `map_01…map_08`, HubSpot reachable check | `READY · LIVE · integrity verified · SYNTHETIC DEMO DATA` | REAL + SIMULATED |
| +00:00 | `tk_live_0001`, `ins_syn_asean_eq_01` / `SYN-ASEQ-01`, `2026-11-06 09:58:14 SGT`, price **25.90 → 26.45** | `MARKET EVENT · SYN-ASEQ-01 · <source> · as-of 09:58:14 SGT · LIVE` | **REAL** |
| +00:02 | `sig_0001`, `cl_wong_001`, `hd_0001`, drift **5.88pp → 6.12pp** crossing the 6.00pp rule-pack threshold | `Wong portfolio drifted 6% from target · tick as-of 09:58:14 · rule-pack v1` | REAL (derived) + SIMULATED (holdings) |
| +00:06 | `priority_list` v1→v2, 42-client book, ranking-policy version | `Opportunity — rebalancing · ↑3 (from 4)` | SIMULATED |
| +00:08 | `meeting_brief` v1, `bk_01`, `evt_01`, `att_amb_01`, 5 sourced sections | `Portfolio, as of prior close` / `Client preference, verified` | SIMULATED + STUBBED |
| +00:10 | `utt_09` @ `00:03:12` / `confidence 0.94`, `mf_001`, `ex_01…ex_06` | `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)` **or** `STUB · declared` | SIMULATED / STUBBED |
| +00:14 | `post_meeting_review`, 8 old→new field pairs `pv_01…pv_08`, `fmv_20261105_1`, `msg_02` draft | `ticket · suitability current · execution disabled` / `CRM old → new` | SIMULATED + STUBBED |
| +00:16 | `appr_001` — `Approved by Sarah (RM) · 10:14:32`, `sync_01…06` with six distinct idempotency keys, `audit_events`, `corr_demo_0001` | `Approved by Sarah (RM) · 10:14:32 · CRM write-back → sandbox portal succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades, 0 real dialled calls` | `REAL (SANDBOXED)` + STUBBED |
| +00:18 | `priority_list` v3, `meeting_brief` v2, approved preference now canonical | `Client preference, verified · approved 10:14:32` | SIMULATED |
| +00:20 | `nd_01…nd_06`, `ed_01…ed_08`, `doc_01…doc_08`, `ent_matrix_v1`, `family_pack_mr_tan` / `family_pack_next_gen` | `Trust deed, reviewed by Sarah · family_pack_… · ent_matrix_v1` | SIMULATED (synthetic seed) |
| F1 | last tick age 47s, **no new tick**, `replay_stream.parquet` + CSV twin, market section `unavailable` | `FEED STALE · age 47s` → `REPLAY — recorded 09:58` | SIMULATED — never `LIVE` (G8 DB CHECK) |
| F2 | `cl_lim_002` consent declined, **no transcript**, `rm_manual` low-confidence notes | `rm_manual · low-confidence · review required` | STUBBED |
| End | honesty chrome only | `SYNTHETIC DEMO DATA · DEMO SINK — not delivered · 0 sends · 0 trades · 0 real dialled calls · 0 real client-facing sends · 0 real PII` | permanent to last frame (G11) |

Locked tagline from `RM_Workbench_Video_Treatment.md`: **"AI orchestrates the workflow. You orchestrate the relationship."**

---

## 6. The surrounding systems

| System | Role in the demo | Posture |
|---|---|---|
| **HUBSPOT FREE · DEMO SANDBOX PORTAL** | Primary external CRM binding; dedicated free portal, 100% synthetic contacts/deals/tasks/activities | **`REAL (SANDBOXED)`** — real vendor service, synthetic records, no real person contacted |
| **CRM ADAPTER · LOCAL PROJECTION** | The "very lightweight CRM built with a few tables": exactly 6 `crm.*` tables inside the single Postgres instance, re-purposed as projection + field mapping + idempotency/outbox ledger | SIMULATED / local state |
| **RETELL AI (OPTIONAL)** | Voice/transcript adapter; simulation/test call with a synthetic caller producing `utt_01…utt_16` + extraction candidates | SIMULATED — off the critical path |
| **Meeting / Booking / Email** | `bk_01…bk_06` appointments, `evt_01…evt_06` `.ics`-shaped events, `thr_01…thr_04` threads with `draft` only | STUBBED |
| **Live market feed** | `+00:00` genuine tick; `<source>` versioned placeholder, entitlement/attribution checked before append | REAL in `live`, SIMULATED in `replay` |
| **External Shariah project** | Inbound-only preference-flag pointer; `nd_01` carries `shariah_preference_flag=OFF` + `external_ref=shariah_project_ext` | EXTERNAL — flag OFF, nothing on stage |
| **Demo sink** | Email draft endpoint, zero egress | STUBBED |

**Booking ambiguity (E-2, not silently resolved):** primary = (i) appointment/meeting booking. (ii) trade/order booking and (iii) booking entity / centre are reference-only alternates with **no tables and no execution path**; (ii) would collide with the HARD-BLOCKED trade-execution non-goal. `DI-01` remains open for Alan to confirm.

---

## 7. Vendor adapter ruling (HubSpot Free + Retell AI) — the critical part

Alan's "i plan to use hubspot free … i may use retell.ai" **amends E-4**, which had frozen the CRM as an in-Postgres stand-in with "real CRM remains a demo sink". A real external SaaS is not a stub; treating it as a label swap would misstate the architecture and break the honesty posture. `14_…` is the authoritative ruling.

**Verified vendor facts (evidence grades in `14_…` §2–3):**
- HubSpot Free exposes CRM API v3 via a scope-minimised Private App token — 100 req/10s, 250,000/day, `429 Retry-After`. **Webhook availability on Free is contested**, and workflow webhook actions require Operations/Data Hub Professional (~US$800/month). Free-tier limits conflict across sources by account cohort/region; the robust intersection is **1 pipeline, ≤10 custom properties, no real automation, HubSpot branding on forms/emails**.
- Retell AI is a real voice platform: ~US$0.07–0.31/min, **US$10 free credits** covering simulation testing + live test calls, transcripts/webhooks included, with SOC 2 Type II / HIPAA / GDPR / ISO 27001 claims. It also lists a **native HubSpot integration**.
- Retell's own FAQ: outbound dialling requires prior consent under TCPA, some jurisdictions require AI disclosure, and the FCC treats AI-generated voices in robocalls under existing restrictions. HK adds PDPO Cap.486 DPP1 notification before recording, UEMO/OFCA for AI outbound, PCPD 2021 AI ethics guidance (human oversight/accountability — non-binding but an enforcement lens), and HKMA/SFC GenAI guidance keeping senior management accountable for AI-assisted client communications. **This is legal commentary / secondary analysis, not legal advice**, and needs primary verification before any real call.

**Ratified decisions `E-9…E-16`:** `E-9…E-14` are the vendor-adapter decisions ratified on 6 Nov 2026; `E-15/E-16` are **post-Phase-B lead clarifications** on binding granularity and frozen filenames, ratified after the architecture and seed-pack passes and now written back into `14_…` §5 with an explicit precedence note.

| ID | Decision |
|---|---|
| E-9 | HubSpot Free sandbox portal = primary external CRM binding; 6 `crm.*` tables retained but re-purposed as `CRM ADAPTER · LOCAL PROJECTION`. **Amends E-4, does not delete it.** |
| E-10 | Four frozen honesty categories unchanged; qualifier **`REAL (SANDBOXED)`** added. A post-Approve sandbox write is permitted, declared on stage, and is **not** a "send". |
| E-11 | Additive `IF-A01` / `IF-A02`, three announced bindings each; **no new SVC IDs**; `IF-01…22` / `EV-01…20` not renumbered. |
| **E-12** | **Retell's native HubSpot integration MUST be OFF.** It would bypass the single-Approve C-3 gate — a workflow-level control gap, precisely the "formal governance principles vs operational practice" gap. Retell yields transcript + extraction candidates only. |
| E-13 | No inbound webhook dependency: outbound REST PATCH + **read-after-write GET verification**; `crm_sync_log` + `idempotency_key` handle retries; ≤10 custom properties; all orchestration stays in the workbench. |
| E-14 | Because Alan said "**may**", Retell is **optional and off the critical path**. Golden path must also run on `scripted_stub` / `retell_webhook_replay`. HARD-BLOCKED: real dialling, recording real persons, direct Retell→HubSpot writes. |
| **E-15** | **One call = one binding.** All 16 utterances of a run carry the **same** `adapter_binding`; the three bindings are **complete run variants**, never mid-call switches — because every switch needs `EV-A01` + C-4 and the `+00:10` chip is per-run (`12_` §7.4). The golden-path run is `scripted_stub` (vendor-independent); `retell_test` is an opt-in `S1-R` variant. **Ratified as a lead correction**: it supersedes an earlier instruction that permitted a mid-call split. |
| **E-16** | **Canonical filenames.** The frozen `<NN>_<schema>_<table>.<ext>` convention (`03` §7.4) binds the 8 frozen schemas' `file_fdw` tables and the G5 `EXCEPT` check. Legible sample filenames such as `clients.csv` are **display aliases**, neither additive nor replacements; a `canonical_filename_map` in `schema_contract.json` records the mapping. Additive `crm` / vendor files use the names in `manifest_addendum_crm.json`. No 51-file rename. |

**Contract freeze intact:** 8 schemas / 40 tables, `IF-01…22`, `EV-01…20`, `SVC-01…18`, `DF-01…06`, `NFR-1…18`, `ADR-01…08`, {TimescaleDB, `file_fdw`}, `manifest v1.3` / `schema v1.3` all unchanged. Additive only: `IF-A01/A02`, `EV-A01…06`, `NFR-A1…5`, `X-A1…7`, `D-H`, `DI-18…25`, `OQ-9…13`, E-9…E-16 — all architect-authored and synced to Phase 4 (`FU-01`, `FU-08`, `FU-17/18`, `FU-19…21`).

---

## 8. What is real, and what is not — the honesty contract

| Posture | What it covers |
|---|---|
| **REAL** | The `+00:00` live market tick (when `live` binding is licensed and cleared); Postgres; the workbench core; the generator mechanism |
| **REAL (SANDBOXED)** | HubSpot Free sandbox portal write-back after Approve — real vendor service, synthetic records, no real person contacted |
| **SIMULATED** | The entire seeded client world, scripted/test-call transcript, derived artefacts, replay ticks, the 6-node family graph |
| **STUBBED** | Meeting, appointment booking, email (draft only), demo sink, `local_stub` CRM fallback |
| **EXTERNAL** | Shariah project pointer — flag OFF, nothing on stage |
| **HARD-BLOCKED** | Trade execution (no table / endpoint / code path), real outbound dialling, direct Retell→HubSpot writes, auto-send |

**Measurable zero counters, verified in the seed pack:** `0 sends`, `0 trades`, `0 real dialled calls`, `0 real client-facing sends`, `0 real PII`, `0 real credentials` (placeholder `<HUBSPOT_PRIVATE_APP_TOKEN>` only), `0` email states other than `draft`, `0` trade/order files, `0` `succeeded` CRM writes before the 10:14:32 approval.

`SYNTHETIC DEMO DATA` is permanent to the last frame and not removable by config (G11). A statement with no C-1 envelope is suppressed as `insufficient evidence` and emits a C-4 event — never rendered as bare text (G1, FR-26).

---

## 9. Independent verification (team lead, on disk — not the writers' own reports)

| Check | Result |
|---|---|
| Four cross-file defects found before acceptance | `utt_07`→`utt_09`, missing `manifest_addendum_crm.json`, collapsed idempotency key, missing `client_id_uuid` — all fixed and re-verified |
| `12_…` | 1,253 lines / 14,664 words, 14 sections, 8 Mermaid blocks (parsed OK), 34 balanced fences, exactly 6 `crm` tables and 6 graph nodes, no `sent` state value, correct closing line |
| `13_…` / `demo_data/` | 57 files, 43 CSV / 1,277 rows / 12 JSON, all parse, **0 C-1 nulls**, **0 bad markers**, 0 width issues |
| Checksums | **52 / 52 real SHA-256 verified**; `dataset_checksum = sha256:22425b482b7d47522e41d43c69949ba01233453cea9d26b249c406cf23569dd3` identical in both manifests; `integrity_report.json` verdict **PASS**, 31 checks |
| Shape | 6 nodes / 8 edges / 8 docs / 5 node classes / 6 CRM tables / 2 family packs / exactly 1 signal |
| Entitlement | `ent_matrix_v1`; `Mr_Tan` all 6 nodes; `Next_gen` = `nd_01, nd_03, nd_04` only — **0 cross-node facts including hidden/draft jsonb** |
| Keys | `utt_09` @ `00:03:12` / `0.94`; six distinct `appr_001:fmv_20261105_1:map_0X` keys; `client_id_uuid` valid RFC-4122 v4, unique, 1:1 across `clients.csv` and `crm_contacts.csv` |
| Golden path | Wong holds `ins_syn_asean_eq_01`; tick 25.90→26.45; drift 5.88pp→6.12pp across 6.00pp; one `sig_0001`; `appr_001`; `corr_demo_0001`; `art_pl_v1/v2/v3` |
| No code | Zero `.py` / `.sh` / `.sql` / `.js` / `.ts` / `.parquet` artefacts under `deliverables/` |
| Determinism | Two runs from seed `20261105` → identical `dataset_checksum` |

**Two architect deviations were reviewed and ratified, not rubber-stamped:** (1) `client.client.client_id` is frozen as `uuid`, so `contact_id text` stays the projector key and a `client_id_uuid` column carries the real deferrable FK; (2) one immutable `appr_001` produces six accepted writes, so `mapping_id` must disambiguate the `UNIQUE` idempotency key or all six collapse into one effect. Both are additive physical clarifications with no frozen artefact changed.

---

## 10. What Alan must provide — the intake request

`11_…` §6 owns `DI-01…17` (format, minimum fields, volume, anonymisation, when needed, default synthetic stand-in, priority A/B/C). `14_…` §8 adds `DI-18…25`.

**Send first (Priority A, longest lead time / highest consequence):**

| ID | Item | Default if absent |
|---|---|---|
| `DI-01` | Which reading of "booking" applies | (i) appointment booking; (ii)/(iii) reference-only |
| `DI-02` | Live feed source + entitlement / written display / attribution clearance | `<source>` placeholder; `REPLAY — recorded 09:58` — **the only item that can collapse the headline claim** |
| `DI-03` | May any real client data (even anonymised) be used? | **No** — 100% synthetic |
| `DI-04` | Jurisdiction / currency / timezone / language | SGD / Singapore / SGT / English; HKD + USD minority |
| `DI-05` | Transcript content / consent wording | Synthetic scripted transcript |
| `DI-06` (+`DI-20`) | CRM field mapping incl. `hubspot_property`, `custom_property_slot` 1–10, `writable`, `version` | `map_01…map_08` synthetic |
| `DI-18` | HubSpot Free sandbox portal confirmation — cohort/region, Private App availability, ≤2 seats | Assume available; if not, run entirely on `local_stub` — **do not purchase** |
| `DI-19` | Private App token + scopes — **out of band only** | Placeholder `<HUBSPOT_PRIVATE_APP_TOKEN>` in ALL artefacts |
| `DI-22` | Retell go / no-go + agent config (prompt, voice, EN vs Cantonese, simulation suite) | Retell **OFF**, `scripted_stub` |
| `DI-24` | Consent / AI-disclosure wording and retention/residency for any real call | **No real calls** |
| `DI-25` | Confirm `0 real dialled calls` hard stop | **Yes**, enforced |

**Nice-to-have (B):** `DI-07…13`, `DI-17`, `DI-21` (HubSpot branding permission), `DI-23` (Retell webhook sample). **Deferrable (C):** `DI-14/15/16` (Shariah boundary detail, real screenshots/branding, real system schema echo).

**If Alan provides nothing, the demo still runs end-to-end** on generated synthetic data. The costs are honest and bounded: the `+00:00` tick cannot claim a licensed `LIVE` source, wording stays generic, no real-screen echo, "booking" shows appointments only, HubSpot/Retell run on offline bindings, and the Shariah beat stays a pointer. **None of these blocks the loop.**

**Resolved judgement calls (Alan — 6 Nov 2026):** `OQ-9` → **yes**, a real external write to the sandbox SaaS is acceptable on stage (post-Approve, declared `REAL (SANDBOXED)`); `OQ-11` → **default stands** (no HubSpot branding; user indifferent); `OQ-10` → Retell confirmed **optional** (deferred to MVP2, OFF in MVP1); **`OQ-1` → appointment/meeting booking (reading i)**; **`OQ-4` → multi-currency HKD/SGD/USD**; **`OQ-5` → family-graph range beat kept (FR-24)**. Full record in `14_…` §8.1 (round 1), §8.2 (round 2), §8.3 (round 3). `Q1`/`OD-1` resolved (Tiger Brokers paper-trading API as **data-only** live source — not named on stage, §8.3); `Q3` answered (**AI-generated demo data**, §8.3); `Q2` **ratified** (Postgres extensions TimescaleDB+`file_fdw`, §8.4); `OD-3/4/5/6/7/8` resolved in §8.2 (OD-3 **ratified** = no real client data / 100% synthetic, §8.4; OD-4 ElevenLabs now covers ASR via Speech-to-Text, §8.3). Retell `DI-23`/`DI-24` **in scope** (§8.3). Multi-currency seed amendment **confirmed** as the single remaining build-phase data task (§8.4). `OQ-2/3/6/7/8` resolved by earlier rulings (E-3, no-echo default, 6-node reconciliation, real-data "No", CRM sandbox).

---

## 11. Cost and go/no-go

**No paid tier is required or assumed — US$0.** HubSpot Free is free; Retell's US$10 signup credits cover building an agent, simulation testing and live test calls. Data/Operations Hub Professional (~US$800/month) is explicitly out of scope. The offline binding is mandatory because those credits are finite and vendor-dependent.

**Go/no-go before the leadership demo:** (1) sandbox portal reachable + Private App token valid; (2) ≤10-property mapping loaded; (3) read-after-write verification passes; (4) `local_stub` + `scripted_stub` offline rehearsal passes with reset ≤60s including sandbox re-seed by external ID; (5) native Retell→HubSpot integration confirmed OFF; (6) zero counters verified; (7) `SYNTHETIC DEMO DATA` visible to the last frame. **If 1–3 fail, run the entire demo on the offline bindings — the journey is unchanged, only the honesty chip changes.**

---

## 12. Next steps

1. **Review and ratify or override** `E-9…E-16` (remaining live items: `Q1/Q2/Q3`; `OQ-9` resolved yes, `OQ-11` default stands — both recorded in `14_…` §8.1).
2. **Send the Priority-A intake items** — `DI-02` has the longest lead time and is the only item that can collapse the `LIVE` headline claim; `DI-18/19/20/22/25` are now answered (demo-only, no purchase, token not a blocker, synthetic map, Retell→MVP2, webcall-only).
3. **Confirm the demo environment** — dual-output hardware (OD-6), Postgres 16 with TimescaleDB + `file_fdw`, and the HubSpot sandbox portal.
4. **Only then consider authorising a build.** `FU-01…24` are ready but executing any of them requires a new decision. **No code exists today.**

---

*Enhancement addendum assembled by Qi Huolin (Delivery Director), software-dev-team. All deliverables are in `deliverables/`. Design only — no application code, no executed DDL, no scaffold, no build commands, no vendor account opened, no credentials created.*

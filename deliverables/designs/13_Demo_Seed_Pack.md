# Demo Seed Pack — RM Workbench MVP (Leadership Journey Demo)

**Phase B deliverable (addendum) · Author:** seed-pack-author, software-dev-team
**Companion data:** `deliverables/demo_data/` (57 files)
**Consumer:** Qi Huolin (team lead) → Phase C assembly. Self-contained; the data files are the authoritative seeded world.
**Status:** **DESIGN ONLY.** No application code, no runnable generator, no scripts, no scaffold, no executed DDL, no credentials created, no vendor account opened. CSV/JSON sample rows are the *specified output shape* of a future generator (H2); they are **data**, allowed and expected.
**Conformance:** aligned to the ratified `12_Demo_Data_and_Systems_Architecture_Enhancement.md` (§2, §4.10 deviations 1 & 2, §5.2, §6, §7.4 one-call-one-binding, §9 per-run chip, §10.2 naming scope) and to `14_Vendor_Adapter_Ruling_HubSpot_Retell.md` (E-9…E-16 incl. the §5 E-15 / E-16 clarifications). `12_…`, `14_…`, `15_…` and `RM_Workbench_MVP_Design_Package.md` are authoritative and were **NOT edited**.
**Language:** English (per the addendum brief). Inline code/data identifiers are verbatim.

---

## 1. Purpose — why this pack exists

Alan, verbatim: *"i need to use a generator to generate some fake data to populate for a demo ... the firtst MVP should be demo to our company's leader aboutt he journey that we envision, so data is important"*.

The earlier package designed the generator as a **mechanism** (deterministic seed → flat files → one-transaction Postgres load → integrity validation → reset). It never made the *data* visible. This deliverable closes that gap: it is the **concrete seeded WORLD written as DATA FILES**, not another design of the generator. An executive can now click a chip and find a named client, a holding that genuinely drifts 6%, a tick with a wall-clock `as_of`, a brief whose every line resolves to a source, and a single human Approve that stops every outbound action.

The pack is deliberately **demo-scale** (E-6): 42 clients, 342 holdings, 48 instruments, a 120-frame replay excerpt, 6 graph nodes / 8 edges / 8 source docs, 6 CRM tables and 2 family packs — small enough to display and reset in ≤60s (NFR-9), large enough to be credible. It is **100% synthetic**, deterministic from one seed, C-1-complete on every fact row, FK-clean, and honest to the last frame.

---

## 2. What these files ARE — and are NOT (read this on stage)

> These files are the **SPECIFIED OUTPUT SHAPE of a future generator**. They are a static, labelled preview of the world that an `H2` generator will emit in `seed` / `replay` / `live` mode from one seed and the frozen `schema v1.3` / `manifest v1.3`. They are **NOT a running generator**, **NOT application code**, **NOT a scaffold**, **NOT executed DDL**, and **NOT a production migration**. No generator, script or executable is included anywhere under `deliverables/`. The generator that will one day emit them is explicitly *not a production migration tool* (`03_Technical_Solution.md` §7.10): it performs no schema evolution, no PII handling, no CDC, no upserts against live records. Computing SHA-256 hashes of the emitted files is a verification step only.

Everything is labelled `SYNTHETIC DEMO DATA`: a `README.md` header, a top-level `"synthetic_marker": "SYNTHETIC DEMO DATA"` in every JSON file, and a `synthetic_marker` column on every CSV row. No CSV contains comment lines — all files are machine-parseable. `manifest v1.3` is **READ-ONLY and MUST NOT be bumped**; the additive `crm.*` tables and vendor external-reference files are declared in a **separate architect-authored `manifest_addendum_crm.json`** (Phase-4 sync), never inside the frozen manifest (12_… §10.2 / §12.1). E-9…E-14 add no new Postgres table.

**Canonical filenames vs display aliases (E-16 / 12_… §10.2 "Naming scope").** The future generator emits the frozen `<NN>_<schema>_<table>.<ext>` canonical names (`03` §7.4) — that is what the `file_fdw` foreign tables and the G5 `EXCEPT` cross-view check bind to. The sample pack's legible names (`clients.csv`, `graph_nodes.csv`, …) are **display aliases**, not additive files and not replacements: `clients.csv` is the display alias of the frozen `client.client` table. `schema_contract.json → canonical_filename_map` records the mapping for all 51 manifest-v1.3 files, with `NN` taken verbatim from the recorded `load_order[].seq` (no number invented). Additive `crm.*` and vendor external-reference files use **exactly** the names declared in `manifest_addendum_crm.json`. No file is renamed and `manifest v1.3` stays FROZEN / `read_only` / `v1.3` / 51-file scope.

---

## 3. Binding seed registry (restated — cross-file consistency is mandatory)

| Item | Binding value |
|---|---|
| Seed | one numeric seed `20261105`; generator id `RM-WB-DEMO-v1.3`; `splitmix64` namespaced sub-seeds |
| World anchor | `world_as_of = 2026-11-05T17:00:00+08:00` (prior close, SGT) |
| Demo clock | live tick `2026-11-06 09:58:14 SGT`; single Approve `10:14:32 SGT` |
| Base | SGD / Singapore / SGT / English; minority HKD and USD |
| RM | `rm_sarah` → display `Sarah (RM)` |
| Primary client | `cl_wong_001` → synthetic HNWI "Wong" (matches the frozen line "Wong portfolio drifted 6% from target") |
| Secondary clients | `cl_lim_002` (F2 consent-declined variant), `cl_tan_003` (+00:20 family-graph range beat) |
| Drift instrument | `ins_syn_asean_eq_01`, invented symbol `SYN-ASEQ-01`, SGD; its tick breaches the 6% drift threshold |
| Instrument universe | `ins_syn_*` × 48; **no real issuer, bank or vendor name anywhere** |
| Market source | `<source>` versioned placeholder (OD-7/8); replay label `REPLAY — recorded 09:58`; **never a vendor** |
| CRM schema | EXACTLY 6 tables in a distinct `crm` schema: `crm.crm_contact`, `crm.crm_interaction`, `crm.crm_task`, `crm.crm_opportunity`, `crm.crm_field_mapping`, `crm.crm_sync_log` |
| CRM logical join key | `crm.crm_contact.contact_id` ↔ `client.client.client_id`; Wong row = `cl_wong_001` (text, projector-visible registry key used by **all** flat-file FKs) |
| CRM physical join key (12_… §4.10 deviation 1) | `clients.csv.client_id_uuid` and `crm_contacts.csv.client_id_uuid` hold the **same deterministic RFC-4122 UUID per client**, derived from `splitmix64(20261105, '<client_id>')`. This `uuid` column carries the `crm.crm_contact.client_id_uuid → client.client(client_id) DEFERRABLE INITIALLY DEFERRED` FK. `client_id` (text) stays the flat-file logical key; **no literal text→uuid FK is emitted**. Example: `cl_wong_001` → `0cabbbc6-0405-433a-a263-6fbaba4e5fa9` |
| CRM write-back | 8 versioned field mappings `map_01…map_08`; `field_mapping_version = fmv_20261105_1`; **literal registry rule** `idempotency_key = approval_token + field_mapping_version` (stored as text in `crm_field_mapping.csv`); **physical key** (12_… §4.10 deviation 2) `approval_token \|\| ':' \|\| field_mapping_version \|\| ':' \|\| mapping_id`, e.g. `appr_001:fmv_20261105_1:map_01`; `crm_sync_log` states `succeeded` / `pending` / `failed` |
| CRM row keys | `cri_01…cri_12` (interactions), `crt_01…crt_06` (tasks), `cro_01…cro_05` (opportunities), `map_01…map_08`, `sync_01…sync_08`, `pv_01…pv_08` |
| Booking | appointment booking only; `bk_01…bk_06`; readings (ii) trade/order and (iii) booking entity documented as **reference-only, NO tables, NO execution path** |
| Meeting | `evt_01…evt_06` (.ics-shaped, SGT); one Wong 10:00 meeting; ≥1 deliberately ambiguous attendee `att_amb_01` |
| Transcript | `utt_01…utt_16`, speaker-labelled, `timestamp_offset` HH:MM:SS, monotonic; **"daughter should join" fact = `utt_09` @ `00:03:12`, `confidence 0.94`** (12_… §7.4); **one call = one binding** — all 16 rows of the golden-path run carry `adapter_binding = scripted_stub` and the single per-run chip `STUB · declared (scripted transcript)` (E-15) |
| Adapter run variants (E-15) | voice bindings `retell_test` / `retell_webhook_replay` / `scripted_stub` are **complete run variants**, never mid-call switches (12_… §7.4 / E-15); `scenarios.json` = S1 `scripted_stub` (golden path) / S1-R `retell_test` (opt-in) / S2 `retell_webhook_replay` / S3–S4 `local_stub` + `scripted_stub`; `aud_12`/`aud_13` are BETWEEN-RUN rehearsal switches under `corr_rehearsal_0001` |
| Canonical filename map (E-16) | `schema_contract.json → canonical_filename_map` maps all 51 manifest-v1.3 files: 29 frozen-schema CSVs → `<NN>_<schema>_<table>.csv`, 4 frozen-schema JSONs → `<NN>_<schema>_<table>.json`, 18 additive crm/vendor files → their `manifest_addendum_crm.json` declared names; `NN` = `load_order[].seq` |
| Email | `thr_01…thr_04`, messages `msg_01…msg_04`; state `draft` ONLY — **no `sent` state exists**; `DEMO SINK — not delivered` |
| Graph | EXACTLY 6 nodes `nd_01…nd_06`; 8 edges `ed_01…ed_08`; 5 node classes; 8 directed edge types; source-doc refs `doc_01…doc_08` |
| Graph entitlement | two attendee classes `Mr_Tan` (entitled all 6 nodes) and `Next_gen` (entitled `nd_01, nd_03, nd_04` only); matrix `ent_matrix_v1`; packs `family_pack_mr_tan` + `family_pack_next_gen` differing EXACTLY on the entitlement boundary; 0 cross-node facts incl. hidden/draft jsonb |
| Artefacts | `priority_list` v1→v3, `meeting_brief` v1→v2, `post_meeting_review`, `family_pack` ×2; one immutable C-3 token `appr_001` — "Approved by Sarah (RM) · 10:14:32" |
| Workflow | one `correlation_id = corr_demo_0001` spanning tick → signal → brief → review → approval → re-rank |
| Synthetic marker | every row `synthetic_marker = 'SYNTHETIC DEMO DATA'`; C-1 envelope (`source_id, source_kind, as_of, ingested_at, confidence, mode, version_stamp`) non-null on every stored fact |
| Addendum | `manifest_addendum_crm.json` — **52nd file**, architect-authored, `manifest_version_not_bumped: true`, `phase4_sync: true`, `no_new_postgres_tables_from_vendor_adapters: true`; `manifest v1.3` stays FROZEN / `read_only` / `v1.3` with its 51-file frozen scope |
| Honesty | REAL (live tick) / REAL (SANDBOXED) (HubSpot Free) / SIMULATED (scripted transcript, seeded world) / STUBBED (CRM, meeting, booking, email demo sink) / EXTERNAL (Shariah project) / HARD-BLOCKED (trade execution). No `sent`, no `LIVE` while bound to replay, **0 sends, 0 trades, 0 real dialled calls, 0 real client-facing sends, 0 real PII** |

---

## 4. Full file inventory with row counts

`deliverables/demo_data/` — **57 files**: 51 hashed *data* files (43 CSV + 8 content JSON) + 6 *control artefacts*. All 51 data files are declared in `manifest_v1.3.json` `files[]` with a real SHA-256; `checksums.sha256` carries **52 lines** (51 data files + the addendum control-file verification line). Row counts exclude CSV headers.

### 4.1 Client / portfolio / market (data)

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `rm_books.csv` | csv | 1 | `client.rm_book` |
| `clients.csv` | csv | 42 | `client.client` |
| `accounts.csv` | csv | 65 | `client.account` |
| `instruments.csv` | csv | 48 | `market.instrument` |
| `holdings.csv` | csv | 342 | `client.holding` |
| `allocation_targets.csv` | csv | 325 | `client.allocation_target` |
| `products.csv` | csv | 24 | `client.product` |
| `interactions.csv` | csv | 14 | `client.interaction` |
| `consent_state.csv` | csv | 4 | `client.consent_state` |
| `suitability_state.csv` | csv | 6 | `client.suitability_state` |
| `market_ticks_live.csv` | csv | 1 | `market.market_tick` |
| `market_ticks_replay.csv` | csv | 120 | `market.market_tick` |
| `market_signals.csv` | csv | 1 | `market.market_signal` |
| `news_items.csv` | csv | 8 | `market.news_item` |
| `feed_status.csv` | csv | 2 | `demo_meta.feed_status` |

### 4.2 Memory / relationship graph (data)

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `memory_facts.csv` | csv | 19 | `graph.memory_fact` |
| `graph_nodes.csv` | csv | **6** | `graph.graph_node` |
| `graph_edges.csv` | csv | **8** | `graph.graph_edge` |
| `graph_source_docs.csv` | csv | 8 | `graph.source_doc` |
| `entitlement_matrix.csv` | csv | 12 | `graph.entitlement_rule` |
| `entitlement_decisions.csv` | csv | 6 | `graph.entitlement_decision` |
| `family_packs.json` | json | **2** | `artefact.artefact` |

### 4.3 CRM adapter · local projection (data) — EXACTLY 6 `crm.*` tables

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `crm_contacts.csv` | csv | 42 | `crm.crm_contact` |
| `crm_interactions.csv` | csv | 12 | `crm.crm_interaction` |
| `crm_tasks.csv` | csv | 6 | `crm.crm_task` |
| `crm_opportunities.csv` | csv | 5 | `crm.crm_opportunity` |
| `crm_field_mapping.csv` | csv | 8 | `crm.crm_field_mapping` |
| `crm_sync_log.csv` | csv | 8 | `crm.crm_sync_log` |
| `crm_old_new_preview.csv` | csv | 8 | `review.old_new_preview` *(review-surface artefact, **not** a 7th Postgres table)* |

### 4.4 Meeting / booking / email (data)

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `bookings.csv` | csv | 6 | `external.booking` |
| `meetings_calendar.csv` | csv | 6 | `external.calendar_event` |
| `meeting_attendees.csv` | csv | 14 | `external.meeting_attendee` |
| `transcript_utterances.csv` | csv | 16 | `external.transcript_utterance` |
| `extraction_items.csv` | csv | 6 | `artefact.extraction_item` |
| `email_threads.csv` | csv | 4 | `external.email_thread` |
| `email_messages.csv` | csv | 4 | `artefact.demo_sink_message` |
| `email_templates.json` | json | 3 | `external.email_template` |

### 4.5 Workflow / trust / control (data)

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `artefacts.json` | json | 8 | `artefact.artefact` |
| `approval_tokens.json` | json | 1 | `artefact.approval_token` |
| `workflow_instances.csv` | csv | 1 | `workflow.workflow_instance` |
| `workflow_stages.csv` | csv | 6 | `workflow.workflow_stage` |
| `audit_events.csv` | csv | 18 | `audit.audit_event` |
| `config_versions.csv` | csv | 20 | `demo_meta.config_version` |
| `version_registry.csv` | csv | 10 | `demo_meta.version_registry` |
| `scenarios.json` | json | 5 | `demo_meta.scenario` (S1…S4 + opt-in S1-R) |
| `demo_sink_messages.csv` | csv | 3 | `artefact.demo_sink_message` |

### 4.6 Vendor adapters (E-9…E-14) — data

| File | Fmt | Rows | Logical table |
|---|---|---|---|
| `hubspot_portal_seed.json` | json | 16 | `external.hubspot_portal` |
| `hubspot_api_exchange.json` | json | 5 | `external.hubspot_api_exchange` |
| `retell_call.json` | json | 16 | `external.retell_call` |
| `adapter_bindings.csv` | csv | 6 | `external.adapter_binding` |
| `vendor_health.csv` | csv | 6 | `external.vendor_health` |

### 4.7 Control artefacts

| File | Fmt | Row count | Purpose |
|---|---|---|---|
| `README.md` | md | n/a | synthetic banner + how to read the pack |
| `checksums.sha256` | sha256 | **52** | REAL SHA-256 of each of the 51 data files **plus** the 52nd line = `manifest_addendum_crm.json` (leading `#` banner is a comment) |
| `schema_contract.json` | json | **35 FK rules** | columns / types / FKs / `\N` null sentinel / deferred FKs / `uuid_resolution` / `idempotency_rule` / `load_order` / **`canonical_filename_map`** (E-16) |
| `integrity_report.json` | json | **34 checks** | PASS verdict with all checks run (incl. E-15 audit chain / one-call-one-binding and E-16 canonical map) |
| `manifest_v1.3.json` | json | 51 files | **READ-ONLY**; declares every frozen data file + table + row count + checksum |
| `manifest_addendum_crm.json` | json | 17 declared files | **52nd file**; architect-authored, Phase-4 sync; declares the 6 additive `crm.*` tables and all vendor external-reference files, explicitly **NOT inside `manifest_v1.3`** |

> **Volume note (E-6 / NFR-9).** `market_ticks_replay.csv` is a **representative 120-frame excerpt**; the full ~1,200-frame recorded stream is generator-emitted and is **NOT padded to a fake 1,200** here (`manifest.notes` records `full_stream_row_count = 1200`). Totals: 42 clients / 342 holdings / 48 instruments / 65 accounts / 6 nodes / 8 edges / 8 docs / 6 CRM tables / 2 family packs / 6 bookings / 6 events / 4 threads / 4 messages / 16 utterances — all inside the requested demo-scale bands.

---

## 5. C-1 column conventions

Every CSV begins with the **same eight leading columns**, in this exact order:

```
synthetic_marker, source_id, source_kind, as_of, ingested_at, confidence, mode, version_stamp
```

The last seven are the frozen C-1 provenance envelope from `03_Technical_Solution.md` §4.3. All seven are **non-null on every fact row** (verified: `0` nulls across **1,277 CSV rows**). `synthetic_marker = 'SYNTHETIC DEMO DATA'` is non-null on every row. Conventions:

| Column | Default (seeded fact) | Overrides used in this pack |
|---|---|---|
| `source_id` | `gen:20261105:<table>:<pk>` | live/replay ticks: `<source>:v1` (versioned placeholder, OD-7/8); F2 notes: `gen:20261105:rm_manual:<pk>` |
| `source_kind` | `seeded` | `live_feed` (live tick), `replay` (replay frames + F1 stale), `derived` (signal/workflow/audit/sync), `rm_manual` (F2 notes + config + consent) |
| `as_of` | `2026-11-05T17:00:00+08:00` (prior close) | event-time for live/derived rows; **original `feed_as_of` preserved** for replay frames |
| `ingested_at` | fixed generation wall-clock `2026-11-05T17:00:00+08:00` | equals event-time for live/derived rows. **Excluded from checksums** (DDR-25 AC-2) so two runs are byte-identical |
| `confidence` | `1.000` | `0.940` (`utt_09` daughter fact), `0.42`–`0.45` (F2 low-confidence notes) |
| `mode` | `seed` | `live` (live tick / signal / approval-loop rows), `replay` (replay frames + F1 stale) |
| `version_stamp` | `schema v1.3` | unchanged everywhere |

Enum domains (`source_kind`, `mode`) match the §4.3 `CREATE TYPE` definitions. Every JSON file carries a top-level `"synthetic_marker": "SYNTHETIC DEMO DATA"` (**12 JSON files**: 8 content + 4 control). CSV null sentinel is `\N` (declared in `schema_contract.json`); blank business fields are empty strings, never NULL in the envelope.

Two physical columns are additive clarifications, **not** changes to the frozen registry:
- `client_id_uuid` on `clients.csv` and `crm_contacts.csv` — deterministic RFC-4122 v4 UUID (§3, 12_… §4.10 deviation 1).
- `crm_field_mapping.csv` carries **both** `idempotency_key` (the literal registry rule `approval_token + field_mapping_version`) and `physical_idempotency_key` / `idempotency_rule` (the deviation-2 physical form). `crm_sync_log.csv` and `crm_old_new_preview.csv` carry the concrete `idempotency_key` per write, plus `field_mapping_version = fmv_20261105_1`. `crm_old_new_preview.csv` additionally carries `evidence_ref` / `evidence_offset` so the daughter fact is evidence-linked (`utt_09` @ `00:03:12`).

---

## 6. FK map (deterministic, parent-derived, FK-clean)

All FKs are parent-derived: child keys are built from the parent's stable key, so referential integrity holds by construction and the generator never "invents a parent row" (X-20). `schema_contract.json` declares **35 FK rules** (including the `client_id_uuid` uuid-resolution rule) and a `uuid_resolution` block; `integrity_report.json` reports **0 orphans across 1,828 references checked**.

| Child file · column | Parent file · key |
|---|---|
| `clients.rm_book_id` | `rm_books.rm_book_id` |
| `accounts.client_id` | `clients.client_id` |
| `holdings.account_id` / `.client_id` / `.instrument_id` | `accounts.account_id` / `clients.client_id` / `instruments.instrument_id` |
| `allocation_targets.account_id` | `accounts.account_id` |
| `market_ticks_live.instrument_id`, `market_ticks_replay.instrument_id`, `news_items.instrument_id` | `instruments.instrument_id` |
| `market_signals.tick_key` | `market_ticks_live.tick_key` (logical FK, §7.5) |
| `memory_facts.client_id`, `crm_contacts.client_id`, `bookings.client_id`, `meetings_calendar.client_id`, `email_threads.client_id`, `consent_state.client_id`, `suitability_state.client_id`, `interactions.client_id` | `clients.client_id` |
| **`crm_contacts.client_id_uuid`** | **`clients.client_id_uuid`** (physical uuid FK; 1:1, valid uuid, unique per client) |
| `graph_edges.from_node_id` / `.to_node_id` | `graph_nodes.node_id` |
| `graph_edges.source_doc_id`, `graph_nodes.source_doc_id` | `graph_source_docs.doc_id` |
| `entitlement_matrix.node_id`, `entitlement_decisions.requested_node_id` | `graph_nodes.node_id` |
| `crm_interactions.contact_id`, `crm_tasks.contact_id`, `crm_opportunities.contact_id`, `crm_old_new_preview.contact_id` | `crm_contacts.contact_id` (= `client_id`) |
| `crm_sync_log.mapping_id`, `crm_old_new_preview.mapping_id` | `crm_field_mapping.mapping_id` |
| `bookings.event_id`, `meeting_attendees.event_id`, `transcript_utterances.event_id` | `meetings_calendar.event_id` |
| `extraction_items.utterance_id` | `transcript_utterances.utterance_id` |
| `email_messages.thread_id` | `email_threads.thread_id` |
| `workflow_stages.workflow_id` | `workflow_instances.workflow_id` |

Loose (declared, non-strict) references: `market_signals.correlation_id`, `workflow_stages.correlation_id`, `audit_events.correlation_id`, `crm_sync_log.request_payload_ref` / `verification_get_ref` → `hubspot_api_exchange.json`, `memory_facts.evidence_ref` → `transcript_utterances.utterance_id` (only where non-empty), `demo_sink_messages.message_ref` → `email_messages.message_id`. Golden-path link: **`corr_demo_0001`** ties tick → signal → brief → review → approval → re-rank.

### 6.1 Load order / `<NN>_<schema>_<table>.<ext>` emission order

`12_…` §10.2 fixes the FK-safe emission order via `<NN>` sequence prefixes. The full 51-step ordered list is declared in `manifest_addendum_crm.json` → `load_order[]` (and in `schema_contract.json` → `load_order`). In brief:

`demo_meta.version_registry` / `config_version` / `scenario` → `market.instrument` → `client.client` + `rm_book` → `graph.graph_node` / `graph_edge` / `source_doc` / `entitlement_rule` / `entitlement_decision` → `client.account` → `client.holding` → `allocation_target` → `graph.memory_fact` → `client.interaction` / `consent_state` / `suitability_state` / `product` → **the six `crm.*` tables** (`crm_contact` → `crm_interaction` → `crm_task` → `crm_opportunity` → `crm_field_mapping` → `crm_sync_log`) → `review.old_new_preview` → `market.news_item` → `market.market_tick` (live + replay) → `market.market_signal` / `feed_status` → `artefact.*` / `workflow.*` / `audit.*` → the external-reference files (booking / event / attendee / utterance / extraction / thread / message / email template / HubSpot / Retell / adapter / vendor-health / sink totals) → manifest & control files last. The emitted filenames here are the short `<table>.<ext>` **display aliases**; the `<NN>_<schema>_<table>.<ext>` canonical sequence is the **specified generator naming** that the `file_fdw` foreign tables and the G5 `EXCEPT` check bind to (`03` §7.4 / 12_… §10.2 / E-16). `schema_contract.json → canonical_filename_map` records the exact mapping for all 51 manifest-v1.3 files, with `NN` taken verbatim from `load_order[].seq`; additive `crm` / vendor files keep the names declared in `manifest_addendum_crm.json`. No file is renamed and `manifest v1.3` is not bumped.

---

## 7. Beat → exact row key map (SAME beats as Phase A §2)

Row keys are literal values present in the emitted files.

| Beat | Exact row keys in this pack | Source chip that renders |
|---|---|---|
| **−00:30** pre-flight | `scenarios.json` S1–S4 (+ opt-in S1-R); `manifest_v1.3.json`; `manifest_addendum_crm.json`; `integrity_report.json`; `version_registry.csv` `vr_01…vr_10`; `config_versions.csv` `cfg_01…cfg_20`; `adapter_bindings.csv` `IF-A01` / `IF-A02`; `vendor_health.csv` `vh_03`; `demo_sink_messages.csv` `ds_03` | `READY · LIVE · integrity verified · SYNTHETIC DEMO DATA · manifest v1.3 · checksum acc91f0c…` |
| **+00:00** real tick | `market_ticks_live.csv` `tk_live_0001`; `instruments.csv` `ins_syn_asean_eq_01`; `feed_status.csv` `fs_000` | `MARKET EVENT · SYN-ASEQ-01 · <source> · as-of 09:58:14 SGT` + `LIVE` |
| **+00:02** signal | `market_signals.csv` `sig_0001` (**exactly one**); `holdings.csv` `hd_0001…hd_0008` (Wong `acc_001`); `allocation_targets.csv` `tg_0001…tg_0005`; `config_versions.csv` `cfg_01` (6.00) | `Wong portfolio drifted 6% from target · Risk/Opportunity · tick as-of 09:58:14 · rule-pack v1` |
| **+00:04** workflow | `workflow_instances.csv` `wf_0001`; `workflow_stages.csv` `ws_01…ws_06`; `memory_facts.csv` `mf_001…mf_018` | `context reused from D5 · fact mf_001 · as-of prior close` |
| **+00:06** My Day re-rank | `artefacts.json` `art_pl_v1 → art_pl_v2`; `clients.csv` (42 rows, ≤10 rendered); `market_signals.csv` `sig_0001`; `config_versions.csv` `cfg_05` | `Opportunity — rebalancing · as-of 09:58:14 · ↑3 (from 4)` |
| **+00:08** five-section brief | `artefacts.json` `art_brief_v1`; `accounts.csv` `acc_001…acc_003`; `holdings.csv` Wong rows; `interactions.csv` `int_01…int_04`; `news_items.csv` `nw_01`, `nw_02` (`nw_07` excluded — unlicensed); `memory_facts.csv` `mf_001…`; `market_signals.csv` `sig_0001` | `Portfolio, as of prior close` / `Client preference, verified` / `Market · <source> · as-of …` |
| **+00:10** consent + capture | `consent_state.csv` `consent_wong_01`; `transcript_utterances.csv` `utt_01…utt_16` (**`utt_09` at `00:03:12`**, `scripted_stub` 16/16); `extraction_items.csv` `ex_01…ex_06`; `memory_facts.csv` `mf_001`; `retell_call.json`; `scenarios.json` S1 / S1-R; `adapter_bindings.csv` `IF-A02` / `scripted_stub` | `STUB · declared (scripted transcript)` for the S1 golden-path run (default); `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)` for the opt-in S1-R whole-run variant. **Per-run, binding-dependent — one chip per run (12_… §9 / E-15)** |
| **+00:14** one review | `artefacts.json` `art_review_v1`; `crm_old_new_preview.csv` `pv_01…pv_08`; `crm_contacts.csv` `cl_wong_001`; `email_messages.csv` `msg_02` (`draft`); `products.csv` `prod_01`; `suitability_state.csv` `su_01`; `artefacts.json` `art_pl_v3` | `ticket · suitability current · execution disabled` / `CRM old → new` |
| **+00:16** single Approve | `approval_tokens.json` `appr_001`; `crm_sync_log.csv` `sync_01…sync_08`; `email_messages.csv` `msg_02` (`draft`); `audit_events.csv` `aud_08/09/10`; `demo_sink_messages.csv` `ds_01` | `Approved by Sarah (RM) · 10:14:32 · CRM write-back → sandbox portal succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades, 0 real dialled calls` |
| **+00:18** loop closes | `artefacts.json` `art_pl_v3` + `art_brief_v2`; `memory_facts.csv` `mf_001` (canonical); `workflow_stages.csv` `ws_06`; `email_messages.csv` `msg_02` | `Client preference, verified · approved 10:14:32` |
| **+00:20** range beat | `graph_nodes.csv` `nd_01…nd_06`; `graph_edges.csv` `ed_01…ed_08`; `graph_source_docs.csv` `doc_01…doc_08`; `entitlement_matrix.csv` `em_01…em_12`; `entitlement_decisions.csv` `dec_01…dec_06`; `family_packs.json` (2); `clients.csv` `cl_tan_003` (flag-OFF Shariah pointer) | `Trust deed, reviewed by Sarah · pack v_n · ent_matrix_v1 · as-of …` |
| **End** card | honesty chrome only — `demo_sink_messages.csv` `ds_03` | `SYNTHETIC DEMO DATA · DEMO SINK — not delivered · ModeChip` |
| **F1** feed outage (+00:03) | `feed_status.csv` `fs_001` (`STALE`, age `47s`, **no new tick**); `market_ticks_replay.csv` `tk_rp_0001…tk_rp_0120`; `vendor_health.csv` `vh_02`; `audit_events.csv` `aud_11` | `FEED STALE · last tick 09:58:14 · age 47s` → `REPLAY — recorded 09:58` |
| **F2** consent declined (+00:10) | `consent_state.csv` `consent_lim_01`, `consent_wong_02`; `memory_facts.csv` `mf_013…mf_016` (`rm_manual`, low confidence, **no transcript-derived facts**); `adapter_bindings.csv` `IF-A02` / `scripted_stub` | `rm_manual · low-confidence · review required` / `STUB · declared` |

> **The +00:10 chip is per-run and binding-dependent (12_… §9 / E-15).** One call = one binding: all 16 utterances of a run carry the same `adapter_binding`, so exactly **one** chip renders for the whole beat. The three voice bindings are **complete run variants** — `S1` `scripted_stub` (golden path, `STUB · declared (scripted transcript)`), `S1-R` `retell_test` (opt-in, `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)`), `S2` `retell_webhook_replay` — never mid-call switches. `aud_12` / `aud_13` are announced **BETWEEN-RUN** operator switches during rehearsal under `corr_rehearsal_0001`, not switches inside `corr_demo_0001`.

---

## 8. Inline preview of the most important rows

Verbatim excerpts of the core golden-path rows (full C-1 envelope retained). Wide-table rows are shown as compact projections of their business columns; the complete rows live in `demo_data/`.

**`clients.csv` — primary client (logical text key + physical uuid key)**
```
SYNTHETIC DEMO DATA,gen:20261105:client.client:cl_wong_001,seeded,2026-11-05T17:00:00+08:00,2026-11-05T17:00:00+08:00,1.000,seed,schema v1.3,cl_wong_001,0cabbbc6-0405-433a-a263-6fbaba4e5fa9,Wong Kah Mun,HNWI,Tier A,Singapore,SGD,28500000,false,accept,false,rb_001,hs_ct_001,wong@demo.invalid,fabricated name string — no real individual referenced
```

**`crm_contacts.csv` — same `client_id_uuid`, 1:1 physical FK**
```
SYNTHETIC DEMO DATA,gen:20261105:crm.crm_contact:cl_wong_001,seeded,2026-11-05T17:00:00+08:00,2026-11-05T17:00:00+08:00,1.000,seed,schema v1.3,cl_wong_001,cl_wong_001,0cabbbc6-0405-433a-a263-6fbaba4e5fa9,hs_ct_001,Wong Kah Mun,wong@demo.invalid,HNWI,SGD,rm_sarah,Quarterly call,phone,Balanced,2027-02-05,Q3 portfolio review,not recorded,rm_sarah,true,contacts,HUBSPOT FREE · DEMO SANDBOX PORTAL,CRM ADAPTER · LOCAL PROJECTION
```

**`instruments.csv` — drift instrument (no real issuer)**
```
SYNTHETIC DEMO DATA,gen:20261105:market.instrument:ins_syn_asean_eq_01,seeded,2026-11-05T17:00:00+08:00,2026-11-05T17:00:00+08:00,1.000,seed,schema v1.3,ins_syn_asean_eq_01,SYN-ASEQ-01,Synthetic ASEAN Equity Basket 01,Equity,SGD,units,synthetic-demo-ok,symmap_v1,SYNTHETIC ISSUER · no real issuer named
```

**`holdings.csv` — Wong holds the drift instrument**
```
SYNTHETIC DEMO DATA,gen:20261105:client.holding:hd_0001,seeded,2026-11-05T17:00:00+08:00,2026-11-05T17:00:00+08:00,1.000,seed,schema v1.3,hd_0001,acc_001,cl_wong_001,ins_syn_asean_eq_01,Equity,200000,25.90,5180000,SGD,0,0.200,0.2590,DRIFT INSTRUMENT — golden path
```

**`market_ticks_live.csv` — the ONE live tick (09:58:14 SGT)**
```
SYNTHETIC DEMO DATA,<source>:v1,live_feed,2026-11-06T09:58:14+08:00,2026-11-06T09:58:14+08:00,1.000,live,schema v1.3,tk_live_0001,ins_syn_asean_eq_01,SYN-ASEQ-01,26.45,SGD,25.90,2.124,2026-11-06T09:58:14+08:00,2026-11-06T09:58:14+08:00,synthetic-demo-ok,<source> (versioned placeholder · OD-7/8 · no vendor named),corr_demo_0001,MARKET EVENT · SYN-ASEQ-01 · <source> · as-of 09:58:14 SGT
```

**`market_signals.csv` — EXACTLY ONE signal, 6% rule-pack v1 (drift literally computable)**
```
SYNTHETIC DEMO DATA,gen:20261105:market.market_signal:sig_0001,derived,2026-11-06T09:58:14+08:00,2026-11-06T09:58:16+08:00,1.000,live,schema v1.3,sig_0001,portfolio_drift,cl_wong_001,acc_001,ins_syn_asean_eq_01,tk_live_0001,5.88,6.12,6.00,rule-pack v1,max_class_weight_deviation_pp,EQ sleeve max-class-weight-deviation: before tick (11176000/20000000 - 0.50)*100 = 5.88pp; live tick SYN-ASEQ-01 price 25.90->26.45 on 200000 units adds delta=110000; after tick (11286000/20110000 - 0.50)*100 = 6.12pp; crosses 6.00pp threshold once,corr_demo_0001,Wong portfolio drifted 6% from target · Risk/Opportunity · tick as-of 09:58:14 · rule-pack v1,2026-11-06T09:58:14+08:00
```
> Drift is genuinely computable from `holdings.csv` + the tick: Wong `acc_001` total = 20,000,000 SGD; Equity sleeve target 0.50; prior-close EQ = 11,176,000 → 5.88pp; the +2.124% tick on 200,000 units adds Δ = 110,000 → 6.12pp, crossing the 6.00pp threshold **once**. `allocation_targets.csv` `tg_0001…tg_0005` carries the same class weights (0.500/0.300/0.100/0.070/0.030, sum 1.000).

**`transcript_utterances.csv` — `utt_09` @ `00:03:12` / `confidence 0.94` (the daughter fact)**
```
SYNTHETIC DEMO DATA,gen:20261105:external.transcript_utterance:utt_09,derived,2026-11-06T10:00:00+08:00,2026-11-06T10:00:00+08:00,0.940,seed,schema v1.3,utt_09,evt_01,scripted_stub,Wong (client),client,00:03:12,I think my daughter should join the next review meeting.,0.94,STUB · declared (scripted transcript via test call),STUB · declared (scripted transcript)
```
All 16 `source_id` values match their row ID (`gen:20261105:external.transcript_utterance:utt_NN`); offsets increase monotonically `00:00:05 … 00:06:35`; **all 16 rows carry `adapter_binding = scripted_stub` and the single per-run `source_chip = STUB · declared (scripted transcript)`** (one call = one binding, E-15 / 12_… §7.4). Per the E-15 scoping ("only the `adapter_binding` column changes" plus the per-row `source_chip`), utterance text, offsets, `stub_declaration` and `mode` were deliberately left unchanged. The other two bindings are evidenced as **complete run variants** in `scenarios.json` (S1-R / S2), `adapter_bindings.csv` and `retell_call.json`, not as slices of this call.

**`memory_facts.csv` — `mf_001`, the daughter fact (confidence 0.94, linked to `utt_09`)**
```
SYNTHETIC DEMO DATA,gen:20261105:graph.memory_fact:mf_001,derived,2026-11-06T10:14:32+08:00,2026-11-06T10:14:32+08:00,0.940,live,schema v1.3,mf_001,cl_wong_001,family_preference,next review meeting,Family: daughter should join the next review meeting · preference noted,0.94,utt_09,00:03:12,approved,false,,corr_demo_0001,
```

**`approval_tokens.json` — ONE immutable C-3 token**
```json
{
  "token_id": "appr_001",
  "approver_display": "Sarah (RM)",
  "approved_at": "2026-11-06T10:14:32+08:00",
  "label": "Approved by Sarah (RM) · 10:14:32",
  "field_mapping_version": "fmv_20261105_1",
  "immutable": true,
  "correlation_id": "corr_demo_0001"
}
```

**`graph_nodes.csv` — EXACTLY 6 nodes (5 classes), ratified §6.1 keys**
```
nd_01,person,Patriarch,Tan_WL,doc_01,OFF,shariah_project_ext
nd_02,person,Next-gen family member,Tan_ML,doc_02,false
nd_03,trust,Family trust,Trust_WL,doc_03,false
nd_04,holding_entity,Holding company,SPV_SYN_01,doc_04,false
nd_05,advisor,Relationship manager,rm_sarah,doc_05,false
nd_06,account,Custody account,acc_syn_sgd_01,doc_06,false
```
**`graph_edges.csv` — 8 edges, 8 distinct directed types** (`settlor_of`, `beneficiary_of`, `owns`, `holds`, `advises`, `successor_of`, `signatory_of`, `beneficial_interest_in`), e.g. `ed_01,settlor_of,nd_01,nd_03,…` / `ed_02,beneficiary_of,nd_02,nd_03,…`. `nd_01` carries the Shariah `preference-flag` pointer (`shariah_preference_flag=OFF`, `external_project_ref=shariah_project_ext`) with zero screening / zakat / SSB data.

**`crm_field_mapping.csv` — literal registry rule + physical disambiguator (`fmv_20261105_1`)**
```
map_01 … version=fmv_20261105_1 | idempotency_key="approval_token + field_mapping_version" | physical_idempotency_key="appr_001:fmv_20261105_1:map_01" | idempotency_rule="approval_token || ':' || field_mapping_version || ':' || mapping_id"
```

**`crm_sync_log.csv` — `succeeded` only AFTER 10:14:32; 429 retry; pre-Approve failure; six distinct physical keys**
```
sync_01,map_01,cl_wong_001,appr_001,fmv_20261105_1,appr_001:fmv_20261105_1:map_01,hubspot_free,accepted,succeeded,200,2026-11-06T10:14:33+08:00
sync_06,map_06,cl_wong_001,appr_001,fmv_20261105_1,appr_001:fmv_20261105_1:map_06,hubspot_free,accepted,succeeded,200,2026-11-06T10:14:38+08:00
sync_07,map_07,cl_wong_001,appr_001,fmv_20261105_1,appr_001:fmv_20261105_1:map_07,hubspot_free,pending,429,2026-11-06T10:14:39+08:00 (429 Retry-After)
sync_08,map_08,cl_wong_001,appr_001,fmv_20261105_1,appr_001:fmv_20261105_1:map_08,demo_sink,failed,writable=false
```

**`crm_old_new_preview.csv` — old → new (12_… §5.2 exact values), `utt_09` evidence**
```
pv_01,next_meeting_preference,Quarterly call -> Quarterly review with daughter present,accepted,utt_09 @ 00:03:12
pv_06,family_attendee_preference,not recorded -> Daughter to join,accepted,utt_09 @ 00:03:12
pv_07,task_owner,rm_sarah -> rm_sarah,rejected — unchanged
pv_08,email_consent,true -> true,rejected — unchanged (FR-16 AC-4; consent never inferred)
```

**`demo_sink_messages.csv` — the zero counters**
```
ds_03,TOTAL,all,n/a,0,0,0,0,0,0,false,0 sends · 0 trades · 0 real dialled calls · 0 real client-facing sends · 0 real PII,2026-11-06T10:30:00+08:00
```

**`feed_status.csv` — F1 stale row at age 47s, no new tick**
```
fs_001,2026-11-06T09:59:01+08:00,STALE,tk_live_0001,2026-11-06T09:58:14+08:00,47,30,120,REPLAY — recorded 09:58,FEED STALE · last tick 09:58:14 · age 47s
```

**`email_messages.csv` — `draft` ONLY (`@demo.invalid` addresses); `msg_02` is the review draft**
```
msg_01,thr_01,sarah@demo.invalid,wong@demo.invalid,Q3 review notes,Synthetic Q3 review notes · every fact evidence-linked,outbound,draft,DEMO SINK — not delivered,tpl_v1,disc_v1,2026-11-05T17:00:00+08:00
msg_02,thr_02,sarah@demo.invalid,wong@demo.invalid,Follow-up after 6 Nov review,Synthetic follow-up draft · daughter to join next review,outbound,draft,DEMO SINK — not delivered,tpl_v2,disc_v1,2026-11-06T10:14:32+08:00
```

---

## 9. The two entitled family pack views + leakage statement

`family_packs.json` holds two `approved` (C-3) packs stamped `ent_matrix_v1`, `approval_token_ref = appr_001`, `corr_demo_0001` and `as_of 2026-11-06T10:20:10+08:00`:

| Pack | Attendee class | Entitled nodes | Visible facts / edges |
|---|---|---|---|
| `family_pack_mr_tan` | `Mr_Tan` | `nd_01, nd_02, nd_03, nd_04, nd_05, nd_06` (all 6) | 6 node facts + all 8 internal edges `ed_01…ed_08` + `doc_01…doc_08` |
| `family_pack_next_gen` | `Next_gen` | `nd_01, nd_03, nd_04` only | 3 node facts + edges fully inside the entitled set (`ed_01`, `ed_03`) + `doc_01`, `doc_03`, `doc_04` |

**They differ EXACTLY on the entitlement boundary.** A diff that includes the `hidden_jsonb` and `draft_jsonb` text returns **`0 cross-node facts`** (`diff_result.diff_cross_node_facts_including_hidden_draft_jsonb = 0`); each pack's `leakage_check` reports `cross_node_facts: 0, incl_hidden_draft_jsonb: 0`. The suppressed nodes (`nd_02` next-gen person, `nd_05` advisor, `nd_06` account), the six suppressed edges and `doc_02/05/06/07/08` are absent from the Next-gen pack in both visible and hidden/draft jsonb. Note (12_… §6.2): `Next_gen` is entitled only to `nd_01, nd_03, nd_04`; a person node (`nd_02`) can therefore be hidden from the class that names it — entitlement is a **matrix decision**, not an identity inference.

Enforcement is in **context assembly, not UI** (FR-06 / X-11): `entitlement_matrix.csv` (`ent_matrix_v1`) is the single source of truth. A direct unentitled read (`Next_gen` → `nd_02` / `nd_05`) is **denied** and logged (`entitlement_decisions.csv` `dec_05`, `dec_06` → `audit_events.csv` `aud_14`, C-4). `graph_nodes.csv` `nd_01` carries only a Shariah `preference-flag` pointer (`OFF`, `external_ref=shariah_project_ext`) with **zero** screening / zakat / SSB data (DDR-14, E-3).

---

## 10. External vendor adapters (E-9…E-14)

**Authoritative ruling:** `deliverables/14_Vendor_Adapter_Ruling_HubSpot_Retell.md` (read in full). It amends E-4 and supersedes OQ-8; E-1, E-2, E-3, E-5, E-6, E-7, E-8 remain in force. Trigger (Alan, verbatim): *"for CRM, i plan to use hubspot free as the demo, i may use retell.ai as an agent , please plan this in"*.

- **E-9** — HubSpot Free is the **primary external CRM binding**, in a dedicated free sandbox portal with 100% synthetic records. The 6 `crm.*` tables are **retained but re-purposed** as `CRM ADAPTER · LOCAL PROJECTION` (local projection + field mapping + idempotency/outbox ledger), **NOT the CRM itself**. Labels: external `HUBSPOT FREE · DEMO SANDBOX PORTAL`; internal `CRM ADAPTER · LOCAL PROJECTION (6 tables)`.
- **E-10** — four frozen honesty categories kept; add qualifier **`REAL (SANDBOXED)`** = real vendor service + synthetic records + no real person contacted. New counters: **0 real dialled calls / 0 real client-facing sends / 0 real PII**. A post-Approve sandbox CRM write is permitted, declared on stage, and is **not** a "send".
- **E-11** — additive `IF-A01` (CRM adapter) / `IF-A02` (voice adapter), three announced bindings each: CRM `hubspot_free → local_stub → demo_sink`; Voice `retell_test → retell_webhook_replay → scripted_stub`. `IF-01…22` / `EV-01…20` are **NOT renumbered**; every switch is announced + C-4 (`aud_12`, `aud_13`). `adapter_bindings.csv` rows carry `adapter_id = IF-A01` / `IF-A02`.
- **E-12** — Retell's **native HubSpot integration MUST be OFF** (`config_versions.csv` `cfg_17 = OFF`). Retell yields only transcript + extraction candidates; every write follows `appr_001`.
- **E-13** — **no inbound HubSpot webhooks** (`cfg_18 = false`); outbound REST + **read-after-write GET verification** (`hubspot_api_exchange.json`), `429 Retry-After` (`sync_07`, `vh_05`), physical `idempotency_key = appr_001:fmv_20261105_1:map_01` (deviation 2), **≤10 custom properties** (8 used, slots 1–8), 100 req/10s and 250,000/day limits (`cfg_12`, `cfg_13`).
- **E-14** — Retell is **OPTIONAL / off the critical path** ("may"). Default transcript = Retell simulation/test call with a **synthetic caller**; golden path also runs on `scripted_stub` / `retell_webhook_replay` (S3/S4). HARD-BLOCKED: real outbound dialling, recording real persons, direct Retell→HubSpot writes.

### 10.1 HubSpot object ↔ `crm` table mapping (14 §6.1)

| Local `crm` table (retained) | HubSpot object | Direction | Seed-pack evidence |
|---|---|---|---|
| `crm.crm_contact` | `contacts` | in (projection) / out (write-back) | `crm_contacts.csv` `cl_wong_001` ↔ `hubspot_portal_seed.json` `hs_ct_001`; `@demo.invalid` emails |
| `crm.crm_interaction` | activities `notes` / `calls` / `emails` / `meetings` | in | `crm_interactions.csv` (12 rows, `cri_01…cri_12`) |
| `crm.crm_task` | `tasks` | in / out | `crm_tasks.csv` (`crt_01…crt_06`); `hubspot_portal_seed.json` post-Approve task |
| `crm.crm_opportunity` | `deals` (single pipeline) | in | `crm_opportunities.csv` (`cro_01…cro_05`) |
| `crm.crm_field_mapping` | **local only** | — | `crm_field_mapping.csv` `map_01…map_08`, `fmv_20261105_1`, slots 1–8 |
| `crm.crm_sync_log` | **local only** | — | `crm_sync_log.csv` `sync_01…sync_08`, `adapter_binding`, `http_status`, `retry_after_ms` |

**Canonical filenames (E-16).** `schema_contract.json → canonical_filename_map` maps each of the 51 files declared by READ-ONLY `manifest v1.3` to its canonical `<NN>_<schema>_<table>.<ext>` emission name (`03` §7.4), with `NN` taken verbatim from `manifest_addendum_crm.json.load_order[].seq` — no number is invented. The 8 frozen schemas are `demo_meta`, `market`, `client`, `graph`, `workflow`, `artefact`, `audit`, `staging` (`03` §4.1). 29 frozen-schema CSVs map to `<NN>_<schema>_<table>.csv`, 4 frozen-schema JSONs to their `.json` form, and the 18 additive `crm.*` / vendor external-reference files keep **exactly** the names declared in `manifest_addendum_crm.json`. Legible sample-pack names are **display aliases**; the future generator emits the canonical names so the `file_fdw` `EXCEPT` / G5 check has a real path to read. **No file is renamed and `manifest v1.3` is NOT bumped.**

### 10.2 No new Postgres table (contract-freeze statement)

> HubSpot Free and Retell AI are **EXTERNAL REFERENCES**. **No new Postgres table was added.** The frozen 8 schemas / 40 tables, `IF-01…22`, `EV-01…20`, `SVC-01…18`, `DF-01…06`, `NFR-1…18`, `ADR-01…08`, extension set `{TimescaleDB, file_fdw}`, `schema v1.3` and **`manifest v1.3` (NOT bumped)** are unchanged. `crm_old_new_preview.csv` is a review-surface artefact, **not** a 7th table. `manifest_v1.3.json` carries `frozen: true, read_only: true` and `no_new_postgres_tables_from_vendor_adapters: true`; `schema_contract.json` and `manifest_addendum_crm.json` repeat the same declaration.

### 10.3 Binding → beat chip mapping (exact chips from 14 §6.4 / 12_… §9)

| Beat | Binding(s) | Exact chip text |
|---|---|---|
| **+00:00** | market feed (`<source>`) | `MARKET EVENT · SYN-ASEQ-01 · <source> · as-of 09:58:14 SGT` + `LIVE` |
| **+00:10** | `scripted_stub` (S1 golden-path run, default) | `STUB · declared (scripted transcript)` |
| **+00:10** | `retell_test` (S1-R opt-in whole-run variant) | `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)` |
| **+00:10** | `retell_webhook_replay` (S2 complete run variant) | `STUB · declared (scripted transcript)` |
| **+00:16** | `hubspot_free` (post-Approve write) | `Approved by Sarah (RM) · 10:14:32 · CRM write-back → sandbox portal succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades, 0 real dialled calls` |

`Family: daughter added …` and `confidence 0.94` at `00:03:12` are unchanged. **One call = one binding (E-15 / 12_… §7.4):** all 16 utterances of the golden-path run are `scripted_stub`, and `source_chip` declares the single per-run chip `STUB · declared (scripted transcript)` on every row — **never a REAL conversation**, and never three chips inside one call. The three voice bindings are **complete run variants** (`S1` `scripted_stub`, `S1-R` `retell_test`, `S2` `retell_webhook_replay`), not slices of one transcript; `retell_call.json` references all 16 `utt_*` IDs legitimately because every variant emits the same 16-ID shape. `12_…` §9's +00:10 chip is **per-run and binding-dependent**. `aud_12` / `aud_13` are announced **BETWEEN-RUN** operator switches during rehearsal under `corr_rehearsal_0001` — not mid-call switches within `corr_demo_0001` — so `EV-A01` + C-4 and the honesty posture stay intact while the golden path remains provably vendor-independent (E-14).

### 10.4 The three zero counters

| Counter | Value | Where proven |
|---|---|---|
| `0 real dialled calls` | 0 | `retell_call.json` `real_dialled_calls: 0`, `synthetic_caller: true`; `demo_sink_messages.csv` `ds_03`; `adapter_bindings.csv` HARD-BLOCKED columns; `integrity_report.json` |
| `0 real client-facing sends` | 0 | `demo_sink_messages.csv` `ds_03`; email `draft` ONLY |
| `0 real PII` | 0 | all names fabricated, `@demo.invalid`, `<PHONE_PLACEHOLDER>`; `integrity_report.json` no-real-data guard |

Frozen counters remain: **0 sends / 0 trades**. A sandbox CRM write (`sync_01…sync_06`) is `REAL (SANDBOXED)` and explicitly `is_send = false`.

### 10.5 Fully offline rehearsal + sandbox re-seed by external ID ≤60s

`adapter_bindings.csv` lists all six announced bindings (`IF-A01` × 3, `IF-A02` × 3); its two `default_flag = true` rows are `hubspot_free` and `scripted_stub`, consistent with S1. `scenarios.json` S1 (golden path) and S3 / S4 run on **`scripted_stub`** (S3/S4 also `local_stub` for CRM) with 0 external calls, proving the golden path end-to-end offline; `vendor_health.csv` `vh_06` records that rehearsal. `hubspot_portal_seed.json` gives every synthetic object a stable external ID (`hs_ct_001…`, `hs_deal_001`, `hs_task_001`) so the sandbox portal can be **re-seeded by external ID** on reset. Reset reuses the single generator load path (truncate-and-reload from the frozen flat-file baseline) and re-verifies `dataset_checksum` in the same operation — comfortably within NFR-9 / NFR-A4's **≤60s**, with the audit log archived by `run_id` and never deleted. Go/no-go (14 §9): if the sandbox portal, Private App token or read-after-write verification fails, run the entire demo on the offline bindings — **the journey is unchanged, only the honesty chip changes**.

### 10.6 `manifest_addendum_crm.json` — the 52nd file (12_… §10.2 / §12.1)

`12_…` §10.2 requires a **separate architect-authored addendum** declaring the six additive `crm.*` tables and all vendor external-reference files, **explicitly NOT inside `manifest_v1.3`**. `demo_data/manifest_addendum_crm.json` satisfies this with top-level:

```json
{
  "synthetic_marker": "SYNTHETIC DEMO DATA",
  "architect_authored": true,
  "manifest_version_not_bumped": true,
  "manifest_v1_3_read_only": true,
  "phase4_sync": true,
  "no_new_postgres_tables_from_vendor_adapters": true,
  "explicitly_not_inside_manifest_v1_3": true,
  "dataset_checksum": "sha256:acc91f0c0038c03726c0314823e1082c7cc65722d950ef9e8dc8ff6d5b86669c"
}
```

`declared_files[]` covers the 6 `crm_*` CSVs, `crm_old_new_preview.csv`, `hubspot_portal_seed.json`, `hubspot_api_exchange.json`, `retell_call.json`, `adapter_bindings.csv`, `vendor_health.csv`, `transcript_utterances.csv`, `config_versions.csv`, `demo_sink_messages.csv`, `scenarios.json` and the addendum itself (17 entries); `related_external_reference_files[]` cross-references the booking / event / attendee / extraction / email files for the §10.2 load order; `load_order[]` records all 51 `<NN>_<schema>_<table>` steps. The 52nd file is declared **in the addendum itself, in `checksums.sha256`, in `integrity_report.json` and in this guide's §4.7 inventory**. `manifest_v1.3.json` stays FROZEN / `read_only` / `v1.3` with its 51-file frozen scope unchanged — only its `dataset_checksum` hash value, the per-file hash values and the `scenarios.json` declared row count (4 → 5, for the S1-R variant) were refreshed. The addendum's `notes[]` now also records the E-15 one-call-one-binding and E-16 canonical-filename clarifications.

---

## 11. "If Alan provides nothing" — stand-in mapping to DI-01…17

The demo still works **entirely on generated synthetic data** (Phase A §6.2). Here is the concrete stand-in actually present in this pack for every intake item:

| DI | Item | Synthetic stand-in in this pack |
|---|---|---|
| **DI-01** | Booking-reading decision | **(i) appointment booking** — `bookings.csv` `bk_01…bk_06`; readings (ii) trade/order and (iii) booking entity are **reference-only** (`accounts.csv` `booking_centre_code` attribute), **no tables, no execution path** |
| **DI-02** | Market feed entitlement / attribution | `<source>:v1` versioned placeholder (`market_ticks_live.csv`), `REPLAY — recorded 09:58` (`market_ticks_replay.csv`), `config_versions.csv` `cfg_06`; **no vendor invented** |
| **DI-03** | Any real client data? | **No** — 100% synthetic; `integrity_report.json` no-real-data guard |
| **DI-04** | Jurisdiction / currency | `clients.csv`: SGD / Singapore / SGT / English, minority HKD + USD |
| **DI-05** | Transcript / scripted dialogue | `transcript_utterances.csv` `utt_01…utt_16` (`utt_09` daughter fact; golden-path run `scripted_stub` 16/16) + `retell_call.json` (declared STUB / SIMULATED; complete run variants) |
| **DI-06** | CRM field mapping + write permissions | `crm_field_mapping.csv` `map_01…map_08`, `fmv_20261105_1`; literal rule `approval_token + field_mapping_version`; physical key `appr_001:fmv_20261105_1:map_01` (deviation 2) |
| **DI-07** | Calendar `.ics` + attendees | `meetings_calendar.csv` `evt_01…evt_06` (Wong 10:00), `meeting_attendees.csv` incl. ambiguous `att_amb_01` |
| **DI-08** | Booking records | `bookings.csv` `bk_01…bk_06` (reading i only) |
| **DI-09** | Email threads | `email_threads.csv` `thr_01…thr_04`, `email_messages.csv` `msg_01…msg_04` on `@demo.invalid`, all `draft` |
| **DI-10** | Disclosure / template / consent wording | `email_templates.json` — illustrative, `not_legally_approved: true` |
| **DI-11** | CRM interaction / task / opportunity | `crm_interactions.csv`, `crm_tasks.csv`, `crm_opportunities.csv` |
| **DI-12** | Portfolio / product / suitability | `holdings.csv`, `allocation_targets.csv`, `products.csv` (screened-status placeholder only), `suitability_state.csv` |
| **DI-13** | Household / entity documents | `graph_source_docs.csv` `doc_01…doc_08` (100% synthetic, labelled) |
| **DI-14** | Shariah project boundary | `graph_nodes.csv` `nd_01` preference-flag pointer + `memory_facts.csv` `mf_017`; **flag OFF, zero screening/zakat/SSB data** |
| **DI-15** | Branding / naming | `Sarah (RM)`, fabricated client names, `name_note` column; no real logo |
| **DI-16** | Real screenshots | **None** — frozen SCR/CMP + labelled stubs only |
| **DI-17** | Live feed schema / recorded ticks | `market_ticks_replay.csv` 120-frame excerpt, original `feed_as_of` preserved |

What is **less convincing** without Alan's inputs (honest, from Phase A §6.2): the +00:00 tick cannot claim a genuinely licensed `LIVE` source (D1 leans on the replay fallback); wording is generic rather than the firm's tone of voice; no UI echo; jurisdiction/currency may be wrong; "booking" shows only appointment booking; the Shariah beat stays a labelled pointer. **None of these block the loop.**

---

## 12. DI-18…25 stand-in mapping (vendor adapters)

From `14_…` §8. **DI-19 is the critical one: the token is out of band, placeholder only.**

| DI | Item | Default if absent / stand-in in this pack |
|---|---|---|
| **DI-18** | HubSpot Free sandbox portal confirmation | Assume available: `hubspot_portal_seed.json` `portal` descriptor (Free, 2 seats, 1 pipeline, Private Apps assumed). If not → run entirely on `local_stub` (`adapter_bindings.csv` `IF-A01` local_stub row) — **do not purchase** |
| **DI-19** | Private App token + scope list | **Literal placeholder `<HUBSPOT_PRIVATE_APP_TOKEN>` only**, `token_out_of_band: true`, `no_real_credential: true`, `no_realistic_looking_token: true` in `hubspot_api_exchange.json` (the `Authorization` header of the PATCH / GET examples). **Never in repo, never in sample data, never a realistic-looking token.** Default binding `local_stub` |
| **DI-20** | HubSpot object/property map | `crm_field_mapping.csv` `map_01…map_08` with `hubspot_property`, `object_type`, `custom_property_slot` 1–8 (≤10), `writable`, `transform`, `version = fmv_20261105_1`, literal `idempotency_key` rule + `physical_idempotency_key`; contacts-only write-back |
| **DI-21** | Permission to show HubSpot branding | **No** real branding; generic `HUBSPOT FREE · DEMO SANDBOX PORTAL` text only |
| **DI-22** | Retell go/no-go + agent config | **OFF by default** → `scripted_stub` (`IF-A02` scripted_stub row); if enabled, `retell_call.json` `simulation_test_call`, `synthetic_caller: true`, `language en-SG` |
| **DI-23** | Retell post-call webhook payload | `retell_call.json` `post_call_webhook` — labelled synthetic / REPLAY-shaped transcript + extraction candidates (`utt_09` daughter fact) |
| **DI-24** | Consent / AI-disclosure wording for real calls | **No real calls** — `email_templates.json` `consent_wording` illustrative only |
| **DI-25** | Confirm `0 real dialled calls` | **Yes, enforced** — `demo_sink_messages.csv` `ds_03`, `retell_call.json`, `integrity_report.json` |

Open questions OQ-9…13 keep their `14_…` §8 defaults: OQ-9 sandbox write permitted post-Approve (declared `REAL (SANDBOXED)`); OQ-10 Retell optional, test-call with synthetic caller; OQ-11 no branding; OQ-12 out of scope; OQ-13 no HubSpot/Retell pointer for the external Shariah project (preference-flag pointer only, E-3 unchanged).

---

## 13. Sensitivity / honesty checklist (binding on every fact)

Derived from `11_…` §7 plus E-10 / `14_…` §7 and the E-15 / E-16 clarifications. Verified in `integrity_report.json` (**34 PASS checks**).

| # | Rule | How this pack satisfies it | Verified |
|---|---|---|---|
| 1 | No real PII | Fabricated names + `name_note`; `@demo.invalid`; `<PHONE_PLACEHOLDER>`; no real issuer/bank/vendor; no real religious rulings | PASS — only `@demo.invalid` domain found |
| 2 | C-1 on every fact | 8-column envelope, all 7 C-1 columns non-null on every CSV row | PASS — **0 nulls / 1,277 rows** |
| 3 | Permanent `SYNTHETIC DEMO DATA` | README header, top-level marker in all 12 JSON, column on all 43 CSV | PASS — **0 bad rows** |
| 4 | No bare statements | every brief/signal/audit row carries `source_id` + `as_of` + chip | PASS |
| 5 | No invented ticks / last-price substitution | F1 has **no new tick after 09:58:14**; only `fs_001` stale at age 47s; replay frames preserve original `feed_as_of` | PASS |
| 6 | No `sent` state | `email_messages.state = draft` ONLY; **0 exact `sent` state values anywhere**. A sandbox CRM write is explicitly **not** a send | PASS — 0 |
| 7 | No trade execution path | **No trade/order table, no execution path**; ticket handoff `execution disabled` | PASS — 0 trade/order filenames |
| 8 | No silent `LIVE` on replay | replay rows `source_kind=replay`, `mode=replay`; `LIVE` impossible while bound to replay | PASS |
| +E-10 | `REAL (SANDBOXED)` qualifier | `adapter_bindings.csv` `IF-A01 hubspot_free`; `hubspot_portal_seed.json` posture | PASS |
| +E-10 | 0 real dialled calls / 0 client-facing sends / 0 PII | `demo_sink_messages.csv` `ds_03`; `retell_call.json` | PASS — 0 / 0 / 0 |
| +E-12 | Single-Approve gate preserved | `appr_001` immutable; Retell native HubSpot integration `OFF` (`cfg_17`); all writes post-Approve | PASS |
| +E-13 | ≤10 custom properties, no inbound webhooks | slots 1–8 used; `cfg_18 inbound_webhooks_used = false`; read-after-write GET | PASS |
| +E-7 | `manifest v1.3` not bumped | `frozen: true, read_only: true`, `v1.3`, 51-file scope; addendum separate | PASS |
| +§4.10-1 | Physical uuid FK | `client_id_uuid` valid / unique / 1:1 between `clients.csv` and `crm_contacts.csv` | PASS |
| +§4.10-2 | Idempotency keys do not collapse | six distinct keys `map_01…map_06`, 8 unique keys across 8 sync rows; `fmv_20261105_1` everywhere | PASS |
| +§7.4 | Daughter fact is `utt_09` | `00:03:12` / `0.94`; all 16 `source_id`s match row IDs; evidence refs in `memory_facts` / `extraction_items` / `crm_old_new_preview` / `retell_call` point to `utt_09` | PASS |
| +E-15 | One call = one binding | 16/16 `transcript_utterances.csv` rows `scripted_stub` + single per-run STUB chip; `retell_test` / `retell_webhook_replay` are complete run variants (S1-R / S2); `aud_12`/`aud_13` under `corr_rehearsal_0001` | PASS |
| +E-15 | Audit hash chain | 18/18 `audit_events.csv` rows verify end-to-end from a 64-zero genesis | PASS |
| +E-16 | Canonical filename map | `schema_contract.json → canonical_filename_map` maps all 51 manifest files; 8 frozen schemas; `NN` from `load_order[].seq`; no file renamed, manifest not bumped | PASS |

---

## 14. Validation results (computed, not asserted)

| Check | Method | Result |
|---|---|---|
| CSV parse | `csv.reader` over all 43 CSVs; header = 8-col envelope; column count per row | **PASS** — 1,277 rows, all widths consistent |
| JSON parse | `json.load` over all 12 JSONs + top-level `synthetic_marker` | **PASS** — 0 invalid |
| C-1 completeness | count empty envelope cells | **0 nulls** |
| FK integrity | 35 declared FK rules, 1,828 references checked | **0 orphans** |
| `checksums.sha256` | `grep -v '^#' checksums.sha256 \| shasum -a 256 -c -` | **52 / 52 OK** (REAL hashes; 51 data + addendum) |
| `dataset_checksum` | `sha256(concat(sorted per-file hashes of the 51 frozen data files))` | `sha256:acc91f0c0038c03726c0314823e1082c7cc65722d950ef9e8dc8ff6d5b86669c` — **matches manifest / integrity_report / addendum / guide** |
| `pack_checksum_52` | `sha256(concat(sorted per-file hashes of all 52 checksums.sha256 lines))` | `sha256:ec06381830a51ae8a31adfd805d4e314e64aa1c1f3576947944bb3df2b8de1c8` — **matches integrity_report.determinism / guide** |
| determinism | recompute from the frozen files → identical `dataset_checksum`; one seed `20261105` + `splitmix64` | **PASS** (run1 == run2) |
| exactly 1 signal / 6 nodes / 8 edges / 8 docs / 6 CRM tables / 2 packs | row counts | **PASS** |
| `ent_matrix_v1` | `Mr_Tan` all 6; `Next_gen` `nd_01, nd_03, nd_04` only | **PASS** |
| `utt_09` daughter fact | `00:03:12` / `0.94`; 16 unique IDs, `source_id` matches, monotonic offsets, **16/16 `scripted_stub`** | **PASS** |
| six distinct idempotency keys | `crm_sync_log.csv` `map_01…map_06` distinct; 8 unique keys overall; `fmv_20261105_1` | **PASS** |
| `client_id_uuid` | valid uuid / unique per client / 1:1 across the two files | **PASS** |
| `succeeded` timestamps > 10:14:32 | `crm_sync_log.csv` scan | **PASS — 0 before** |
| 0 `sent` states | exact-state scan across all CSVs | **PASS — 0** |
| 0 real credentials | only `<HUBSPOT_PRIVATE_APP_TOKEN>` appears; 0 realistic Bearer tokens | **PASS** |
| 0 real phone numbers | only `<PHONE_PLACEHOLDER>` | **PASS** |
| 0 real domains | only `@demo.invalid` | **PASS** |
| custom properties ≤ 10, slots 1–10 | `crm_field_mapping.csv` | **PASS** — slots 1–8 |
| offline-binding scenario present | `scenarios.json` S1 golden path = `scripted_stub`; S3 / S4 = `local_stub` + `scripted_stub` | **PASS** |
| addendum present / manifest frozen | `manifest_addendum_crm.json` flags; `manifest v1.3` frozen/read_only/v1.3/51 files | **PASS** |
| flat-file ↔ Postgres `EXCEPT` | declared expectation (G5): 0 rows in both directions via `file_fdw` CSV twin | **PASS (expected)** |
| no-real-data guard / fail-loud X-20 | declared: `BLOCKED` on non-`demo_*` DSN; `SCHEMA MISMATCH · <offending record> · demo start BLOCKED · ROLLBACK` | **PASS (declared)** |
| DESIGN ONLY | scan `deliverables/` for `.py/.sh/.js/.ts/.sql/.parquet/.ipynb` | **PASS — 0 files** |
| one-call-one-binding (E-15) | 16/16 `scripted_stub`; S1 / S1-R / S2 complete run variants; `aud_12`/`aud_13` = `corr_rehearsal_0001` | **PASS** |
| audit hash chain | recompute `sha256(prev_hash + event_id + event_type + event_at)` from 64-zero genesis | **PASS — 18/18 end-to-end** |
| canonical filename map (E-16) | `schema_contract.json` maps 51 files: 29 CSV + 4 JSON + 18 additive; `NN` = `load_order[].seq` | **PASS** |
| `integrity_report.json` verdict | — | **PASS** (34 checks) |

`checksums.sha256` has a leading `#` banner comment for the synthetic marker; verify with the filtered `shasum -a 256 -c -` command above (or `sha256sum -c` after filtering). `manifest_v1.3.json` declares 51 data files (real checksums) + 5 control artefacts (README, checksums, schema_contract, integrity_report, self); the **6th control artefact** `manifest_addendum_crm.json` is declared in the addendum / checksums.sha256 / integrity_report / §4.7. `schema_contract.json` declares 35 FK rules, the `\N` null sentinel, deferred FKs, the `uuid_resolution` block, the `idempotency_rule`, the `load_order`, the **`canonical_filename_map`** (E-16), the extension set and the exact 6 CRM table names. `integrity_report.json` carries **34 PASS checks** (3 added for E-15 / E-16); `dataset_checksum` and `pack_checksum_52` above are the recomputed values after those changes.

---

## 15. Deviations from the specification

No material deviation. The following are explicit, documented **additive clarifications** (12_… §4.10 deviations 1 & 2, §10.2) and interpretation choices, all reported in the hand-off:

1. **Physical uuid FK (12_… §4.10 deviation 1).** `03_Technical_Solution.md` line 854 freezes `client.client.client_id` as `uuid PRIMARY KEY`; a `text` → `uuid` FK would not execute. Accordingly `clients.csv` and `crm_contacts.csv` carry **both** the projector-visible text registry key `client_id` (used by every flat-file FK) **and** `client_id_uuid` — a deterministic RFC-4122 v4 UUID derived from `splitmix64(20261105, '<client_id>')` (mix each key byte into the seed via `splitmix64`, take `a` = that digest, `b = splitmix64(a ^ 0xD1B54A32D192ED03)`, build a 128-bit int `(a<<64)|b`, set version-4 and RFC-4122 variant bits, format via `uuid.UUID(int=...)`). `schema_contract.json` adds the uuid-resolution FK rule + `uuid_resolution` block; `integrity_report.json` adds a PASS check that every uuid is valid, unique per client and 1:1 between the two files. Example: `cl_wong_001` → `0cabbbc6-0405-433a-a263-6fbaba4e5fa9`. No literal text→uuid FK is emitted.
2. **Physical idempotency key (12_… §4.10 deviation 2).** The literal binding rule `idempotency_key = approval_token + field_mapping_version` is restated verbatim in `crm_field_mapping.csv`. One immutable token `appr_001` produces **six accepted writes** at one `field_mapping_version`; without a per-field disambiguator all six would share one `UNIQUE` key and collapse into a single effect (breaking FR-19 / NFR-18). The physical key therefore appends `mapping_id`: `approval_token || ':' || field_mapping_version || ':' || mapping_id`, e.g. `appr_001:fmv_20261105_1:map_01`. `crm_sync_log.csv` carries six distinct keys for `map_01…map_06` (8 unique across all 8 rows, including the pending 429 and failed rows); the version is `fmv_20261105_1` everywhere (`version_registry.csv` `vr_06`, `config_versions.csv` `cfg_19`, `approval_tokens.json`, `hubspot_api_exchange.json`). **This is an additive physical clarification, not a change to the frozen registry rule.**
3. **Separate architect-authored addendum (12_… §10.2 / §12.1).** The six additive `crm.*` tables and vendor external-reference files are declared in `manifest_addendum_crm.json`, **never inside `manifest_v1.3`**. `manifest v1.3` is FROZEN / `read_only` / `v1.3` with its 51-file frozen scope unchanged; only its `dataset_checksum` hash value, the per-file hash values and the `scenarios.json` declared row count (4 → 5, for the S1-R variant) were refreshed (no version bump, no flag change, no scope change).
4. **`dataset_checksum` scope + the 52nd line.** `dataset_checksum = sha256(concat(sorted per-file sha256 hex hashes of the 51 frozen data files))`. `checksums.sha256` carries 52 lines: the 51 data files **plus** a 52nd control-file verification line for `manifest_addendum_crm.json`. That 52nd line is **excluded** from `dataset_checksum` to avoid self-reference — the addendum contains the `dataset_checksum` value, so folding its own hash in would be circular. The same value is restated consistently in `manifest_v1.3.json`, `integrity_report.json` and the addendum.
5. **`checksums.sha256` carries a leading `#` banner comment** so every artefact including the verification file shows the synthetic marker; the file remains machine-verifiable via `grep -v '^#' … | shasum -a 256 -c -` (**52/52 OK**). It is a control artefact, not a data file, so it is not itself hashed (no circularity); its checksum is declared in `manifest.control_artifacts[]`.
6. **`manifest_v1.3.json` scopes "every file" to `demo_data/`.** The guide `13_Demo_Seed_Pack.md` is a sibling deliverable outside the hashed dataset and is explicitly referenced in `manifest.scope`. `manifest_v1.3.json` itself is listed with `checksum: "n/a (self-reference — manifest is read-only)"` — a self-hash would be circular; all other control artefacts carry real checksums.
7. **Canonical filename map (E-16 / `12_…` §10.2 "Naming scope").** The frozen `<NN>_<schema>_<table>.<ext>` convention applies only to the 51 files declared by READ-ONLY `manifest v1.3` (the 8 frozen schemas), because `file_fdw` foreign tables and the G5 `EXCEPT` check bind to those exact paths. The sample pack's legible names are **display aliases** — `clients.csv` is neither additive nor a replacement, it is the display alias of the frozen `client.client` table. `schema_contract.json → canonical_filename_map` maps all 51 files: **29** frozen-schema CSVs to `<NN>_<schema>_<table>.csv`, **4** frozen-schema JSONs to `<NN>_<schema>_<table>.json`, and **18** additive `crm.*` / vendor external-reference files to exactly the names declared in `manifest_addendum_crm.json`. `NN` is taken verbatim from `load_order[].seq` (record schema + table, then look up the seq) — **no arbitrary number is invented**. The future generator emits canonical names; the sample pack keeps its leadership-legible aliases; **no file is renamed** and `manifest v1.3` is not bumped. The full 51-step `load_order[]` remains in `manifest_addendum_crm.json` and `schema_contract.json`.

8. **One call = one binding (E-15 / `12_…` §7.4 / §9).** The earlier pack split one 16-utterance call across three `adapter_binding` values (9/4/3), which read as an unannounced mid-call switch and contradicted `scenarios.json` S1's single voice binding and the per-run +00:10 chip. Now `transcript_utterances.csv` is the **golden-path `scripted_stub` run with 16/16 rows uniform** (only `adapter_binding` and the per-row `source_chip` changed — `STUB · declared (scripted transcript)`); utterance text, offsets, `utt_09` @ `00:03:12` / `0.94`, all `source_id` values, `mf_001`, `ex_*`, `pv_01`/`pv_06` evidence refs are unchanged. `retell_test` and `retell_webhook_replay` become **complete run variants**: `scenarios.json` S1 = `scripted_stub`, opt-in `S1-R` = `retell_test` with the SIMULATED chip, S2 = `retell_webhook_replay`, S3/S4 = `local_stub` + `scripted_stub`; `adapter_bindings.csv` keeps all 6 rows with `default_flag` `hubspot_free` + `scripted_stub` consistent with S1; `retell_call.json` notes all three variants emit the same 16-ID shape. The +00:10 chip is **per-run and binding-dependent** (`12_…` §9). No utterance text was changed, and no mid-call fallback language remains.
9. **Audit chain requalification + integrity checks (E-15 point 3).** `audit_events.csv` `aud_12` / `aud_13` (`adapter.binding.switch`) were reframed as **BETWEEN-RUN operator switches during rehearsal** under a separate `corr_rehearsal_0001`, with detail text stating they are not mid-call switches within `corr_demo_0001`. The full `prev_hash` / `row_hash` chain was recomputed for all 18 rows from a 64-zero genesis using the emitted formula `sha256(prev_hash + event_id + event_type + event_at)` and verifies **18/18 end-to-end**. Because that emitted chain binds `event_id` / `event_type` / `event_at` (not `correlation_id` / `detail`), the stored hash values for the two requalified rows remain valid — the chain stays tamper-evident over its declared fields. Three new PASS checks were added to `integrity_report.json` (`audit_hash_chain`, `one_call_one_binding`, `canonical_filename_map`), taking it from 31 to **34 checks**; `dataset_checksum`, `pack_checksum_52`, `checksums.sha256` and all control-artefact checksums were recomputed accordingly.

Additions beyond the minimum file list (all supporting, all C-1-complete, all declared): `rm_books.csv`, `feed_status.csv`, `version_registry.csv`, `consent_state.csv`, `suitability_state.csv`, `products.csv`, `interactions.csv`. They exist to make `clients.rm_book_id` FK-clean, to host the F1 stale row explicitly, and to populate the +00:08 brief / +00:14 review / F2 beats from real rows. `crm_old_new_preview.csv` is a review-surface artefact, **not** a 7th `crm.*` table — the 6-table count is exact.

**Everything delivered lands on disk** (global rule 4): this guide plus `deliverables/demo_data/` (57 files). Design only — no code has been written, no credentials created, no vendor account opened, no DDL executed, no trade/order table, no `sent` state. `manifest v1.3` is not bumped. E-15 (one call = one binding) and E-16 (canonical filename map) are applied without renaming any file. `12_Demo_Data_and_Systems_Architecture_Enhancement.md`, `14_Vendor_Adapter_Ruling_HubSpot_Retell.md`, `15_Enhancement_Executive_Summary.md` and `RM_Workbench_MVP_Design_Package.md` were NOT edited — they are ratified and authoritative; the seed pack conforms to them.

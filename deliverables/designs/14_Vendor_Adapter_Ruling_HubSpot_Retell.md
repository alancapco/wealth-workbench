# Vendor Adapter Ruling — HubSpot Free (CRM) + Retell AI (Voice Agent)

**Addendum to:** `10_Data_Enhancement_Brief.md` and the *Next-Generation RM Workbench MVP Design Package* (5 Nov 2026)
**Trigger:** Alan, 6 Nov 2026 — *"for CRM, i plan to use hubspot free as the demo, i may use retell.ai as an agent , please plan this in"*
**Owner:** Qi Huolin (Delivery Director), software-dev-team — team-lead ruling
**Status:** **DESIGN ONLY.** No application code, no runnable generator, no scaffold, no executed DDL, no credentials created, no vendor account opened.
**Language:** English.
**Authority:** This document **amends E-4** and **supersedes OQ-8's default**. All other frozen artefacts remain frozen (E-7).

---

## 1. Reading the request precisely

| Phrase | Reading | Consequence |
|---|---|---|
| "i **plan** to use hubspot free as the demo" | Committed intent | HubSpot Free becomes the **primary CRM binding**, not a hypothetical |
| "i **may** use retell.ai as an agent" | **Tentative** | Retell must be **optional and off the critical path**; the golden path must run without it |
| "please plan this in" | Additive, design-stage | No new product-design phase (E-1); this is an **adapter/binding** change, not a new screen or component |

**Critical framing.** E-4 froze the CRM as an *in-Postgres stand-in* with "real CRM remains a stub/demo sink per the frozen honesty posture". A real external SaaS is not a stub. Treating HubSpot as "just another label on the same 6 tables" would misstate the architecture and break the honesty posture that the leadership demo depends on. **This is therefore a ratified amendment, not a silent implementation detail.**

---

## 2. Evidence register — HubSpot Free (retrieved 6 Nov 2026)

| # | Finding | Grade | Source |
|---|---|---|---|
| H-1 | Free tier includes CRM objects API v3 — contacts, companies, deals, tickets, activities (calls, emails, meetings, notes, tasks), associations, search, batch (≤100 inputs). Base `https://api.hubapi.com`. | `[EVIDENCE · vendor-adjacent]` | developers.hubspot.com via [ibl.ai HubSpot connector](https://ibl.ai/developer/connectors/hubspot), [Knit API guide](https://getknit.dev/blog/hubspot-api-directory-od0rst) |
| H-2 | Auth via **Private App access token** (Bearer, scope-minimised) or OAuth. Legacy API keys deprecated 30 Nov 2022. Private Apps generally available on Free, but **some older free / developer-portal accounts do not expose them**; a Starter upgrade may be required. | `[EVIDENCE]` + `[RISK]` | [HubSpot legacy private apps docs](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview), [SFAILabs 2026 guide](https://sfailabs.com/guides/how-to-get-hubspot-api-key) |
| H-3 | Private App rate limits: **100 req / 10 s per app**, **250,000 / day per account** on Free/Starter; over-limit → `429` with `Retry-After`. | `[EVIDENCE · first-party docs]` | [HubSpot private apps docs](https://developers.hubspot.com/docs/apps/legacy-apps/private-apps/overview) |
| H-4 | **Webhook availability on Free is contested.** One source: "Webhooks API available on all plans including Free"; another: "webhook subscriptions require a **public app** — not available on private apps". All sources agree **workflow webhook actions require Operations/Data Hub Professional (~US$800/month)** and inbound workflow triggers require Professional/Enterprise. | `[CONFLICTING]` → **treat as unavailable** | [FranchiseNinja webhooks](https://help.franchiseninja.ai/portal/en/kb/articles/hubspot-webhooks-16-10-2025), [Knit](https://getknit.dev/blog/hubspot-api-directory-od0rst), [AutomationAtlas Data Hub pricing](https://automationatlas.io/answers/hubspot-operations-hub-pricing-2026) |
| H-5 | Free tier limits are **cohort/region-dependent and mutually contradictory across sources**: 1,000 contacts / 2 users / 1 pipeline / **10 custom properties** / no or 5 simple workflows (Claritysoft, MO Agency, AutomationAtlas) **vs** 1,000,000 contacts / unlimited users (older guides, PlanMyHub current model) **vs** 3,000 records for new EMEA accounts (PlanMyHub). Robust across all: **1 deal pipeline, 10 custom properties, limited/no automation, HubSpot branding on emails/forms/meeting links.** | `[CONFLICTING]` → design to **intersection** | [Claritysoft](https://claritysoft.com/?p=998335), [MO Agency](https://www.mo.agency/blog/what-are-the-limitations-of-hubspots-free-crm), [PlanMyHub](https://planmyhub.com/resources/hubspot-free-crm), [AutomationAtlas](https://automationatlas.io/answers/can-you-use-hubspot-crm-for-free) |
| H-6 | Free tier carries **HubSpot branding** on emails, forms, landing pages, live chat and meeting links; branding removal is a paid feature. | `[EVIDENCE]` | Claritysoft, MO Agency, PlanMyHub |
| H-7 | A remote HubSpot MCP server (`mcp.hubspot.com`, OAuth 2.1 PKCE, "GA 13 Apr 2026") is claimed by a third-party connector directory. | `[UNVERIFIED · third-party]` | [ibl.ai connector](https://ibl.ai/developer/connectors/hubspot) — **not designed against** |

**Design consequence (H-4 + H-5):** no reliance on inbound HubSpot webhooks; **≤10 custom properties**; all orchestration stays in the workbench because the free tier has no real automation. The 30–50 synthetic contacts are under every published cap, so the cohort conflict is immaterial to data volume.

---

## 3. Evidence register — Retell AI (retrieved 6 Nov 2026)

| # | Finding | Grade | Source |
|---|---|---|---|
| R-1 | Managed **voice agent** platform for real inbound/outbound phone calls; ~600 ms latency, interruption handling, function calling, ~55 languages. Post-call delivers **transcripts, recordings and structured outcome data** via webhook/API. | `[EVIDENCE · first-party]` | [retellai.com](https://www.retellai.com/), [Retell receptionists](https://retellai.com/use-cases/receptionists) |
| R-2 | Pay-as-you-go **US$0.07–0.31/min**; **US$10 free credits** at signup covering building an agent, **simulation testing** and **live test calls**; 20 free concurrent calls. Transcripts, call analytics, **simulation testing, webhooks and API access** are included on the base plan. Chat agents from ~US$0.002/message. | `[EVIDENCE · first-party + pricing aggregator]` | [Retell pricing via APIs.io](https://apis.io/plans/retell/retell-plans-pricing), [Retell vs Twilio](https://www.retellai.com/comparisons/retell-vs-twilio) |
| R-3 | **Simulation testing** runs AI-simulated callers against the agent and grades each run against success criteria; production calls can become regression tests. | `[EVIDENCE · first-party]` | [Retell vs Twilio](https://www.retellai.com/comparisons/retell-vs-twilio), [Retell receptionists](https://retellai.com/use-cases/receptionists) |
| R-4 | Claims **SOC 2 Type I & II, ISO 27001, HIPAA (self-serve BAA), GDPR (self-serve DPA)**; built-in PII redaction; configurable retention **1 day–2 years**; option to **opt out of storing recordings/audio** on Retell's systems; enterprise on-prem for data residency. PII redaction is listed as a **paid add-on (+US$0.01/min)** in the pricing schedule — the two statements are not fully reconciled. | `[EVIDENCE · first-party claim]` + `[CONFLICT]` | [retellai.com](https://retellai.com/), [Retell receptionists](https://retellai.com/use-cases/receptionists), [APIs.io pricing](https://apis.io/plans/retell/retell-plans-pricing), [Retell community](https://community.retellai.com/t/health-care-use-case/746/4) |
| R-5 | **Native HubSpot integration is listed** among Retell's out-of-the-box connectors; the agent can read/write CRM mid-call. | `[EVIDENCE · first-party]` → **[GOVERNANCE RISK]** | [Retell receptionists](https://retellai.com/use-cases/receptionists), Retell healthcare use-case page |
| R-6 | Retell's own FAQ: **outbound calling requires prior consent under TCPA**, some US states require **disclosure that the caller is automated**, recording-consent rules vary, and the FCC has ruled AI-generated voices in robocalls fall under existing TCPA restrictions. "Compliance depends on how the platform is used, not on the platform itself." | `[EVIDENCE · first-party legal framing]` | [retellai.com FAQ](https://www.retellai.com/) |

**Design consequence (R-3 + R-5 + R-6):** Retell's **simulation / test-call** mode is the honest bridge — a real platform producing a real transcript from a **synthetic caller**, with **zero real persons dialled**. But its native HubSpot write would **bypass the single-Approve gate**, so it must be disabled. Real outbound dialling is HARD-BLOCKED.

---

## 4. Regulatory / governance context — Hong Kong & Singapore

Alan's research concerns AI governance in financial services and the gap between formal principles and operational controls. This is the evidence base for treating "an agent that writes to CRM mid-call" as a governance issue, not just an integration choice. **Evidence and inference are separated deliberately.**

| # | Statement | Grade | Source |
|---|---|---|---|
| G-1 | **PDPO (Cap. 486)** Data Protection Principle 1 requires a lawful purpose and **notification of the purpose and use of collection**; a one-party-consent analysis of interception does **not** discharge PDPO collection/notification/retention/security duties. Transcripts and AI summaries carry the same privacy obligations as audio; every copy counts. | `[EVIDENCE · legal commentary]` | [Genium Group PDPO call-recording checklist](https://genium-group.com/zh-hk/blog/pdpo-call-recording-hong-kong-compliance-checklist-msgei1m2?lang=zh) |
| G-2 | Outbound AI dialling in Hong Kong additionally engages **UEMO (Cap. 593) / OFCA** (pre-recorded/AI messages, do-not-call register, no concealed caller ID) and **PDPO Part 6A** consent for use of personal data in direct marketing. PCPD guidance expects a spoken PICS-like disclosure **before** recording begins. | `[EVIDENCE · legal commentary]` | [Genium Group AI cold-calling](https://genium-group.com/zh-hk/blog/ai-cold-calling-agent-sales-teams-hong-kong) |
| G-3 | PCPD's 2021 *Guidance on the Ethical Development and Use of AI* sets seven principles incl. **accountability, human oversight, transparency/interpretability, data privacy, fairness, beneficial AI, reliability/robustness/security**. It is explicitly **non-binding**, but functions as the interpretive lens when PCPD exercises PDPO enforcement powers. | `[EVIDENCE · secondary analysis]` | [Hong Kong AI Regulation 2026 operator's guide](https://agentliability.co/articles/hong-kong-ai-regulation-2026-operators-guide.html) |
| G-4 | **HKMA** has issued guidance on consumer protection for big-data analytics/AI and extended supervisory expectations to generative AI (governance, model risk, data security). **SFC** has issued a circular on generative-AI language models requiring **senior management to remain accountable** for AI-assisted research, advice and client communications, with expectations on data governance, model validation and disclosure. These operate through existing supervisory powers rather than a standalone AI statute. | `[EVIDENCE · secondary analysis]` | [Agent Liability HK guide](https://agentliability.co/articles/hong-kong-ai-regulation-2026-operators-guide.html) |
| G-5 | Third-party country survey states: Hong Kong PDPO requires notification before recording; **SFC-regulated firms must record telephone conversations relating to regulated activities**; Singapore (MAS) recorded-call minimum retention **5 years**; AI transcription of live calls is treated as call recording in virtually all jurisdictions. | `[EVIDENCE · third-party survey — verify with primary regulator before any real call]` | [CallSphere 2026 country guide](https://callsphere.ai/blog/call-recording-laws-by-country-2026-guide) |
| G-6 | `[INFERENCE]` A vendor-native agent writing to CRM **mid-call** creates a workflow-level control gap: the human approval gate exists in the workbench design, but the vendor path bypasses it. This is precisely the "formal governance principles vs operational practice" gap, and a leadership demo that shows an ungated auto-write would demonstrate the wrong thing. | `[INFERENCE]` | Lead analysis, derived from R-5 + G-3/G-4 + frozen G2/G3 |
| G-7 | `[INFERENCE]` **US$10 of free credits and a 20-concurrent-call allowance are finite, vendor-dependent resources**; a leadership demo must therefore have an offline replay binding on the critical path, not as an afterthought. | `[INFERENCE]` | Lead analysis, derived from R-2 + frozen F1/NFR replay requirement |

> **Boundary:** none of the above is legal advice, and none of it is a claim that this MVP is compliant. It is the evidence base for the **HARD-BLOCKED** decisions in §5. Any move from simulated/test calls to real calls requires an explicit regulatory review and a new decision.

---

## 5. Ratified lead decisions (E-9 … E-16)

| ID | Decision | Effect on frozen artefacts |
|---|---|---|
| **E-9** *(amends E-4)* | **HubSpot Free is the primary external CRM binding** for the demo, in a **dedicated free sandbox portal** containing **100% synthetic records only**. The 6-table `crm` schema is **retained but re-purposed** as the adapter's **local projection + field mapping + idempotency/outbox ledger** — not as the CRM itself. Labels: external `HUBSPOT FREE · DEMO SANDBOX PORTAL`; internal `CRM ADAPTER · LOCAL PROJECTION (6 tables)`. The term `DEMO CRM (lightweight)` now denotes the **adapter**, not the external system. | `crm` schema stays additive; 8 frozen schemas / 40 tables unchanged. **E-4 amended**, not deleted. |
| **E-10** | **Honesty posture keeps its four frozen categories.** Add the qualifier **`REAL (SANDBOXED)`** = real vendor service + synthetic records + no real person contacted. Do **not** invent a fifth top-level category. New measurable hard stops: **0 real dialled calls, 0 real client-facing sends, 0 real PII**. A **system write to the sandbox portal after Approve is permitted** and must be declared on stage as `CRM write-back → sandbox portal (synthetic records)`; this is **not** a "send". | Posture taxonomy preserved; +1 qualifier, +3 counters. |
| **E-11** | Both vendors sit behind **additive interface contracts** `IF-A01` (CRM adapter) and `IF-A02` (voice/transcript adapter), each with **three announced bindings**: CRM `hubspot_free` → `local_stub` → `demo_sink`; Voice `retell_test` → `retell_webhook_replay` → `scripted_stub`. **No new SVC IDs** — adapters are bindings of **SVC-14 Demo Sink** and the context/capture path. `IF-01…22` and `EV-01…20` are **NOT renumbered**; additive IDs use `IF-Axx` / `EV-Axx`. Every binding switch is announced and emits a C-4 event. | Contract freeze E-7 intact. |
| **E-12** | **Single-Approve gate preserved.** Retell's **native HubSpot integration MUST be OFF**. Retell may produce only **transcript + extraction candidates**; all external writes (CRM properties, booking/calendar, email drafts) route through the human Approve / C-3 `appr_001`. Retell must not write to CRM, place real outbound calls, or trigger HubSpot workflows. This is the workflow-level control that closes G-6. | G2/G3/FR-18/19/23 intact. |
| **E-13** | **No dependency on inbound HubSpot webhooks.** Use outbound REST via a scope-minimised Private App token, then **read-after-write `GET` verification**; `crm.crm_sync_log` + `idempotency_key = approval_token + field_mapping_version` handle retries and `429 Retry-After`. Free-tier ceiling → **≤10 custom properties**, remainder map to standard HubSpot properties. Webhooks documented as future-optional, off the critical path. Free tier has no real automation, so **all orchestration stays in the workbench**. | NFR-18 idempotency extended, not replaced. |
| **E-14** | Because Alan said **"may"**, Retell is **optional and off the demo critical path**. If enabled, the +00:10 transcript comes from **Retell simulation / test call with a synthetic caller**, posture `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)`. The golden path must run end-to-end on `scripted_stub` or `retell_webhook_replay`. **HARD-BLOCKED:** real outbound dialling, recording of real persons, direct Retell→HubSpot writes. | F1/replay NFRs extended to cover vendor outage and credit exhaustion. |
| **E-15** *(post-Phase-B clarification; narrows the reading of E-11 / §6.3 / §6.4)* | **One call = one binding.** All **16 utterances of a single demo run carry the SAME `adapter_binding`**. `retell_test`, `retell_webhook_replay` and `scripted_stub` are **complete-run variants** (`S1` golden path vs the opt-in `S1-R` rehearsals), **never mid-call switches**: each switch requires an announced `EV-A01` + C-4 event, and the `+00:10` source chip is **per-run**. The **golden-path run is `scripted_stub` 16/16**; Retell bindings are opt-in whole-run rehearsals only. COROLLARIES: §6.3's "add `adapter_binding` column: `retell_test` \| `retell_webhook_replay` \| `scripted_stub`" is an **enumeration of allowed run-level values**, not a split within one transcript; §6.4's "announced binding switch **within one beat**" is **withdrawn** — switches happen **between runs**, never inside a call. | Contract freeze E-7 intact; `IF-A02` / `EV-A01` unchanged; `12_…` **§7.4** is authoritative. |
| **E-16** *(post-Phase-B clarification)* | **Canonical filename scope.** The frozen `<NN>_<schema>_<table>.<ext>` convention applies **only** to the **51** files declared by the READ-ONLY `manifest v1.3` (the 8 frozen schemas), because `file_fdw` foreign tables and the **G5** `EXCEPT` integrity check bind to those exact paths. Legible names (`clients.csv`, `graph_nodes.csv`, …) are **display aliases**, not additive or replacement artefacts; the mapping is recorded in `schema_contract.json → canonical_filename_map`. **No file is renamed and `manifest v1.3` is NOT bumped**; additive CRM/vendor files remain declared by `manifest_addendum_crm.json`, with FK-safe load order in `load_order` / `schema_contract.json`. | 8 frozen schemas / 40 tables, `file_fdw` and G5 flat-file↔DB integrity all unchanged; `12_…` **§10.2** is authoritative. |

**Ruling precedence — read before any future build.** E-15 and E-16 were ratified by the lead *after* `12_…` and the first seed-pack pass, following review of the solution-architect's §7.4 and §10.2 clarifications. Where any earlier clause in this document (E-11's "every binding switch", §6.2 D-F / D-H, §6.3, §6.4 NFR-A1) could read as permitting an intra-call binding change or a frozen-filename change, **E-15 / E-16 govern**. Both rulings are also recorded in `15_Enhancement_Executive_Summary.md` §7 and are reflected in `13_Demo_Seed_Pack.md` and `demo_data/`. Separately, E-13's literal `idempotency_key = approval_token + field_mapping_version` remains the **registry-level** rule; the **physical** key appends `mapping_id` (`appr_001:fmv_20261105_1:map_01` … `map_06`) so that six accepted writes under one `appr_001` do not collapse into a single UNIQUE effect (`12_…` §4.10; FR-19 / NFR-18).

---

## 6. Architecture delta to be applied in `12_…` and `13_…`

### 6.1 Object mapping (≤10 custom properties)

| Local `crm` table (retained) | HubSpot object | Direction | Notes |
|---|---|---|---|
| `crm.crm_contact` | `contacts` | in (projection) / out (write-back) | `contact_id` ↔ `cl_wong_001`; synthetic `@demo.invalid` emails |
| `crm.crm_interaction` | activities: `notes`, `calls`, `emails`, `meetings` | in | Seeded interaction history for the brief |
| `crm.crm_task` | `tasks` | in / out | Post-Approve follow-up task |
| `crm.crm_opportunity` | `deals` (single pipeline) | in | 1 pipeline only on Free |
| `crm.crm_field_mapping` | **local only** | — | `map_01…map_08`, ≤10 custom properties, version-stamped |
| `crm.crm_sync_log` | **local only** | — | outbox, `idempotency_key`, `succeeded`/`pending`/`failed`, `http_status`, `retry_after_ms` |

### 6.2 Diagram deltas (H3 six families + one new)

- **D-A** — add `HUBSPOT FREE · DEMO SANDBOX PORTAL` labelled `REAL (SANDBOXED)` and `RETELL AI (OPTIONAL)` labelled `SIMULATED · TEST CALL`; **dashed** edge for optional Retell; a **red HARD-BLOCKED** marker on "real outbound dialling" and on "Retell → HubSpot direct write".
- **D-B** — show `IF-A01` / `IF-A02` as bindings under SVC-14; keep SVC-16 READ-ONLY / SVC-17 SOLE WRITER visually unbroken.
- **D-C** — rewrite CRM interaction: seeded old values → old→new preview (+00:14) → **HUMAN GATE / single Approve (C-3)** → REST PATCH → **read-after-write GET verify** → `crm_sync_log.succeeded` → email `draft` to Demo Sink. Add a `local_stub` fallback branch and a crossed-out "Retell auto-write" path.
- **D-D / D-E / D-F** — unchanged structurally; D-E must mark HubSpot/Retell as **external references, not new Postgres tables** (40-table freeze). D-F gains the `retell_test` branch into `transcript_utterances` with `SIMULATED` label and the `scripted_stub` fallback.
- **D-H (new)** — adapter binding state diagram: 2 adapters × 3 bindings, with the announced-switch and C-4 annotation.

### 6.3 Data additions to the seed pack (no new Postgres tables)

Add to `demo_data/` (external-reference artefacts, all synthetic): `hubspot_portal_seed.json` (synthetic contacts/deals/tasks in HubSpot object shape), `hubspot_api_exchange.json` (request/response examples with **placeholder** token, never a real credential), `crm_old_new_preview.csv` (extend with `hubspot_property`, `http_status`, `idempotency_key`), `retell_call.json` (synthetic test-call metadata + post-call webhook payload), `transcript_utterances.csv` (add `adapter_binding` column: `retell_test` | `retell_webhook_replay` | `scripted_stub` — **[E-15] run-level enum, one value per 16-utterance run, NOT a mid-call split**), `adapter_bindings.csv`, `vendor_health.csv`, and `demo_sink_messages.csv` extended with `0 real dialled calls`. `config_versions.csv` must carry the active binding per adapter.

### 6.4 Beat, NFR and exception deltas

- **+00:10** chip becomes `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)` **or** `STUB · declared (scripted transcript)`, depending on binding. `Family: daughter added …` and `confidence 0.94` at `00:03:12` are unchanged.
- **+00:16** chip becomes `Approved by Sarah (RM) · 10:14:32 · CRM write-back → sandbox portal succeeded · draft · DEMO SINK — not delivered · 0 sends, 0 trades, 0 real dialled calls`.
- **New NFR-A1…A5:** **[NFR-A1 "announced binding switch within one beat" is WITHDRAWN by E-15 — switches occur between complete runs, never inside a call]**; idempotent write-back under `429` retry (≤1 write per mapping per approval token); full offline run on `local_stub` + `scripted_stub` with reset ≤60s including sandbox re-seed by external ID; measurable zero counters; ≤10 custom properties / ≤2 seats / contacts under any published free-tier cap.
- **New X-A1…A7:** `401/403` scope failure → `local_stub`, announced; `429` → `Retry-After` backoff with no duplicate write; network/HubSpot outage → `local_stub`; Private App unavailable on the Free account → `local_stub` (**no purchase mid-demo**); Retell outage or credits exhausted → **next run** on `retell_webhook_replay` → `scripted_stub` (**[E-15] no mid-call switch**); native Retell→HubSpot integration detected enabled → **hard stop + C-4 governance-breach event**; any real dialling attempt → HARD-BLOCKED, no code path.

---

## 7. Phase A amendments by reference

- **§4 surrounding systems**, row (a) Lightweight CRM: posture changes from `STUBBED` to **`REAL (SANDBOXED)` with `STUBBED` `local_stub` fallback**; flow becomes bidirectional (inbound projection + post-Approve write-back).
- **OQ-8** default is **superseded**: Alan has chosen a real external CRM sandbox; the "labelled stubs only" default no longer applies to CRM, but **still applies** to meeting/booking/email.
- **DI-06** is upgraded: field mapping must now name `hubspot_property`, `object_type`, `writable`, `custom_property_slot` (1–10), `idempotency_key`, `transform`, `version`.
- **§7 rule 6** is extended: "no `sent` state" now also means **no real dialled call**, and a sandbox CRM write is explicitly **not** a send.

---

## 8. What Alan must decide / provide (additive to `DI-01…17`, `OQ-1…8`)

| ID | Item | Format | Priority | Default if absent |
|---|---|---|---|---|
| **DI-18** | HubSpot Free **sandbox portal** confirmation — portal/cohort/region, whether **Private Apps** are available, seat count (Free ≤2 users) | Plain text / screenshot of settings (no token) | **A** | Assume available; if not, run entirely on `local_stub` — **do not purchase** |
| **DI-19** | Private App token + scope list — **out of band**, never in repo, never in sample data | Secure channel, reference only | **A** | Placeholder `<HUBSPOT_PRIVATE_APP_TOKEN>` in all artefacts; `local_stub` binding |
| **DI-20** | HubSpot object/property map incl. which of the ≤10 custom properties, and whether `deals`/`tasks`/`meetings` are in scope | CSV schema | **A** | Synthetic `map_01…map_08`, contacts-only write-back |
| **DI-21** | Permission to show **HubSpot branding / logo** on stage (OD-7/OD-8, OQ-3) | Yes/No | **B** | No real branding; use generic framing and `HUBSPOT FREE · DEMO SANDBOX PORTAL` text |
| **DI-22** | **Retell go / no-go** + agent config (agent id, prompt, voice, language — EN or Cantonese, simulation suite) | Plain text / JSON | **A (conditional)** | Retell **OFF**; `scripted_stub` transcript |
| **DI-23** | Retell post-call webhook payload sample (transcript + structured outcome) | JSON | **B** | Synthesise a labelled `REPLAY` payload |
| **DI-24** | Consent / AI-disclosure wording, data-retention and data-residency decision **for any real call** | Plain text | **A (conditional)** | **No real calls** — only synthetic test calls |
| **DI-25** | Confirm the `0 real dialled calls` hard stop for the demo | Yes/No | **A** | **Yes** — enforced |

| ID | Open question | Default |
|---|---|---|
| **OQ-9** | Is a **real external write to a sandbox SaaS** acceptable on stage, or must every write stay in the local Demo Sink? | Permitted post-Approve, declared on stage as `REAL (SANDBOXED)` |
| **OQ-10** | Is Retell committed or optional; test-call or fully scripted? | Optional; simulation/test-call with synthetic caller |
| **OQ-11** | May HubSpot branding appear on stage? | No |
| **OQ-12** | If real calls are ever enabled: HK or SG jurisdiction, and who owns the regulatory review? | Out of scope for this MVP |
| **OQ-13** | Does the external Shariah project need a HubSpot/Retell pointer too? | No — preference-flag pointer only (E-3 unchanged) |

### 8.1 Resolved decisions (Alan — 6 Nov 2026)

The following §8 items were answered by Alan on 6 Nov 2026. Each resolution is recorded with its design impact; no frozen artefact is reopened (E-7).

| ID | Alan's decision | Design impact |
|---|---|---|
| **DI-18** | Demo only — **no plan to purchase** anything; HubSpot Free sandbox is sufficient. | Confirms the "do not purchase" default. Demo runs on the Free sandbox portal; if Private Apps are unavailable it falls back to `local_stub`. No paid tier (Data Hub Professional ~US$800/mo) is ever assumed. |
| **DI-19** | Do **not** treat the token as a blocker for the demo. | Token handling is out of scope. All artefacts keep the placeholder `<HUBSPOT_PRIVATE_APP_TOKEN>`; no real credential is created, stored, or referenced. `local_stub` binding remains valid. |
| **DI-20** | **Yes** — use the synthetic property map as designed. | Contacts-only write-back with ≤10 custom properties, synthetic `map_01…map_08`. `deals` / `tasks` / `meetings` remain out of write-back scope. |
| **DI-21** | Resolves via **OQ-11** (user indifferent) — no-branding default stands. | No real HubSpot branding/logo on stage; generic framing + `HUBSPOT FREE · DEMO SANDBOX PORTAL` text. |
| **DI-22** | **Defer Retell to MVP2**; for MVP1 it stays **OFF** (`scripted_stub`). Alan is undecided on whether Retell will ultimately be confirmed. | Retell remains optional, off the critical path. MVP1 golden path uses `scripted_stub` only; `retell_test` / `retell_webhook_replay` persist as complete-run variants (S1-R / S2) for a future MVP2 opt-in. No agent config required now. |
| **DI-25** | Demo uses **webcall only — no dial call**. | Confirms the `0 real dialled calls` hard stop (§7 rule 6). Any future Retell test (MVP2) is a browser/webcall simulation, never a phone dial. `HARD-BLOCKED`: real outbound dialling, recording of real persons, direct Retell→HubSpot writes. |
| **OQ-9** | **Yes** — write to the sandbox SaaS is acceptable on stage. | Post-Approve sandbox write-back is permitted and must be declared on stage as `REAL (SANDBOXED)`. Pre-tap = 0 writes / 0 sends; consistent with `crm_sync_log.csv` (6 succeeded writes strictly after `10:14:32`). |
| **OQ-11** | **Does not matter** — default stands. | No real HubSpot branding on stage (see DI-21). |

**Still open after round 1:** `OQ-10` (Retell optional — confirmed by the DI-22 deferral); `OQ-12` / `OQ-13` (jurisdiction / Shariah pointer — out of scope). `Q2` remains confirm-only (Q1 = OD-1 resolved in §8.2; Q3 answered in §8.3). `DI-23` / `DI-24` are **in scope** per round 3 (§8.3), no longer deferred.

### 8.2 Resolved decisions — round 2 (Alan — 6 Nov 2026)

| ID | Alan's decision | Design impact / new open sub-item |
|---|---|---|
| **OD-1 / Q1** | **Use the Tiger Brokers paper-trading API as the live market source.** | `<source>` placeholder is replaced by `source_id = tiger_open_api`. Tiger's paper-trading feed delivers **real-time market quotes** (no real orders), so the `LIVE` headline becomes genuinely achievable under OD-5. Vendor name stays internal only (see OD-8). **Refined in §8.3:** Tiger is **data-only** — Alan provides the API and Tiger is **never named on stage**; the audience-facing `ModeChip` stays generic (`LIVE · market data`). |
| **OD-7** | (Resolved via OD-1) | The `<source>` placeholder now resolves to `tiger_open_api`; no further decision needed. |
| **OD-5 / Q6** | **Implement all three bars of the "live" test.** | (i) real external `source_id` (`tiger_open_api`) + cross-checkable wall-clock `as_of`; (ii) event is non-pre-scripted when bound to the live feed, or explicitly labelled `REPLAY` on the replay binding; (iii) permanent audience-visible `ModeChip`; G8 DB `CHECK` blocks `LIVE` while bound to `replay_stream`. |
| **OD-8** | **No vendor name / logo on stage.** | Generic framing only; `source_id` is honest internally but no Tiger branding is shown. Consistent with DI-21/OQ-11. |
| **OQ-1 / DI-01 / E-2** | **"Booking" = appointment / meeting booking (reading i).** | CRM/calendar/order dataset shape = appointment/meeting booking. Readings (ii) trade/order booking and (iii) booking entity/centre remain documented-only and out of write-back scope (no collision with HARD-BLOCKED trade execution). |
| **OD-4 / Q5** | **Real microphone / ASR accepted**; user will provide an **ElevenLabs API** key. | Demo may capture real RM voice. **Round-2 flag corrected in §8.3:** ElevenLabs now ships **Speech-to-Text** (`https://elevenlabs.io/app/speech-to-text`), so it covers **both ASR (input) and TTS (output)** — single vendor for voice in+out; the earlier "ASR/STT provider unidentified" sub-item is resolved. Real recording triggers PRD §14.1 consent/retention work — but only the RM is the live human (scope note), so recording the RM's own voice in a controlled demo is lower-risk; still surface a consent chip. API key held as placeholder `<ELEVENLABS_API_KEY>`; no code written. |
| **OD-6** | **Single screen only — NO dual-output hardware.** | The off-camera operator console is dropped; the presenter-safe hotkey overlay becomes the **baseline**. Operator controls (binding selection, go/no-go, reset) are a same-screen panel. `FU-19…21` scope simplifies accordingly. |
| **OQ-4 / DI-04 / A2** | **Multi-currency: support HKD, SGD, USD.** | Resolves the earlier SGD-vs-HK tension. **New sub-item:** the current seed pack is SGD/SGT-centric; a **seed-data amendment** is needed to add HKD and USD accounts/holdings (still design-only until build). Demo clock stays `SGT` with multi-currency AUM. |
| **OQ-5 / DI-13 / OD-9** | **Keep the family-graph range beat.** | FR-24 stays as the single range moment with a one-click jump; FR-25 is first-to-cut if time pressure. |
| **Relationship graph** | "Could be a Postgres graph plugin." | **Design note (not a hard decision):** evaluate a Postgres graph extension (e.g., Apache AGE) for D5 at build time. Current design uses relational `graph_nodes` / `graph_edges` + SVC-06 context assembly and remains valid; this interacts with Q2 (Postgres plugin interpretation) and is additive. Logged for `FU-17/18`. |
| **Scope (positioning)** | Purpose = demonstrate a **next-generation RM workbench and how it uses AI**; the **ONLY human user is the Relationship Manager**. | No client-facing UI; the client is represented by synthetic data / simulation only. This reinforces the single-screen (OD-6) and RM-centric design and explains the Retell→MVP2 deferral (no live client voice agent in MVP1). Recorded in `15_…` §1. |

**New open sub-items raised by round 2:** (a) Tiger written display clearance; (b) ASR/STT provider for real RM voice (ElevenLabs is TTS only); (c) seed-data multi-currency (HKD/USD) amendment. All three are build-phase items; none blocks the current design.

### 8.3 Resolved decisions — round 3 (Alan — 6 Nov 2026)

| ID | Alan's decision | Design impact |
|---|---|---|
| **Q3** | **The generator is a program that produces the demo data; ALL demo data is AI-generated.** | Reconciles the earlier "deterministic one-seed operator tool" framing: the generator may use an LLM to synthesise realistic records. Provenance label should read **`SYNTHETIC DEMO DATA · AI-GENERATED`** (in addition to the C-1 envelope). For demo reproducibility the AI generation runs once and is **frozen** — the demo replays the frozen output deterministically (no live LLM call on stage). `demo_data/` remains the *specified output shape*; the actual generator is AI-based. |
| **OD-1 / OD-8 (refinement)** | **Tiger = data-only source; do NOT show/label Tiger on stage.** Alan will provide the API. | Tiger supplies live market quotes via the API Alan provides; `source_id = tiger_open_api` is honest *internally* (provenance/audit) but the audience-facing `ModeChip` stays generic (e.g., `LIVE · market data`), with no Tiger name/logo. The earlier "written display clearance" sub-item is **downgraded** — since Tiger is never named on stage, clearance is moot for the demo (API terms-of-use still apply off-stage). |
| **OD-4 / ElevenLabs (correction)** | **Use ElevenLabs for ASR too** — `https://elevenlabs.io/app/speech-to-text`. | Corrects the round-2 flag: ElevenLabs now ships **Speech-to-Text**, so it covers **both ASR (input) and TTS (output)** — single vendor for voice in+out. The round-2 "ASR/STT provider unidentified" sub-item is **resolved** (ElevenLabs Speech-to-Text). API key placeholder `<ELEVENLABS_API_KEY>`; real RM voice is captured, transcribed (STT) and synthesised (TTS); consent chip still surfaced (PRD §14.1, lower-risk because only the RM is the live human). |
| **DI-23 / DI-24** | **Include in scope (no longer deferred to MVP2).** | The Retell post-call webhook payload sample and the consent / AI-disclosure wording are now **designed in the current scope**. The Retell *agent runtime* itself remains optional/off-critical-path (DI-22), but its supporting artefacts are produced now. Updates `14_…` §8.1 still-open list. |

**Net open-sub-item status after round 3:** (a) Tiger written display clearance — **moot** (data-only, no on-stage name); (b) ASR/STT provider — **resolved** (ElevenLabs Speech-to-Text); (c) seed-data multi-currency (HKD/USD) amendment — **confirmed, build-phase** (see §8.4). The Retell *runtime* (DI-22) remains optional; `Q2` ratified in §8.4.

### 8.4 Final ratifications (Alan — 6 Nov 2026)

| ID | Ratification | Design impact |
|---|---|---|
| **Q2 / OD-2** | **Ratified: "Postgres plugin" = Postgres extensions** — TimescaleDB + `file_fdw` (pgvector deferred). The IDE-connector / BI-plugin readings are rejected for the DDL/interface contracts. | No change to `03` §5 / §7; the console display field (if either reading was meant) stays a UI note only. `manifest v1.3` / `schema v1.3` already encode this. |
| **OD-3 / Q4 / OQ-7** | **Ratified: NO real client data, ever — 100% synthetic.** | Confirms the standing assumption (A1). A "yes" would reopen Phase 1; it is locked to **No**. All `SYNTHETIC DEMO DATA` / `AI-GENERATED` labels stand. |
| **(c) Multi-currency seed amendment** | **Confirmed required.** | The generator (Q3, AI-based) must emit multi-currency books — HKD, SGD, USD accounts / holdings / AUM — not only the current SGD/SGT-centric `demo_data/`. This is the **single remaining build-phase data task**; it changes no frozen schema/contract, only generated row content. Execution (editing `accounts.csv` / `holdings.csv` / `allocation_targets.csv` + re-cascading `dataset_checksum` / `pack_checksum_52` / 52 SHA-256) is deferred to the build phase / generator run, consistent with the design-only posture. |

**Status after §8.4:** every open decision from the base package (`Q1…Q3`, `OD-1…11`), the enhancement intake (`DI-01…25`, `OQ-1…13`) and the vendor ruling is now **resolved or explicitly scoped**. The only outstanding *build-phase* work is: (c) the multi-currency seed amendment, and (optionally) the Retell *runtime* (DI-22, still optional). **No open *design* decision remains.**

---

## 9. Cost, vendor dependence and go/no-go

| Item | Cost | Risk |
|---|---|---|
| HubSpot Free | US$0 | Cohort-dependent caps; Private App may be unavailable; branding; **no webhook automation** |
| Retell AI | US$10 free credits, then ~US$0.07–0.31/min (all-in ~US$0.11–0.15/min with LLM + TTS) | Finite credits, network dependence, per-minute billing, regulatory exposure on real calls |
| **No paid tier is required or assumed** | US$0 | Data/Operations Hub Professional (~US$800/month) is explicitly **out of scope** |

**Go/no-go before the leadership demo:** (1) sandbox portal reachable + Private App token valid; (2) ≤10-property mapping loaded; (3) read-after-write verification passes; (4) `local_stub` + `scripted_stub` offline rehearsal passes with reset ≤60s; (5) native Retell→HubSpot integration confirmed OFF; (6) zero counters verified; (7) `SYNTHETIC DEMO DATA` visible to the last frame. **If any of 1–3 fail, run the entire demo on the offline bindings — the journey is unchanged, only the honesty chip changes.**

---

## 10. Contract-freeze compliance (E-7)

**Unchanged:** 8 schemas / 40 `CREATE TABLE` specifications; `IF-01…22`; `EV-01…20`; `SVC-01…18`; `DF-01…06`; `NFR-1…18`; `ADR-01…08`; extension set {TimescaleDB, `file_fdw`}; `manifest v1.3` / `schema v1.3`; honesty taxonomy; `0 sends / 0 trades`; no trade-execution table, endpoint or code path; AppLive/Replay separation and the G8 DB `CHECK`.

**Additive, architect-authored, sync to Phase 4:** `IF-A01`, `IF-A02`, `EV-A01…`, `NFR-A1…5`, `X-A1…7`, `D-H`, `DI-18…25`, `OQ-9…13`, E-9…E-16. **`manifest v1.3` is NOT bumped** — no silent version change; any future bump requires an explicit re-freeze note. Phase 4 FU cards affected by a delta: FU-01 (DDL + ext — additive `crm` projection columns), FU-08 (generator baseline — vendor seed + replay payloads), FU-17/18 (edges/UI — binding chips), FU-19…21 (operator console — announced **between-run** binding selection + go/no-go).

---

## 11. Source traceability

All web sources above were retrieved **6 Nov 2026**. Grades: `[EVIDENCE · first-party]` = vendor's own documentation or pricing page; `[EVIDENCE · first-party claim]` = vendor compliance marketing, not independently audited here; `[EVIDENCE · vendor-adjacent]` / `[secondary analysis]` / `[third-party survey]` = requires primary verification before any compliance decision; `[CONFLICTING]` = sources disagree, design uses the intersection; `[INFERENCE]` = lead reasoning, challengeable, not a fact; `[ASSUMPTION]` = default adopted pending Alan's confirmation (§8).

Frozen internal references: `10_Data_Enhancement_Brief.md` (E-1…E-8), `11_Demo_Data_Requirements_and_Intake.md` (DDR-01…26, DI-01…17, OQ-1…8), `03_Technical_Solution.md` (§4.1, §5, §7, §8, §12), `04_Feature_Unit_Plan.md` §9, `RM_Workbench_MVP_Design_Package.md`.

---

*Design only — no code has been written, no vendor account has been opened, and no credentials have been created.*

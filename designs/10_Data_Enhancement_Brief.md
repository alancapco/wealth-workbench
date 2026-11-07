# Enhancement Brief — Demo Data, Systems & Diagrams

**Engagement:** Addendum to the *Next-Generation RM Workbench — MVP Design Package* (5 Nov 2026).
**Owner:** Qi Huolin (Delivery Director), software-dev-team.
**Output language:** English.
**Status:** DESIGN ONLY — Alan's "i dont want you do write code yet" remains in force.

---

## 1. Alan's new request (verbatim)

> "i think you need to enhance, as i said, i need to use a generator to generate some fake data to populate for a demo, the firtst MVP should be demo to our company's leader about the journey that we envision, so data is important, i need you to show me diagram as well on archicture and also on coponent and systesm, for example CRM, you may need to have a very lightweight CRM built with a few table, so i can visualize how the workbench interact with it, i do have another project that that sharia , you also need to sample the relationship graph too , you may be able to show meeting , and also booking , or email, which i can provide later, but you have to suggest to me what you need"

## 2. Gap analysis — be critical

The existing package designs the generator as a **mechanism** (deterministic seed → flat files → one-transaction Postgres load → integrity validation → reset). It does **not** make the *data* visible. For a leadership-journey demo that is a material gap:

| Gap | Where it shows | Consequence |
|---|---|---|
| No concrete fake records | Phase 3 §7 specifies the algorithm and manifest, but no sample client/holding/interaction rows | Alan cannot "see" the demo world; the journey is abstract |
| No lightweight CRM | Phase 3 has `client.crm_record` and `artefact.demo_sink_message`, but **no CRM as a system** with its own few tables | "How does the workbench interact with CRM?" is unanswerable visually |
| Relationship graph topology not frozen | Phase 2 §13.5(b) and Phase 4 §9 explicitly flag this as *the clearest gap* — A7 says "seeded 4–6 nodes" but no node list/edges/topology exists | The range beat and node-level entitlement proof (G7) have nothing concrete to render |
| Meeting / booking / email systems absent as external systems | Only stubs; no sample records, no interaction diagram | The demo cannot show a realistic RM day across systems |
| Shariah project treated as an out-of-scope flag only | FR-25 is P1/flag-OFF | Alan has another Shariah project; no integration/data boundary is specified |
| No system-context or component diagrams for the *data* landscape | Phase 3 §2/§3 has C4 and dataflow diagrams, but no "CRM + meeting + booking + email + market feed + Shariah project" system context | Leadership cannot visualise the ecosystem |
| No explicit "what Alan must provide" list | Phase 4 §6(f) has go/no-go decisions, not a data intake list | Alan asked for this directly |

**This addendum closes all seven.** It does not reopen frozen product design, requirements or interface contracts; it *adds concrete data and the surrounding-system view*.

## 3. Hard constraints

| ID | Constraint |
|---|---|
| H1 | **No application code.** No generator implementation, no executable scripts, no scaffold, no build commands. DDL, JSON/CSV sample rows, Mermaid and config examples are **specification and data artefacts**, allowed and expected. |
| H2 | **Sample CSV/JSON rows are DATA, not code.** They are the *specified output shape* of the generator — a preview of the seeded world — not a running generator and not a production migration. Every file must be labelled synthetic. |
| H3 | Deliverables must include **diagrams**: (a) system/context architecture, (b) component/systems view, (c) CRM interaction, (d) sampled relationship graph, (e) demo-data entity landscape, (f) meeting/booking/email interaction. Mermaid in the documents; selected ones also rendered inline for Alan. |
| H4 | All data **100% synthetic**, deterministic from one seed, C-1 provenance envelope on every fact, permanent `SYNTHETIC DEMO DATA` posture. No real PII (A1, OD-3). |
| H5 | Purpose: **demo the envisioned journey to company leaders**. Data must be realistic enough to be credible, small enough to be legible, and traceable to a source chip at every beat. |
| H6 | Alan must receive an explicit, critical **data intake request list** — what he should provide later, in what format, with minimum fields, and what happens if he does not. |

## 4. Lead decisions (ratified — design against, do not re-litigate)

| ID | Decision |
|---|---|
| **E-1** | **No new product-design phase.** Phase 2 (SCR-01…14, CMP-01…16, ST states) is frozen and no new screens are introduced. Re-running product design would duplicate frozen output and violates global rule 1. The **journey → concrete data map** is therefore assigned to the architect, not a new designer phase. |
| **E-2** | **"Booking" is ambiguous.** Three readings: (i) client **appointment / meeting booking** (calendar), (ii) **trade / order booking** (back office), (iii) **booking entity / booking centre** (where an account is booked). Primary design = (i) appointment booking, because it sits on the meeting journey; (ii) and (iii) must be documented as alternates and put on the intake list for Alan to confirm. Do not silently pick one. |
| **E-3** | **Shariah is an EXTERNAL project.** This MVP must not rebuild screening, zakat, purification or SSB rule packs. FR-25 remains P1/flag-OFF. Specify an *optional* integration boundary (what the external project could expose: screening status per instrument, rule-pack version, preference flag) and add it to the intake list. Note that the relationship graph sample may carry a Shariah-sensitivity preference as a node attribute, pointing to that project — not implementing it. |
| **E-4** | **The lightweight CRM is a demo stand-in system**, not a real CRM integration. It must be visibly labelled `DEMO CRM (lightweight)` and remain inside the single Postgres instance (recommend a distinct `crm` schema so the boundary is visible in diagrams and DDL). "A few tables" = 5–7, no more; every table needs a stated purpose. Real CRM remains a stub/demo sink per the frozen honesty posture. |
| **E-5** | **The relationship graph sample CLOSES the flagged gap**: produce concrete nodes, edges, source-document refs, an entitlement matrix, and two per-attendee entitled pack views. 6–7 nodes, no more. Do not invent a "canonical Tan family" as if it were research — label it a synthetic seed. |
| **E-6** | **Data volume stays demo-scale.** A few dozen clients, a few hundred holdings, a handful of meetings/emails/ticks per scenario. Enough to make the journey credible; small enough to display and reset in ≤60s (NFR-9). |
| **E-7** | Frozen artefacts from `03_Technical_Solution.md` remain frozen: 8 schemas / 40 tables, `IF-01…22`, `EV-01…20`, `manifest v1.3`, `schema v1.3`, extension set {TimescaleDB, file_fdw}, `NFR-1…18`. The new `crm` schema and any new sample tables are **additive specification**, flagged as an architect-authored extension that syncs to Phase 4. `manifest v1.3` must NOT be silently bumped — a change requires an explicit re-freeze note. |
| **E-8** | The three Q1/Q2/Q3 ambiguities and OD-1…11 from the base package remain open and are **not** resolved by this addendum. |

## 5. Deliverable plan

| Phase | Owner | Output |
|---|---|---|
| A | `req-analyst` | 《Demo Data Requirements & Data Intake Specification》 — what fake data must exist for the leadership journey, which systems it comes from, and **the concrete list of what Alan must provide later** (format, minimum fields, volume, anonymisation, default synthetic stand-in if absent) |
| B | `solution-architect` | 《Demo Data & Systems Architecture Enhancement》 — all six diagram families, lightweight CRM DDL + sample rows + interaction dataflow, sampled relationship graph, generator seed pack with concrete synthetic rows across entities, meeting/booking/email system context, Shariah external boundary, journey → data map, and the sample data files |
| C | team lead | Assemble addendum, render inline diagrams, update the base package with a short pointer, deliver |

## 6. Frozen context to reuse (read the files; do not re-derive)

- `deliverables/00_Shared_Design_Brief.md` — base brief, PRD digest, demo narrative.
- `deliverables/01_Requirements_Specification.md` — `MVP-FR-01…34`, `C-1…5`, `X-01…20`, `G1…G11`, `D1…D10`, `A1…A7`, `Q1…Q7`, `S1…S4`, `F1/F2`, §5.1 golden path.
- `deliverables/02_Product_Design_Specification.md` — `SCR-01…14`, `CMP-01…16`, `ST-…`, §8 generator UX, §13.5(b) **entity-graph topology gap**.
- `deliverables/03_Technical_Solution.md` — **THE FREEZE LINE**: `ADR-01…08`, `SVC-01…18`, `DF-01…06`, 40 tables / 8 schemas, `IF-01…22`, `EV-01…20`, `NFR-1…18`, §7 generator, §5 extension decision.
- `deliverables/04_Feature_Unit_Plan.md` — `FU-01…24`, §9 **"entity graph topology is the clearest gap"**, §5 run-of-show, §6(f) go/no-go.
- `deliverables/RM_Workbench_MVP_Design_Package.md` — consolidated executive entry point.

**Key frozen facts:** single Postgres 16 instance; C-1 provenance envelope (7 columns) on every fact; two BFFs (Presenter READ-ONLY, Operator SOLE WRITER); extension set {TimescaleDB, file_fdw}; generator is deterministic from one seed with `manifest v1.3`; honesty posture REAL/SIMULATED/STUBBED/HARD-BLOCKED; trade execution has no table/endpoint/code path; golden path tick +00:00 → re-rank +00:06 → brief +00:08 → consent/scripted capture +00:10 → one review +00:14 → single Approve +00:16 → loop closes +00:18 → optional range beat +00:20.

## 7. Four global rules

1. **Simplicity over redundancy** — no duplicate implementations, no over-abstraction, minimum viable design; do not re-run frozen phases (E-1).
2. **Annotations only at non-obvious WHY points** — no filler; any future code comments must be Chinese.
3. **Contract freeze** — additive schema/contract changes are architect-authored and sync to Phase 4; `manifest v1.3` is not silently bumped.
4. **Everything delivered lands on disk** — documents and sample data under `deliverables/`.

---

## 8. AMENDMENT — Vendor adapters (ratified 6 Nov 2026)

**Trigger (Alan, verbatim):** *"for CRM, i plan to use hubspot free as the demo, i may use retell.ai as an agent , please plan this in"*

**Authoritative ruling:** `deliverables/14_Vendor_Adapter_Ruling_HubSpot_Retell.md` — **read it in full before writing anything.** It contains the evidence register (HubSpot Free / Retell AI), Hong Kong & Singapore governance context, the architecture delta, Phase A amendments, `DI-18…25`, `OQ-9…13`, cost/go-no-go, and the contract-freeze note.

| ID | Ratified decision | Supersedes |
|---|---|---|
| **E-9** | HubSpot Free = **primary external CRM binding**, dedicated **sandbox portal** with 100% synthetic records. The 6-table `crm` schema is **retained, re-purposed** as **CRM ADAPTER · LOCAL PROJECTION** (projection + field mapping + idempotency/outbox ledger), not the CRM itself. External label `HUBSPOT FREE · DEMO SANDBOX PORTAL`. | **Amends E-4** |
| **E-10** | Four frozen honesty categories **unchanged**; add qualifier **`REAL (SANDBOXED)`** = real vendor service + synthetic records + no real person contacted. New counters: **0 real dialled calls, 0 real client-facing sends, 0 real PII**. A post-Approve sandbox CRM write is permitted and must be declared on stage; it is **not** a "send". | Extends honesty posture |
| **E-11** | Additive `IF-A01` (CRM adapter) / `IF-A02` (voice adapter), three announced bindings each: `hubspot_free` → `local_stub` → `demo_sink` and `retell_test` → `retell_webhook_replay` → `scripted_stub`. **No new SVC IDs**; `IF-01…22` / `EV-01…20` NOT renumbered. Every switch announced + C-4. | Extends IF/EV |
| **E-12** | **Retell native HubSpot integration MUST be OFF.** Retell produces only transcript + extraction candidates; all writes route through the single C-3 `appr_001` after human Approve. No CRM auto-write, no real outbound call, no workflow trigger. | Protects G2/G3 |
| **E-13** | **No dependency on inbound HubSpot webhooks** (Free-tier availability contested; workflow webhooks need ~US$800/mo Professional). Use outbound REST + **read-after-write GET verification**, `crm_sync_log` + `idempotency_key` for `429 Retry-After`. **≤10 custom properties**; all orchestration stays in the workbench. | Extends NFR-18 |
| **E-14** | Retell is **OPTIONAL / off the critical path** ("may"). Default transcript = **Retell simulation/test call with a synthetic caller**, posture `SIMULATED (Retell test call · synthetic caller · 0 real dialled calls)`. Golden path MUST also run on `scripted_stub` / `retell_webhook_replay`. **HARD-BLOCKED:** real dialling, recording real persons, direct Retell→HubSpot writes. | Extends F1/replay |

**Binding consequences for Phase B writers:** `12_…` must add the two external nodes to D-A/D-B, rewrite D-C as REST write-back + read-after-write verification with a `local_stub` branch, add the `retell_test` branch to D-F, add new D-H (binding state), and mark HubSpot/Retell as **external references, not new Postgres tables**. `13_…` must add the vendor seed/exchange/replay artefacts listed in `14_…` §6.3 and the `adapter_binding` column. **E-1, E-2, E-3, E-5, E-6, E-7, E-8 remain in force**; `manifest v1.3` is **NOT** bumped.

*This amendment is DESIGN ONLY — no code, no credentials, no vendor account.*

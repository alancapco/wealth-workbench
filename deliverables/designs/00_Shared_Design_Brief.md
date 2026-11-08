# Shared Design Brief — Next-Generation RM Workbench MVP

**Engagement type:** DESIGN ONLY. No application code, no executing system.
**Audience for the design:** Alan (Capco, CTO advisor) and senior leadership of a wealth-management client.
**Output language:** English.
**Owner:** Qi Huolin (Delivery Director), software-dev-team.

---

## 1. Source material (authoritative)

| File | Role |
|---|---|
| `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_PRD.md` | PRD v1.1 — 14 sections, 12-month V1 roadmap, 22 functional requirements. **Authoritative source.** |
| `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_PRD.docx` | Same PRD in Word form (verified: identical 14 sections, FR-22, Epic 5) with Mermaid diagrams rendered as images. |
| `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_AI_Copilot_and_Niche_Expansions.md` | v1.1 enhancement pack — five-layer copilot architecture, Epic 4 (Islamic wealth), Epic 5 (family office). |
| `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_Product_Strategy_Package.md` | Strategy, personas, RICE, KPIs, roadmap, resource envelope. |
| `/Users/alanyoung/Documents/Capco/Wealth/RM_Workbench_Video_Treatment.md` | "The Future RM" demo narrative — the reference storyboard for a senior-leader demo. |

## 2. User request (verbatim)

> "please base on my draft prd, i want your design frist, make it a MVP, but it would integrate live market data, and you need to plan a gnerator of file / database, try to use postgres and postgres plugin for your design, i dont want you do write code yet, but design the funcitonal spec, non function requirement, component and dataflow first, i think the function need to be a bit elaborated, and this is for demoing the next generation of RM workbench to senior leader"

## 3. Hard requirements

| ID | Requirement |
|---|---|
| R1 | **Design first.** No implementation code. Schema/DDL and interface contracts as *specification* are required; illustrative SQL is allowed; no runnable application, no scripts to be shipped. |
| R2 | Deliverables: **(a) Functional Specification — elaborated / detailed**; **(b) Non-Functional Requirements**; **(c) Component design**; **(d) Dataflow**. |
| R3 | Carve a coherent **MVP** out of the PRD's 12-month V1 plan. |
| R4 | MVP **must integrate live market data**. |
| R5 | **Must plan a file / database generator** — a generator that produces flat files *and* populates a database. |
| R6 | Use **Postgres and a Postgres plugin/extension** in the design; explicitly justify the choice. |
| R7 | Purpose is **demoing the next generation of the RM Workbench to senior leaders** — credible, end-to-end, reproducible, visually provable. |

## 4. PRD digest

- **Vision / product principle:** "The AI copilot that orchestrates the entire wealth advisory day — one client memory, every workflow, human-approved." AI prepares, ranks, drafts and explains; the RM reviews and approves every client-facing or system-writing action. Locked tagline: *"AI orchestrates the workflow. You orchestrate the relationship."*
- **Five-layer architecture:** L1 Experience (one copilot surface, "My Day", proactive cards); L2 Orchestration / Copilot Core (intent → decomposition → skill sequencing → policy checks → human approval gates → execution verify); L3 Context / D5 Client Memory & Relationship Graph (preferences, family/entity graph, meeting history, commitments, consent, suitability state — every fact evidence-backed with source + timestamp + confidence); L4 Skills (`brief.generate`, `meeting.capture`, `actions.extract`, `crm.write`, `rank.clients`, `outreach.draft`, `product.search`, `suitability.check`, `shariah.screen`, `zakat.calculate`, `household.consolidate`, `entity.map`); L5 Trust (policy packs, citations & audit, multi-model router, eval harness, kill switch, zero provider retention).
- **Closed loop:** meeting outcomes feed ranking → ranking drives next briefs → briefs carry latest preferences. *This loop is the product.* Measured by cross-skill task completion (≥85% without manual stitching) and context reuse, not chat volume.
- **Personas:** Senior Private Wealth RM (50–150 HNWI clients, $50M–$500M AUM); Mass Affluent RM (100–300 clients, $20K–$2M each). Customers: banks with 1,000–10,000 RMs.
- **Epics:** E1 Meeting Intelligence (P0: 1.1 pre-meeting brief, 1.2 consented transcription/notes, 1.3 post-meeting automation); E2 Prioritization & Outreach (P0: 2.1 daily Top 10 with Risk/Opportunity/Retention reason codes and evidence, 2.2 grounded outreach drafts with approved send); E3 Product Recommendation (P1: 3.1 NL product search, 3.2 Red/Yellow/Green suitability pre-screen); E4 Islamic Wealth (P1 pilot: Shariah screening, zakat, evidence packs — copilot is a calculation/evidence assistant, **never a fatwa issuer**); E5 Family Office (P1/P2: entity graph, household consolidation, intra-family node-level entitlements, succession).
- **FR-01…FR-22**, each with acceptance criteria. Cross-cutting: FR-20 universal human review; FR-21 mobile parity for defined tasks; FR-22 admin configuration without code deployment.
- **Boundary behaviour (PRD §6):** partial data shown with per-section status/as-of, never invented; conflicting records flag and block suitability/trade handoff; consent withdrawn stops capture; low confidence → explicit review and suppressed client-facing assertions; CRM/email/SMS outage preserves editable draft with visible pending/failed status and idempotent retry, never false success; no high-priority clients → empty state, do not pad Top 10; DNC/channel opt-out blocks send; no suitable product → no-result, never auto-relax a hard filter; missing/expired suitability → Yellow at best and blocks ticket handoff; model failure → manual fallback; Shariah-sensitive client + non-compliant candidate → exclude by construction; intra-family entitlement enforced **in copilot context assembly**, not only UI.
- **NFR baseline (PRD §7):** brief <10s p95, product search <5s p95, 1,000 concurrent users, 99.5% monthly uptime, SOC 2 target, TLS + strong encryption at rest, enterprise RBAC/least privilege/tenant isolation/session timeout/secrets management, EU/US/APAC (+GCC/MY/ID) residency, immutable tamper-evident audit, AI explainability (no private chain-of-thought), mobile parity, WCAG 2.1 AA, correlated telemetry with PII minimisation, backup/restore & DR.
- **AI governance (PRD §8):** mandatory human-in-the-loop; zero provider retention/training; grounding with faithful summaries; override & feedback with structured reasons; versioned models/prompts/templates/ranking policies/rule packs with eval before release and rollback; compliance ownership of consent/disclosures/suitability; monitoring + kill switch; no protected attributes in ranking and data minimisation.
- **Integrations (PRD §9):** core banking (client identity, households, accounts, balances — authoritative IDs + as-of); portfolio management (holdings, allocation, performance, risk); **market data (prices, news, licensed fundamentals — entitlements, attribution, source timestamps; feed unavailability must not block unrelated sections)**; CRM (bidirectional, configurable field mapping, old/new preview, idempotent writes, visible sync status); calendar (least-privilege scopes, ambiguous attendee matching requires user resolution); email/SMS (draft handoff + RM-approved send); product/suitability source; Shariah rule data; custodian/entity sources; identity/SSO.
- **Out of scope (PRD §12):** full financial planning, alternatives marketplace, client portal, autonomous advice / client sends / trade execution, issuing fatwas, general-purpose chatbot, automatic model training on client/RM data.
- **Open decisions (PRD §14):** transcription platforms/languages/consent; CRM/email/calendar targets and write ownership; ranking objective weights and meaningful-touchpoint definition; product universe + market-data entitlements + suitability rule owner + hard-stop matrix; Shariah design partner; entity coverage + entitlement matrix; retention measurement method; mobile policy.

## 5. Reference demo narrative (from the video treatment)

4-minute "Day in the Life" film, Singapore private bank, RM "Sarah":

- **Act 1 (0:00–0:25):** fragmented old way — `45 minutes to prepare. 5 systems. 1 client.`; a client need gets referred away ("Not really my area").
- **Act 2, Seq 1 (0:25–1:00), 7:45 AM:** "My Day" assembles itself — "3 meetings today. Wong 10:00 — brief ready: portfolio drifted 6% from target; rebalancing options aligned to his preferences. Rahman 13:00 — annual review; faith-based preferences and annual giving summary prepared. Tan family 15:30 — multi-generational review." Every section carries a **source chip**. Proactive card: "2 clients flagged for retention risk — outreach drafts queued."
- **Act 2, Seq 2 (1:00–1:55), 10:00 AM:** consent banner → recording indicator; Wong says "next time my daughter should join" → memory chip `Family: daughter added · preference noted`; meeting ends → **one review screen** (notes, CRM updates, follow-up email, rebalancing proposal, tomorrow's re-ranked priority list) → edit two lines → **Approve**. `45 min prep → 5. 20 min admin → 4.`
- **Act 2, Seq 3 (1:55–3:05):** faith-based investing served with confidence (`Screened to client's stated standard · methodology disclosed`, "Estimate for discussion" label); family entity graph unfolding into a consolidated view and a meeting pack split into per-attendee entitled versions.
- **Act 3 (3:05–4:00):** `AI orchestrates the workflow. You orchestrate the relationship.` / `Human-approved. Always.`

**Non-negotiable UI rules for a banking audience:** every AI statement shows a source/timestamp chip; every outbound action shows a human tap; the consent banner, approval taps and "estimate for discussion" label never get cut.

## 6. Demo-specific framing

1. The single most persuasive proof point is a **live market event entering the system and propagating through the closed loop within seconds**, with visible provenance chips and a human approval gate.
2. **Reproducibility:** a stage demo must be repeatable without network/provider risk → design a deterministic **replay mode alongside a genuine live mode**, with an explicit, honest label of which is running.
3. Include at least one lightweight **"range" moment** (Shariah preference or family entity graph) to match the narrative payoff — but do not let niche scope sink the MVP.
4. Be explicit about **what is simulated vs. real** and what is out of MVP scope. Senior leaders will probe this.

## 7. Open assumptions — state them, do not block on them

- **Live market data source:** not named by the user. Evaluate realistic options (licensed vendor e.g. Bloomberg / LSEG Refinitiv / Wind; exchange or delayed public feed; vendor sandbox), covering entitlement, cost, latency and attribution, and recommend a primary + fallback appropriate to a HK/Singapore banking demo.
- **"Postgres plugin":** interpret as Postgres extensions. Evaluate at minimum **TimescaleDB** (time-series market ticks / continuous aggregates), **pgvector** (client memory + grounded semantic retrieval), **pg_cron** (scheduled refresh / materialisation), and **file_fdw / postgres_fdw** (flat-file ingestion). Recommend a *minimal* justified set. Also consider whether a WorkBuddy/IDE Postgres connector or a BI/visualisation plugin is what the user meant — note the interpretation explicitly.
- **"Generator of file / database":** design a deterministic **demo data fabric** that emits flat files (CSV / JSON / Parquet) plus a manifest and schema contract AND loads Postgres; supports `seed` / `replay` / `live` modes; guarantees referential integrity, as-of timestamps and provenance on every fact; reproducible from a single seed.

## 8. Four global rules (apply to every deliverable)

1. **Simplicity over redundancy.** No duplicate implementations, no over-abstraction, no unused components. Reuse common modules. Minimum viable design.
2. **Annotations only at non-obvious points** — core logic, algorithms, boundary handling, error-prone areas — explaining *why*, never line-by-line filler. (When code eventually exists, comments must be in Chinese.)
3. **Contract freeze.** Data model and interface contracts are frozen before any build; changes must go through the architect and be synced to all affected parties. State this explicitly in the design.
4. **Everything delivered lands on disk.** Documents in `deliverables/`; code in the project directory. For this design-only engagement, all design documents must be persisted.

## 9. Team process

Phase 1 Requirements (`req-analyst`) → Phase 2 Product Design (`product-designer`) → Phase 3 Technical Solution / Components / Dataflow / NFRs (`solution-architect`) → Phase 4 Feature Unit Plan (`feature-planner`) → Phase N consolidated delivery. Each phase receives the **full verbatim output** of all prior phases through the team lead. No peer-to-peer direct communication. **Stop before any build work — the user has explicitly asked for design only.**

# RM Workbench — Product Requirements Document (Refreshed)

**Version:** 3.0  
**Date:** 8 November 2026  
**Audience:** Business leadership, product, relationship management leadership, compliance  
**Status:** Current baseline — what the product is, what it does today, what comes next  
**Scope note:** This document covers product intent, capability, priority and roadmap. Technical architecture, data engineering and integration design are handled separately by the engineering team.

---

## How to read this document

**In one line:** RM Workbench is a digital assistant that gives a relationship manager one place to prepare for, advise on, and follow up with every client in their book.

**What you will find here**

| Section | Answers |
|---------|---------|
| 1. Executive summary | What the product is, what is working today, what we are asking for |
| 2. The business case | Why we are building this and what it is worth |
| 3. Who it serves | The people using it and the jobs they need done |
| 4. How it works | The shape of a relationship manager's day with the product |
| 5. Product capability | Every capability area in plain language, with its status |
| 6. Delivery against the brief | What you asked for, item by item, with status |
| 7. What remains | The rest of the scope, grouped by theme |
| 8. Roadmap | Three horizons with sequencing logic |
| 9. Value case | What good looks like, and how we will know |
| 10. Dependencies and approvals | What we need from legal, compliance, and third parties |
| 11. Decisions requested | The five choices we need from you |
| 12. Assumptions and boundaries | What this release deliberately does not do |
| 13. Glossary | Plain-language definitions |

**Status labels used throughout**

| Label | Meaning |
|-------|---------|
| **Live** | In the product today and usable by a relationship manager |
| **Live (demo data)** | Working end-to-end, but populated with demonstration records rather than production data |
| **Live (pilot)** | Working, but deliberately switched off until a named approval is granted |
| **In build** | Being completed now; not yet fully usable |
| **Planned** | Agreed scope, scheduled, not yet started |
| **External** | Cannot be completed by the team alone — needs a third party or a business approval |

---

## 1. Executive summary

### 1.1 What the product is

RM Workbench is a working platform for private-wealth relationship managers. It brings together, on one screen at the moment of need:

- who the client is, what they hold, what they are trying to achieve;
- what has changed in their world and in the market;
- what the manager should talk to them about next;
- the preparation material for the meeting, the products that fit, and the follow-up afterwards.

The design principle is deliberately narrow: **the manager and the client should eventually be looking at the same picture.** Most of today's tools separate "what the system knows" from "what I can show the client." That gap is where the value sits.

### 1.2 What is working today

The product is no longer a prototype. Twenty capability areas are live, and the four experiences you specifically asked us to build last are complete and demonstrable:

| Capability you asked for | Status | What the manager gets |
|--------------------------|--------|------------------------|
| **Holdings in one place** | Live (demo data) | Every holding for a client on one screen — asset class, currency, value, gain or loss, and whether the position meets the client's religious requirements |
| **Currency exposure** | Live | Live exchange rates showing exactly how much of a client's wealth sits in which currency, and where the concentration risk is |
| **Future Planner** | Live | A retirement and goals projection generated in seconds, with year-by-year milestones, a gap analysis, and recommendations — with a worked fallback when the AI service is unavailable |
| **Investors like me** | Live | A benchmark of how this client's allocation compares with comparable clients in the book — useful in the conversation, and honest about who the comparison is drawn from |

Alongside these, the platform already supports a full advisory cycle: a "My Day" dashboard, meeting briefs that draft themselves, meeting recording with explicit client consent, a next-best-action queue that ranks the whole client book, product search with suitability checks, approval-gated actions that never send without authorisation, message drafting that is grounded in the client's record, a tamper-evident audit trail, and an administration console that governs which capabilities are switched on.

### 1.3 What we are asking for

Three things, in priority order:

1. **Confirmation of the product direction** — this document, so that we are all working from the same brief.
2. **A decision on the Hong Kong regulatory work** — the single largest piece of outstanding engineering work, and a precondition for any live client use (§11, Decision 1).
3. **Agreement on the roadmap sequence** in §8, which front-loads regulation and client-record completeness ahead of feature expansion.

### 1.4 The honest summary

The platform is **demonstration-ready and feature-rich, but not yet live-ready.** The distance between those two states is not a large amount of feature work — it is a set of decisions and approvals that belong to the business, not to engineering (§10). We have deliberately built the product so that the risky capabilities (religious-compliance screening, family-office data, mobile access) are switched off by default and cannot reach a client until a named owner approves them.

---

## 2. The business case

### 2.1 The problem

A relationship manager managing a book of high-net-worth clients spends a disproportionate share of the day on preparation and administration rather than advice. Concretely, today:

- portfolio positions live in one system, the client record in another, market data in a third, and the manager's own notes in a fourth;
- producing a meeting pack is manual assembly, repeated from scratch for every client;
- knowing which clients need attention this week relies on memory and a spreadsheet;
- demonstrating "here is how your portfolio compares" or "here is what you are likely to have at retirement" either needs a specialist tool the client cannot see, or takes too long to be worth doing in a meeting;
- anything the manager does leaves an audit trail, but the trail is reconstructed rather than recorded.

None of this is a software failure. It is a fragmentation failure: the information exists, it is simply not assembled for the moment of conversation.

### 2.2 What this product changes

| Today | With the workbench |
|-------|-------------------|
| Assemble a meeting pack by hand | Brief drafts itself from the client's own record; manager reviews and edits |
| Guess who needs attention | The book is ranked daily with stated reasons the manager can inspect |
| Cannot show currency concentration | Live currency exposure, in the meeting, on the client's holdings |
| Retirement plans discussed qualitatively | Projection with milestones, probability and shortfall, generated in seconds |
| No defensible peer comparison | Allocation benchmarked against comparable clients in the book |
| Religious-compliance position held informally | Screening that cites the standard it relied on, with a clear statement of what it is not |
| Audit trail reconstructed afterwards | Every decision, approval and draft recorded as it happens |

### 2.3 The commercial logic

The four completed experiences are not generic dashboard features. They are the four things that private-bank clients in this market consistently ask their manager about and that no incumbent system answers well at the meeting table. They are also, deliberately, the four features most easily demonstrated to a client or prospect.

The two long-horizon areas — religious-compliance screening and family-office capability — address the two client segments where this market is growing fastest and where the competition is least developed.

---

## 3. Who it serves

| User | What they need | What the product gives them |
|------|----------------|-----------------------------|
| **Relationship manager** | Prepare fast, know who to call, advise with evidence, act without overstepping | My Day, priority queue, meeting briefs, portfolio and planning views, approval-gated actions |
| **Team leader / book manager** | See the whole book, direct effort, coach | Book-level dashboard, priority quality, audit visibility |
| **Compliance / risk** | Prove every recommendation was reasoned and authorised | Decision records on every suitability judgement and override, immutable audit trail, controls for which capabilities are live |
| **Administration / operations** | Turn capabilities on and off safely, prove what happened | Configuration console with named approvals, telemetry, audit review |
| **The client** *(future)* | See their own picture, not a description of it | Not yet built — deliberately sequenced as a separate release (§12) |

---

## 4. How it works

### 4.1 The advisory day, with the product

| Step | What the manager does | What the product does |
|------|----------------------|------------------------|
| **1 · Prepare** | Opens the day, decides who to see | Surfaces the day's schedule, the ranked client queue with reasons, and market news relevant to the book |
| **2 · Know the client** | Understands goals, risk appetite, recent changes | Assembles the client's profile, holdings, conversations, goals and preferences into one view |
| **3 · Advise** | Forms a view, tests it | Portfolio analytics, currency exposure, goal projection, peer comparison, product suitability, religious-compliance screening |
| **4 · Act** | Decides and commits | Actions are previewed, approved by the right person, and executed — never silently |
| **5 · Follow up** | Records what happened, plans the next step | Meeting notes and extracted action items, drafted messages, refreshed priorities, recorded audit trail |

### 4.2 The screens

| Screen | Purpose |
|--------|---------|
| **My Day** | The landing screen: today's schedule, key figures for the book, allocation and performance charts, live market news |
| **Client Book** | All clients, filterable |
| **Client Detail** | The single client record — profile, holdings, conversations, goals, suitability, family |
| **Meeting Brief** | The prepared pack for a specific meeting, reviewable section by section |
| **Priorities** | The ranked queue of who to contact, with reasons, snooze/dismiss/pin controls |
| **Workflows** | Multi-step client work in progress, with per-step status and ability to pause or abandon |
| **Portfolio Hub** | All holdings, one place — filters by asset class |
| **Currency Exposure** | Live currency split with concentration flags |
| **Future Planner** | Retirement and goals projection |
| **Investors Like Me** | Peer allocation comparison |
| **Admin / Audit** | Which capabilities are live, who approved what, and the full decision trail |

---

## 5. Product capability

Each area below states what it does, why it matters commercially, and where it stands.

---

### 5.1 Client book and client record — **Live (demo data)**

**What it is.** A single client record holding identity and contact details, wealth profile, asset and net-worth band, risk appetite, investment style, language and cultural preference, religious-compliance preference, family-office affiliation, holdings, financial goals, past conversations, and the suitability profile.

**Why it matters.** Every other capability reads from this record. A fragmented record is the root cause of the problem in §2.1.

**Current state.** A demonstration book of eight clients across Hong Kong, Singapore, mainland China, Japan, Australia and India is loaded, with six to eight holdings each across eight currencies. A larger regional dataset of forty-five contacts — thirty individual high-net-worth clients, eight family-office principals and seven linked family members — has been prepared and is available as a data pack, but the live application currently shows the eight-client demonstration book.

---

### 5.2 My Day dashboard — **Live (demo data)**

**What it is.** The landing screen: a live clock, the day's meetings, the ranked priority queue, four headline figures for the book, an allocation chart, a performance chart, and a market news panel.

**Why it matters.** It is the difference between a relationship manager starting the day with a view of their book versus a view of their inbox.

**Current state.** The layout, navigation and interaction are complete and stable. The headline figures and the performance trend are presently filled with demonstration values rather than calculated from the book; making them live is scheduled in §8.

---

### 5.3 Portfolio — holdings in one place — **Live (demo data)**

**What it is.** Every holding for a client in one table: asset name, ticker, asset class, currency, value in base and local currency, percentage of the portfolio, gain or loss, and a marker showing whether the position meets the client's religious requirements. Filters by asset class. A client list on the left with wealth, risk appetite and compliance markers.

**Why it matters.** This is the screen the client will eventually see. It is also the screen that answers "what do I actually own?" — a question that currently requires a custodian extract and a spreadsheet.

**Current state.** Complete and demonstrable.

---

### 5.4 Currency exposure — **Live**

**What it is.** Aggregates the client's holdings by currency, converts each to a common base currency using live market rates, and shows the split with allocation percentages, the rate applied, and a live-rate banner showing when the rates were last refreshed.

**Why it matters.** In a multi-currency book, unrecognised currency concentration is a real loss to clients and a reputational risk for the manager. It is also a required disclosure in most private-bank suitability processes.

**Current state.** Working with a live rate feed and a one-hour refresh cycle. **Important caveat for planning:** holdings are currently held in a single base currency and converted for display. True multi-currency position accounting — separating investment performance from currency movement, and valuing each position in the currency it is actually held in — is scheduled in §8 under family-office capability, because it is a prerequisite for consolidated family reporting.

---

### 5.5 Future Planner — **Live**

**What it is.** Takes the client's age, retirement age, current savings, monthly contribution, target corpus, assumed return, inflation assumption and up to three specific goals, then produces: a projected corpus at retirement, a probability of success, a year-by-year milestone table, an analysis of any shortfall against target, and prioritised recommendations.

**Why it matters.** It moves the most valuable part of a wealth conversation — "will I be able to do what I want to do?" — from a spreadsheet the manager prepares afterwards to a conversation the manager can have in the room.

**Current state.** Working. The projection is produced by a generative model with a strict output structure; when the AI service is unavailable or slow, the product falls back to a deterministic calculation and says so plainly rather than showing an empty screen or an invented answer. **The probability and recommendations are planning illustrations, not advice, and the screen says so.**

---

### 5.6 Investors like me — **Live**

**What it is.** Finds comparable clients in the book — similar risk appetite, comparable wealth scale — and compares this client's allocation against theirs, showing the difference in each asset class and the largest points of difference.

**Why it matters.** Two conversations at once. To the manager, it is a prompt about where this client's portfolio is unusual relative to peers. To the client, it is reassurance that their positioning is deliberate rather than accidental.

**Current state.** Working. The peer set is drawn from risk appetite and a wide wealth band so that a meaningful comparison group exists in a book of realistic size; where the book is too small to support it, the screen says so rather than presenting a thin comparison as meaningful. The comparison is aggregate — no peer is individually identifiable.

---

### 5.7 Religious-compliance screening — **Live (pilot)**

**What it is.** Screens a product or holding against recognised Islamic finance standards. It retrieves the relevant clauses from a structured library of standards, then assesses the product against the recognised categories of concern — prohibited returns, excessive uncertainty, and prohibited sectors — and returns a likely-compliant, likely-non-compliant, or insufficient-information result, together with the specific clauses relied upon.

**Why it matters.** Serving Muslim clients well requires a documented, defensible position on every recommendation, not an assurance from memory. This turns that position from an individual judgement into a traceable, reviewable process.

**Current state.** The screening engine is complete and works in the background. Three things remain before it can be switched on for live use, and all three are external to engineering: the standards library must be loaded and individually reviewed and approved; the written disclaimers must be settled by legal and compliance; and a qualified Shariah board must approve the methodology. **Until that approval is granted, the capability is switched off and cannot reach a client.** The product states on every result that it is a preliminary technical assessment and **not** a religious ruling, and that limitation is not removable by configuration.

---

### 5.8 Family and household view — **Live (basic) · entity view Planned**

**What it is.** A basic version records relationships between people — spouse, parent, child, sibling — and groups clients into households. The manager can see the family graph and the shared context across a household.

**Why it matters.** Wealth is frequently a family decision, and advice that ignores the household is advice that misses. This is also the entry point to the family-office capability in §7.

**Current state.** The basic relationship and household view is live. The full family-office view — legal structures, look-through exposure, consolidated net worth, decision rights, succession — is planned (§7, §8).

---

### 5.9 Market news and client intelligence — **Live**

**What it is.** A market news feed covering the holdings and names the book actually owns, with sentiment indicators, source attribution, relative timestamps, and a short summary of each item. It refreshes on its own cycle without disturbing the rest of the dashboard, and can be refreshed on demand.

**Why it matters.** News is only useful to a relationship manager if it is relevant to what the client owns. A general financial feed is background noise; a feed scoped to the book is a conversation starter.

**Current state.** Working, with two independent data sources and a failover between them, plus a short cache so that repeated views do not consume the data allowance. The system also detects unusually large market moves in the names the book holds — these currently inform the dashboard but are not yet retained as a history.

---

### 5.10 Meeting preparation — **Live**

**What it is.** Produces a meeting pack from the client's own record: a portfolio overview, material changes, recent interactions, relevant market context, and a suggested agenda. The manager reviews it section by section, edits it, and it becomes the record of what was discussed and agreed.

**Why it matters.** Preparation quality is the single biggest lever on meeting quality. This turns preparation from an hour of assembly into a review.

**Current state.** Working, with explicit section-level review and versioning so that what was reviewed is distinguishable from what was edited. Two additions are scheduled: a surfacing of products approaching maturity or review dates, and, for clients with a religious-compliance requirement, a section on the current holdings' compliance position.

---

### 5.11 Meeting capture and client record — **Live**

**What it is.** Records a meeting with the client's explicit, recorded consent — requested, granted, declined or withdrawn — captures the conversation, and extracts structured items (actions, decisions, dates, figures) for the manager to correct. Withdrawal stops capture and invalidates what was derived from it.

**Why it matters.** It removes the retyping that follows every meeting, and it establishes an auditable consent record, which is a regulatory expectation rather than a feature.

**Current state.** Working, with consent treated as a precondition rather than a formality. The consent wording itself requires legal sign-off before live use.

---

### 5.12 Prioritisation and next best action — **Live**

**What it is.** Ranks the whole book daily and presents the top ten clients with the reasons behind each — the signals that triggered the ranking. The manager can snooze, dismiss or pin a client, and record the outcome of a contact attempt.

**Why it matters.** It converts a question every manager is asked — "who should I call today?" — into an answered question with inspectable reasoning.

**Current state.** Working. The ranking policy itself — the weights and thresholds that decide who appears — must be set by the business before the capability can run on production data; until then it reports that it is not configured rather than inventing a ranking. A second input to the ranking, detection of personal life events affecting clients, is planned.

---

### 5.13 Product discovery and suitability — **Live**

**What it is.** Search by name, identifier or natural language; interprets the client's objective, timeframe and amount from what they said; compares candidate products side by side; assesses each against the client's risk appetite and objective; and detects conflicts. The manager may override a conclusion with a written justification, which is recorded.

**Why it matters.** Suitability is a regulatory obligation. Doing it as a recorded process rather than an experienced individual's memory is what makes it defensible.

**Current state.** Working as a process. The product universe and the suitability rules themselves are demonstration content and must be supplied by product and compliance for live use (§10).

---

### 5.14 Actions, approvals and controlled execution — **Live**

**What it is.** Any outward-facing action is first previewed with exactly what will be sent and where, then authorised by the appropriate person, then executed under that authorisation only. The execution call cannot carry a different payload from the one authorised. If the outcome is uncertain — a timeout or a crash — the system requires the result to be read back and reconciled rather than retried blindly.

**Why it matters.** A preview-then-authorise flow with an immutable payload is what allows automation into client-facing systems without creating the risk of sending something nobody approved.

**Current state.** Working, with the distinct approval classes the business requires (customer records, tasks, stored memory, client communications, ticket preparation) kept separate.

---

### 5.15 Client communications — **Live**

**What it is.** Drafts a follow-up note from the accepted items of a meeting, or an outreach note from the current reason a client is ranked. Drafts are grounded in the client's record, editable before approval, and always require a separate client-send approval. Nothing is sent automatically, and no greeting or fact is used that is not in the record.

**Why it matters.** Speed on the follow-up is where most relationship value is lost. Grounding is what keeps speed from becoming embarrassment.

**Current state.** Working. The sending channel is a placeholder pending a provider agreement (§10).

---

### 5.16 Continuity and memory — **Live**

**What it is.** Remembers confirmed facts about a client — preferences, commitments, stated intentions — and carries context forward between meetings and between workflow steps, so the manager does not re-establish context each time.

**Why it matters.** A relationship manager's value is partly in what they remember. This makes that memory explicit, correctable and shareable.

**Current state.** Working, with a deliberate rule that nothing is stored about a client until it has been proposed and confirmed by the manager.

---

### 5.17 Governance, audit and control — **Live**

**What it is.** Every advice event, configuration change, override and approval is recorded in a tamper-evident log where each entry is chained to the one before it, so that any alteration is detectable. Recorded decisions can be traced to the source data and the date they were made.

**Why it matters.** This is the artefact that turns "our manager was careful" into "our manager was demonstrably careful" — the difference between a claim and evidence when a recommendation is challenged.

**Current state.** Working and applied across the platform.

---

### 5.18 Administration, configuration and controlled rollout — **Live**

**What it is.** An administration console where each capability that carries risk is a named, separately approved switch: recording and consent, communications providers, ranking policy, product universe, religious-compliance methodology, family data, retention measurement, and mobile device access. Nothing is on by default; a capability that is switched off cannot be reached even by direct link. Configuration changes follow draft → validate → approve → activate with author, approver and activator recorded separately.

**Why it matters.** It is the mechanism that lets us ship capability ahead of compliance, which is the only way to move quickly without taking unacceptable risk.

**Current state.** Working. The switches are in place; the decisions behind eight of them are outstanding (§10).

---

### 5.19 Mobile and device access — **In build**

**What it is.** A responsive layout that adapts from desktop to tablet to phone: collapsible navigation, touch-optimised controls, and mobile-specific views for the client list and the meeting brief. A device-access control governs whether mobile is available at all.

**Why it matters.** A large share of relationship-manager time is spent away from a desk. An unusable mobile view is the same as having no mobile view.

**Current state.** The layout and components are in place, but feature parity on mobile has not been verified, and the device-access control requires an internal security policy before it is switched on. No automated mobile testing exists yet.

---

## 6. Delivery against the brief

Every request made to date, and where it stands.

### 6.1 The four flagship experiences

| Request | Status | Notes |
|---------|--------|-------|
| Holdings in one place, with generated demonstration data | **Delivered** | Live with an eight-client demonstration book |
| Currency exposure, using a live exchange-rate service | **Delivered** | Live rates with hourly refresh; see the accounting caveat in §5.4 |
| Future Planner using generative AI, capable of producing a report | **Delivered** | Live, with a deterministic fallback and an explicit advice disclaimer |
| "Investors like me" as a minimal feature | **Delivered** | Live, with the peer-set rule stated on screen |

### 6.2 Market news and client intelligence

| Request | Status | Notes |
|---------|--------|-------|
| Market news capability, informed by a separate reference implementation of a broker integration | **Delivered** | Live; the reference implementation contained no news facility of its own, so the value taken was the proven broker authentication approach and the integration pattern |
| News with caching, a richer display, and refresh independent of the rest of the page | **Delivered** | Live; five-minute cache, two sources with failover, dedicated panel |
| A locally relevant watchlist of quotes on the dashboard | **Delivered** | Live |

### 6.3 Religious-compliance screening

| Request | Status | Notes |
|---------|--------|-------|
| Standards-based screening with cited evidence, brought into the product rather than run as a separate system | **Delivered (engine)** | The screening and retrieval capability is complete and running inside the product |
| Standards library loaded, reviewed and approved | **Outstanding** | Requires the source document and a reviewer sign-off |
| Shariah board approval of the methodology | **Outstanding — external** | §10 |
| Manager-facing review screen | **Planned** | §8 |

### 6.4 Client records and family relationships

| Request | Status | Notes |
|---------|--------|-------|
| Move the client book into the product's own records, removing the external customer-system dependency | **Delivered** | Live; the external connection has been removed |
| Generate a regional client dataset for demonstration | **Delivered (partial)** | Forty-five-contact data pack prepared; the live book shows eight clients — §5.1 |
| Model clients as potentially religious, and model parental and family relationships | **Delivered (basic)** | Basic relationships and household grouping live; full family-office view planned |

### 6.5 Platform quality

| Request | Status | Notes |
|---------|--------|-------|
| Frontend pages must be reachable and connected, not orphaned | **Delivered** | All pages reachable from the application shell; navigation reorganised into a core group and an analytics group |
| Dashboard on the front page, with portfolio and market news visible | **Delivered** | Live |
| Fix and remove errors surfaced during review | **Delivered** | Including the peer-comparison field mismatch and the market news display defects |
| No duplicated database; one instance | **Delivered** | One database service with separate application and test schemas |
| All documents and reports in one place | **Delivered** | Consolidated into a single deliverables area |

---

## 7. What remains

Grouped by theme. Every item is agreed scope; the sequencing is in §8.

### 7.1 Hong Kong regulatory capability

| Item | Why it matters |
|------|----------------|
| A Hong Kong suitability rule set — reasonable basis for the recommendation, risk-tolerance match, product-complexity assessment, disclosure obligations | Suitability is currently a working process without a Hong Kong rule set behind it. This is the precondition for advising live Hong Kong clients |
| Conduct-standards tagging on the audit trail, aligned to the bank's regulatory standards | Makes the audit trail usable by compliance for supervisory review rather than only for internal tracing |
| Jurisdiction-aware controls, so that rules vary by market rather than being embedded in the product | Multi-market expansion is not viable without this |
| Automated monitoring of suitability and KYC expiry, with a task raised before a client becomes non-compliant | Today expiry is visible but not acted upon |

### 7.2 Client record completeness

| Item | Why it matters |
|------|----------------|
| A single aggregated client view assembled in one place rather than pieced together by the screens | Currently the experience of "one screen" is achieved through several assembly steps; this makes it structural |
| A document store — statements, contracts, tax forms, prospectuses, with expiry and tagging | Replacing paper and document chasing; also the missing half of "everything about this client in one place" |
| A transaction history | Holdings are currently a snapshot, not a record of movement; clients and auditors expect the history |
| A pipeline of opportunities — cross-sell, renewals, referrals — with stage and forecast | The manager's second-largest blind spot after client attention; without it, growth is invisible to management |

### 7.3 Portfolio analytics depth

| Item | Why it matters |
|------|----------------|
| Stress testing and scenario analysis | The question every client eventually asks: what if markets fall, or the currency moves against me |
| Comparison against a reference portfolio, showing drift per asset class | Turns "here is your portfolio" into "here is how yours differs, and why" |
| Separating investment performance from currency movement | Currently the two are indistinguishable in any performance view, which is misleading in a multi-currency book |
| Retaining market-movement history | Alerts are useful once; a record of what was flagged and what happened is more useful |

### 7.4 Family-office capability

| Item | Why it matters |
|------|----------------|
| Legal structures — trusts, holding companies, foundations, limited partnerships | The current family view shows relationships between people; it cannot show where wealth legally sits |
| Ownership links between structures, with percentages | Without this the platform cannot answer "what is this family actually exposed to?" |
| Look-through exposure | A holding inside a structure inside a structure is not worth its face value to the family; the effective exposure is what matters |
| Consolidated net worth across structures and currencies | The single number a family-office client asks for |
| Data provenance on every imported figure — source, as-of date, reconciliation state | Trusted totals require knowing where each number came from and whether it has been reconciled |
| Decision rights and entitlements | Who may see what, and who may decide — encoded separately, because the two are not the same |
| Succession planning | Anticipating and preparing for a change of decision-maker is the conversation that a family expects to have early |
| Family governance records | Meetings, charters, and decisions taken |

### 7.5 Religious-compliance depth

| Item | Why it matters |
|------|----------------|
| A manager-facing review screen | Screening exists; a way for a human to review and sign off the evidence does not |
| Portfolio-wide screening | Screening one product at a time leaves the portfolio as a whole unexamined |
| Zakat calculation with recognised thresholds and holding periods | Currently a flat rate without the conditions that make it meaningful |

### 7.6 Everyday working tools

| Item | Why it matters |
|------|----------------|
| Export client information to a spreadsheet | Managers live in spreadsheets, and the reconciliation between them and the platform is today's biggest hidden cost |
| Export a meeting brief to a document | The brief frequently leaves the platform for a document the manager or client holds |
| Export the calendar | The platform's calendar is not yet the manager's calendar |

### 7.7 Live-readiness and control

| Item | Why it matters |
|------|----------------|
| Production sign-in and single sign-on | Currently a development placeholder. A hard blocker for live use |
| Automated testing of the user interface and end-to-end journeys | No interface test suite exists; the regression risk is high and growing |
| Load and performance testing | Unknown behaviour under a full book of clients |
| Approved consent wording, communications agreement, ranking policy, product universe, retention baseline, device policy | §10 — business decisions, not engineering work |
| Deployment, rollback and disaster-recovery documentation | Required before any live client environment |

---

## 8. Roadmap

Three horizons. Each horizon has an exit condition, not just a date.

### Horizon 1 — Make it defensible and complete *(0–8 weeks)*

**Exit condition: every client record is complete, every advice decision is regulated, and the product can be used with real data.**

| Workstream | Items |
|------------|-------|
| Hong Kong regulatory | Suitability rule set; conduct tagging; jurisdiction-aware controls; KYC expiry monitoring with task creation |
| Client record | Aggregated client view; document store with upload, retrieval and expiry; transaction history |
| Commercial visibility | Opportunity pipeline with stage, value and forecast; renewal visibility |
| Analytics depth | Stress testing; reference-portfolio comparison; separating performance from currency movement; market-movement history |
| Everyday tools | Spreadsheet export; brief export to document; calendar export |
| Live-readiness | Production sign-in; interface and end-to-end test suites; load testing; deployment and rollback documentation |

**Why this order.** Two of the three items in §7.1 (regulation, complete client record) are prerequisites for advising live Hong Kong clients, and both are visible to clients and to the regulator. Features that follow them are cheaper to build because the record underneath them is finally reliable.

### Horizon 2 — Serve the complex client *(2–4 months, overlapping)*

**Exit condition: the platform can advise a family-office client and a client with a religious-compliance requirement, on live data.**

| Workstream | Items |
|------------|-------|
| Religious compliance | Load, review and approve the standards library; manager review screen; portfolio-wide screening; Zakat with recognised thresholds; secure Shariah board approval |
| Family office, phase one | Legal structures; ownership links; look-through exposure; consolidated net worth; multi-currency position accounting; provenance on every imported figure |
| Data acquisition | Connection to the platforms where family-office data actually lives, read-only, with reconciliation status |

**Why this order.** The two fastest-growing client segments are the ones where the current product is weakest. Religious-compliance work is gated externally, so the library and review tooling are built while the approval is pursued. Family-office phase one is deliberately about the client's own structures rather than third-party platforms — it can be built without waiting for any external agreement.

### Horizon 3 — Extend and industrialise *(4–9 months)*

**Exit condition: the platform runs at production scale, on a client-facing surface, with governed controls throughout.**

| Workstream | Items |
|------------|-------|
| Family office, phase two | Decision rights and entitlements; succession planning; family governance records; external platform connections for capital calls and distributions |
| Client-facing surface | A client view of their own portfolio, currency position and plan, on the same screens the manager uses — the strategic bet described in §2.2 |
| Mobile | Verified feature parity; touch and accessibility review |
| Industrialisation | Performance and scale hardening; a formal release-readiness review against all control gates; training and support material |

**Why this order.** The client-facing surface is the single largest commercial differentiator, but putting it in front of clients before the record underneath it is complete would expose internal inconsistencies to the people least able to forgive them. Mobile parity and scale hardening follow the same logic.

### Horizon summary

| Horizon | Focus | Duration | Exit condition |
|---------|-------|----------|-----------------|
| 1 | Defensibility and completeness | 0–8 weeks | Regulated advice on complete records |
| 2 | Complex client segments | 2–4 months | Family-office and religious-compliance advisory live |
| 3 | Extension and industrialisation | 4–9 months | Client-facing surface at production scale |

---

## 9. Value case

### 9.1 What we expect the product to deliver

| Measure | Current state | Target | How measured |
|---------|---------------|--------|---------------|
| Meeting preparation time | Manual assembly | Reduced by a substantial margin per client | Time sampled from the brief review |
| Clients contacted with a stated, inspectable reason | Manual | Every priority ranked with a reason | Priority queue audit |
| Portfolio questions answerable in the meeting | Partial | Holdings, currency, plan and peer comparison all available live | Feature usage against the four flagship experiences |
| Advice decisions reconstructable after the fact | Reconstructed | Recorded as they happen | Audit coverage |
| Portfolio-wide religious-compliance visibility | None | Full portfolio screened with cited evidence | Screening coverage |
| Consolidated family net worth | Manual | One number, with provenance | Reporting time |
| Time for the manager to assemble a client pack | Hours | Minutes | Sampled |

Targets are deliberately expressed as movement rather than absolute numbers; the baseline should be measured in the first weeks of Horizon 1 before targets are fixed.

### 9.2 The commercial argument in three sentences

The four completed experiences make the product demonstrable and differentiated in a meeting, today, without waiting for any approval. The two areas we have deliberately built to be switched off — religious-compliance screening and family-office capability — address the two client segments where this market is growing and where the competition is thinnest. And the reason they are switched off is the same reason they are credible: no recommendation in either area reaches a client without a named approval behind it.

---

## 10. Dependencies and approvals

None of these are engineering tasks. Each needs a decision, a signature, or an agreement from outside the team.

| # | Approval needed | Owner | Blocks | Needed by |
|---|-----------------|-------|--------|-----------|
| 1 | Recording and client-consent wording | Legal, with Compliance | Live use of meeting capture | Horizon 1 |
| 2 | Communications provider agreement and credentials | Procurement, with Legal | Live sending of client messages | Horizon 1 |
| 3 | Priority ranking policy — weights, thresholds, what counts as a reason | Business and Compliance | Priority queue running on production data | Horizon 1 |
| 4 | Product universe and suitability rules | Product, with Compliance | Live suitability assessment | Horizon 1 |
| 5 | Hong Kong suitability rule set and conduct tagging | Compliance | Advising live Hong Kong clients | Horizon 1 |
| 6 | Shariah board approval of the screening methodology | Shariah board, with Compliance | Religious-compliance capability switched on | Horizon 2 |
| 7 | Standards library approval | Compliance | Religious-compliance screening returning real results | Horizon 2 |
| 8 | Family data governance and entitlement policy | Data Governance, with Legal | Family-office capability in live use | Horizon 2 |
| 9 | Retention measurement baseline | Analytics, with Legal | Retention reporting | Horizon 3 |
| 10 | Mobile device access policy | IT Security | Mobile access switched on | Horizon 3 |

**Sequencing note.** Approvals 1–5 are the critical path for Horizon 1 and can run in parallel with engineering. Approvals 6 and 7 have the longest lead time of any item on this list because they depend on external bodies with their own calendars; they should be started immediately, even though the engineering they gate does not begin until Horizon 2.

---

## 11. Decisions requested

| # | Decision | Recommendation | Needed by |
|---|----------|----------------|-----------|
| 1 | **Approve the Hong Kong regulatory work as the first priority** and accept that live client use waits for it | Approve. The product is capable but not yet defensible without it | Immediately |
| 2 | **Confirm the product direction** in this document as the baseline for the next two horizons | Confirm | Immediately |
| 3 | **Approve the Horizon 1 → 2 → 3 sequence**, and specifically that client-facing delivery is deferred to Horizon 3 | Approve. Building the client surface before the record is complete would expose internal inconsistencies to clients | Immediately |
| 4 | **Approve the standards library review and Shariah board submission as a parallel workstream**, with the board process started now | Approve. It has the longest external lead time of any item | Immediately |
| 5 | **Decide the eight-versus-forty-five client book** for demonstration use: continue with the focused eight, or load the full regional book | Recommend keeping eight as the default demonstration set, with the full book available as an option — the forty-five-contact dataset is richer but includes family-office contacts who are better demonstrated once family-office capability exists | Before the next demonstration |

---

## 12. Assumptions and boundaries

### 12.1 What this release deliberately does not do

| Excluded | Reasoning |
|----------|-----------|
| Client-facing web or mobile application as a separate product | Requires the client record and regulatory position to be complete first; sequenced as Horizon 3 |
| Placing trades or managing orders | The workbench advises and prepares; execution belongs to the dealing and platform systems |
| Custody, settlement, and position reconciliation | Held by the custodian and platform systems; the workbench consumes, never owns |
| A full financial-planning engine with tax and estate modelling | The projection is a conversation aid; a true planning engine is a separate product decision |
| Multi-entity accounting, net asset value, and waterfalls | Belongs to the family's own administrators |
| Full family-office platform ownership | The workbench presents the family's position in a client-centric way; it does not become the system of record for the family office |
| Automated sending of anything to a client | Every outward action requires a named human approval — not configurable away |
| Building for a specific competitor's feature set | The four flagship experiences were chosen for client value, not for parity with any named institution |

### 12.2 Assumptions

- The client book remains in the range of hundreds, not thousands — the product is designed for a relationship-manager-led book, not for a call-centre or an advisory platform.
- The regulatory environment is Hong Kong-first, with other jurisdictions following the same structure rather than being designed in from the start.
- Generative AI output is always reviewed by a person before it reaches a client, and the product states this on every screen where it appears.
- Data providers continue to be available on commercial terms; the product is designed to fail visibly rather than silently when a provider is unavailable.
- The demonstration dataset is acceptable for demonstration purposes but is not a substitute for approved production content in the product universe, suitability rules, ranking policy, or standards library.

---

## 13. Glossary

| Term | Meaning |
|------|---------|
| **Relationship manager (RM)** | The banker who looks after a client and advises on their wealth |
| **Book** | The set of clients one relationship manager is responsible for |
| **AUM** | Assets under management — the total value of what a manager looks after |
| **HNW / UHNW** | High-net-worth and ultra-high-net-worth clients |
| **Suitability** | The regulatory requirement that a recommendation must fit that particular client's circumstances and risk appetite |
| **Next best action** | The recommendation of who to contact and about what, produced by the platform |
| **Brief** | The prepared pack for a meeting, assembled from the client's own record |
| **Religious-compliance screening** | Assessing a product against recognised Islamic finance standards. A preliminary technical assessment, **not** a religious ruling |
| **Standards library** | The structured collection of recognised standards clauses that screening retrieves and cites |
| **Look-through exposure** | The value a family actually has at risk after tracing ownership through intermediate structures |
| **Consolidated net worth** | Total wealth across all of a family's structures, in one number |
| **Entitlement** | Who may see something, and — separately — who may decide about it |
| **Zakat** | The Islamic obligation of almsgiving on wealth, calculated with recognised thresholds and holding periods |
| **Priority controls** | The ability to snooze, dismiss or pin a client, changing the next ranking only |
| **Pilot** | A capability that is switched off by default and cannot be reached until a named approval is granted |
| **Workbench** | The product itself: the single surface where client context, analysis, preparation and follow-up come together |

---

**End of document**

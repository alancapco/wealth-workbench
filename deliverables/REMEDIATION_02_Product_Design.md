# Product Design Specification · RM Workbench Remediation

**Deliverable:** REMEDIATION_02 · Phase 2 · English implementation-facing interaction specification  
**Designer:** Jian Yiyong (简宜用), Product Designer  
**Status:** Design handoff for lead review and subsequent architecture/contract freeze; not implementation acceptance or production approval.  
**Authority:** Approved `REMEDIATION_01_Requirements.md`, all 28 stable functional IDs and the detailed controls in `01_PRD_Requirement_Inventory.md` §§2–12.  
**Inspection:** Complete requirements/inventory; current `frontend/app/page.tsx`, `components/BriefModal.tsx`, `app/brief/[clientId]/page.tsx`; backend client/workflow endpoints; frontend re-audit. Existing code is context, not the source of product truth.

This document defines pages, user-visible fields, validations, navigation and states. Routes below are **proposed browser destinations**, not API endpoints or data models. Architecture owns technical contracts, persistence implementation, provider selection and security implementation. No application code, API/schema changes, external calls, deployments or destructive operations are part of this deliverable.

## 1. Information architecture

### 1.1 Experience principles and preservation

1. Preserve the existing restrained black header, light page background, white cards, portfolio charts and schedule-oriented dashboard where useful. Correct content, states and layout rather than undertake a visual rebrand.
2. **One copilot, many task views.** My Day is the primary entry. Its `Start workflow` control and contextual actions (`Prepare meeting`, `Draft outreach`, `Find products`) all start/resume the same copilot workflow with authorized client context. They are shortcuts, not separate AI applications. No unrelated chatbot, independent prompt history or context copy/paste between skills.
3. A persistent workflow strip shows client, actual workflow reference, stage, last confirmed save and next human decision. Client memory, evidence and review components are shared across all task views. Viewing existing records does not start generation.
4. One canonical brief experience serves My Day, calendar, client and workflow entry. Remove independently behaving brief modal/page variants. Desktop may use a route-backed side panel for quick viewing; full-page and mobile presentations use the **same content, state and controls**. The existing `/brief/[clientId]` entry resolves authorized existing briefs or an explicit generation prompt; opening it never silently generates another version.
5. An approval is specific to the displayed artifact version, scope and intended action. `Approve notes`, `Approve CRM changes`, `Approve send` and `Approve handoff` are separate, unambiguous decisions. No `Approve everything` that hides email sends or a trade step.
6. Show only entitled facts with verifiable provenance. A global fixture banner is additional to—not a substitute for—per-artifact source state. Do not infer zeros, identities, confidence, successful synchronization or LIVE availability.
7. Core P0 → core GA (including Tier B) → separately governed pilots. Both pilots are off by default. Hidden navigation is not authorization; direct links are gated too.

### 1.2 Page tree

```text
Session boundary
  P-001 Sign in / session recovery
Authorized application shell
  P-002 My Day / copilot entry (/)
    P-003 Calendar and meeting selection (/calendar)
    P-004 Client lookup (/clients)
      P-005 Client workspace and memory (/clients/:clientId)
    P-006 Workflow workspace (/workflows/:workflowId)
      P-007 Canonical brief (/workflows/:workflowId/briefs/:briefId)
      P-008 Consent and meeting capture (/workflows/:workflowId/meeting)
      P-009 Transcript and extraction review (/workflows/:workflowId/transcript)
      P-010 Post-meeting review and action status (/workflows/:workflowId/review)
        P-011 Message draft and send review (/workflows/:workflowId/message/:draftId)
        P-012 Ticket prefill / handoff review (/workflows/:workflowId/ticket/:artifactId)
      P-013 Daily priorities (/priorities)
        reason/evidence drawer; snooze/dismiss/outcome dialogs
      P-014 Product discovery and comparison (/workflows/:workflowId/products)
        P-015 Suitability assessment (/workflows/:workflowId/assessment/:assessmentId)
      P-016 Shariah pilot task view (/workflows/:workflowId/shariah)
      P-017 Family pilot task view (/workflows/:workflowId/family)
  P-018 Administration and readiness (/admin)
    Five runtime configuration tabs; rollout/stage controls; approval evidence
  P-019 Audit and measurement (/oversight)
    Scoped audit detail drawer; measurement/guardrail tabs
Shared overlays (not independent applications)
  Source detail; identity resolution; approval preview; version conflict; unsaved changes
Shared route boundary
  P-020 Unavailable / no access / not found / recoverable application failure
```

No new client portal, account-opening, user self-registration, role-granting console, system-of-record replacement or full financial-planning tool is introduced. Identity and book assignments are read from institutional identity administration; P-018 configures approved workbench settings, not entitlements it has no authority to grant.

## 2. User flows and state transitions

### 2.1 Core flows with exception navigation

| Flow / IDs | Main page-level path | Exception branches and recovery |
|---|---|---|
| Prepare a meeting · FR-01–03, FR-20 | P-002 → P-003 event or P-004 client → P-006 → P-007 → approve reviewed sections → P-008 | Multiple eligible identities → explicit resolution overlay; no authorized match → P-004 or cancel, never create/merge a client. Failed source → section-level unavailable/stale; retain other sections. Generation failure → keep prior version or retry explicitly. Missing audit/persistence readiness → approval blocked. |
| Capture and extract · FR-04–06 | P-007/P-005 → P-008 policy and consent → start capture → stop → P-009 evidence-linked extraction | Unknown policy, no provider, unsupported format or declined consent → manual notes in P-008. Withdrawal → capture stops immediately, affected derived drafts invalidated → manual notes/review. Audio loss → show last confirmed transcript time; recover without duplicate meeting. No transcript → manual notes; never a completed transcript. |
| Review outcomes · FR-07–10, FR-20 | P-009 correct/accept/reject items → P-010 accept specific artifacts → preview old/new values → approve notes/CRM/tasks/memory → inspect action status; message → P-011; ticket → P-012 | Item rejected/deleted → removed from future drafts; dependent approvals invalidated. Missing mandatory action field → return to that artifact with inline validation. Provider failure → retained draft and failed/pending/unknown action card. Changed source version → conflict preview, re-review. |
| Prioritize and converse · FR-11–15 | P-002 → P-013 reason/evidence → P-005 or start/resume P-006 → P-011 editable grounded draft → explicit send preview → confirmed provider outcome → P-013 contact outcome | No eligible clients → criteria + evaluation time, no filler. DNC/channel restriction → excluded/blocked; stale open draft must recheck. Snooze/dismiss/pin persists; failed save restores last confirmed control state. Provider unknown result → check status, not a new send. |
| Discover and assess · FR-16–19 | P-002/P-005 → P-006 → P-014 interpret query → edit filters → run search → compare/select → P-015 factors → RM decision → P-010/P-012 only when eligible | No results → explain constraints; RM explicitly edits soft filters. Missing/expired KYC → Yellow at best, ticket blocked. Soft override only when policy/authority permit → rationale dialog → new decision record. Hard stop → no override CTA. Input changed → assessment stale, re-assess. |
| Shared context/closed loop · D5, C-01–16 | P-010 approved outcomes → P-005 confirmed memory and pending/confirmed sync states → next P-013 evaluation reason → P-007 later brief cites latest entitled context | Failed memory persistence is not a completed workflow. Dismissal is an RM action, not a client preference. Conflicting memory links source records and remains unresolved. Context revoked → clear protected view and resume only after reauthorization. |
| Administration · FR-22 | P-018 select class → edit draft config → validate/diff → authorized approval/activation when policy gates permit → version/readback → P-019 audit | Incomplete policy/evidence → save draft permitted, activation blocked. Concurrent version → resolve diff. Provider credentials absent → unavailable, not connected. Stage disabled → affected P-006 stages offer manual fallback, preserve prior records. |
| Mobile scoped tasks · FR-21 | P-004 lookup → P-005/P-007 briefs; P-013 priorities → P-011 edit/approve outreach | Same authorization and policy gates. Unsupported device/session → P-020 explanation. Recording/ticket may show desktop-only guidance per DEC-08; no insecure transfer link or sensitive cached draft. |
| Shariah pilot · FR-4.1–4.3 | Approved pilot cohort → P-005 preference preview/confirmation → P-006 → P-016 screening → estimate → proposal evidence completeness → review/finalize pack | Flag off/non-cohort → P-020 feature unavailable. Missing SSB rule/evidence → blocked screening label/finalization. Non-compliant candidates never offered as recommendations. Missing estimate input → no authoritative total. Advisor confirmation distinct from RM review; no fatwa. |
| Family pilot · FR-5.1–5.3 | Approved pilot cohort → P-006 → P-017 structure extraction → RM verification → consolidation/reconciliation → attendee-specific pack/scenario or verified notice → 90-day forecast → Risk reason in P-013 | Unauthorized nodes filtered before any output. Unknown attendee entitlement → generation blocked, no pack preview. Unconfirmed structure/notice → noncanonical, excluded from final calculations. Discrepancy above approved tolerance → unresolved banner, no reconciled claim. |

### 2.2 Shared state machines (UX vocabulary; not schema enums)

**Workflow:** Not started → Running stage → Needs review → Stage approved → Executing approved action → Next stage / Completed. Alternative states: Paused by RM; Blocked by policy/entitlement; Unavailable dependency; Failed recoverable; Abandoned by RM. A workflow is not `Completed` merely because generation finished. Display completed, pending, failed and deliberately skipped stages separately; never imply a send/ticket occurred because an earlier review passed. Opening/resuming a workflow restores the last durable stage and actual action results.

**Artifact review:** Draft/Unreviewed → Edited/Needs review → Approved version or Rejected. Brief sections and recommendations have identifiable per-section/item review state; read-only factual source records are not rewritten by reviewing their generated summary. Every changed fact, recipient, content, source basis, mapping, policy or assessment invalidates affected approvals before any new external/system action. Version history preserves prior decisions under retention policy.

**Action delivery:** Not approved → Approved, not executed → In progress → Confirmed succeeded / Failed safe to retry / Outcome unknown, reconciling. Only authoritative persistence readback/provider evidence permits confirmed success. A timeout is not proof of failure. Repeated clicks, reloads and retry refer to the same intended operation; no repeat send/write of an already confirmed action. If the outcome cannot yet be reconciled, provide `Check status`, not an enabled `Send again`. Nothing new is sent in the background without explicit approved action; if a provider returns an existing scheduled outcome, show it, do not add a new scheduling feature.

**Recording:** Not eligible / Ready for consent → Consent recorded → Starting → Recording → Paused → Stopped → Processing → Partial transcript / Transcript available. Declined/Withdrawn/Policy unknown stop or prevent capture independently of UI connectivity. A paused session resumes only if consent/policy remain valid. Show last confirmed capture/transcript position, not guessed progress. Consent changes use their own auditable status.

**Context switch:** Changing client/tenant/book closes or clears protected source/artifact content before loading the next context. Do not show a previous client's skeleton-filled content under a new name. In-flight old-context responses must never become visible. Unsaved permitted edits prompt to save or discard; revoked entitlement takes precedence over retaining a visible draft.

## 3. Page inventory and permissions

`R` = assigned RM with entitled scope; `A` = configuration admin within assigned scope; `G` = institution-designated governance approver; `O` = authorized rollout/operator; `V` = explicitly entitled audit/measurement viewer. Roles are capabilities, not a proposed role database. Governance/Security roles see only evidence assigned to them, not all client records. All actions require authoritative permission checks, including direct links and source viewers.

| Page | Name | Browser destination | FR / controls | Entry → exits | Access |
|---|---|---|---|---|---|
| P-001 | Sign in / recovery | `/sign-in` | D0, INT-10, NFR-04 | any session boundary → sanitized original route / P-002 | unauthenticated |
| P-002 | My Day / copilot entry | `/` | FR-01,11,20,21; C-01,05,07,16 | sign in/shell → P-003/004/006/013 | R; other roles scoped navigation |
| P-003 | Calendar | `/calendar` | FR-01, D1, INT-05 | My Day → resolution / P-006/007 | R |
| P-004 | Client lookup | `/clients` | FR-01,21; D0/D1 | shell/context picker → P-005/006 | R |
| P-005 | Client and memory | `/clients/:clientId` | D5, FR-20,4.1; INT-01/02/04 | lookup/priority/brief → workflow/history/source | R |
| P-006 | Workflow workspace | `/workflows/:workflowId` | FR-20; C-01–16 | task launch/resume → all permitted task views | R |
| P-007 | Canonical brief | `/workflows/:workflowId/briefs/:briefId` | FR-01–03,20,21 | event/client/workflow → sources/P-008 | R |
| P-008 | Consent/capture/manual notes | `/workflows/:workflowId/meeting` | FR-04,06; D2 | brief/workflow → P-009/010 | R |
| P-009 | Transcript and extraction | `/workflows/:workflowId/transcript` | FR-05,06 | meeting/workflow → P-010/source | R |
| P-010 | Unified review/status | `/workflows/:workflowId/review` | FR-07,08,20; D5 | transcript/manual/workflow → P-011/012/005 | R |
| P-011 | Message draft/send | `/workflows/:workflowId/message/:draftId` | FR-09,14,15,20,21 | review/reason/workflow → delivery status/outcome | R |
| P-012 | Ticket handoff | `/workflows/:workflowId/ticket/:artifactId` | FR-10,20 | review/assessment → entitled external ticket tool | R |
| P-013 | Priorities | `/priorities` | FR-11–13,21 | My Day/shell → evidence/P-005/006/011 | R |
| P-014 | Products/compare | `/workflows/:workflowId/products` | FR-16,17 | task launch/workflow → P-015 | R; Tier B readiness |
| P-015 | Suitability | `/workflows/:workflowId/assessment/:assessmentId` | FR-18,19,20 | product/review/ticket → review/ticket/source | R; override privilege if allowed |
| P-016 | Shariah tasks | `/workflows/:workflowId/shariah` | FR-4.1–4.3; C-18 | approved pilot workflow → sources/preview/audit | R + pilot cohort/readiness |
| P-017 | Family tasks | `/workflows/:workflowId/family` | FR-5.1–5.3; C-17 | approved pilot workflow → sources/preview/priority | R + pilot + node entitlement |
| P-018 | Admin/readiness | `/admin` | FR-22; GOV-02,05–07; C-10,11,13 | authorized shell → config diff/audit | A/G/O separated by capability |
| P-019 | Audit/measurement | `/oversight` | NFR-06,10; M/TEL/GRD/GATE | artifacts/admin/shell → scoped record details | V; RM own permitted workflow audit |
| P-020 | Boundary/failure | current route or `/unavailable` | D0, B-10; NFR-03/09 | failed/denied/off route → safe back/retry/sign in | no protected data |

## 4. Page details and complete interaction rules

### 4.0 Common field, validation and state specifications

**Field notation:** RO = read-only authoritative display; Req = required for the named action, not necessarily for saving an incomplete draft; Opt = optional; Cond = conditional. Unless stated, editable text defaults blank; selections default unselected; approval checkboxes default unchecked. Never fill absent facts from an example. Text displays are plain/safely rendered content, including graph/chart tooltips. Saved drafts are not approved canonical outcomes or permission to send.

**Shared validation dictionary (applies to every field below):**

| Type | Required / range / default / validation behavior |
|---|---|
| Entitled reference | Req when acting on a client/meeting/account/product/node. Select an existing permitted record; no free-text identifier substitution. Read-only inherited selection remains visible. Revalidate permission and current version at action time. No default `demo`, client, approver or account. |
| Short text / long text | Trim for nonblank validation; preserve meaningful internal whitespace. Required text must contain a non-whitespace character. Provider/policy/configured length limits are shown as counters and enforced consistently; no silent truncation. If a mandatory downstream limit is unknown, drafting is allowed but downstream approval is blocked with `Field rules are not configured`. No invented institution-wide numeric maxima. |
| Structured reason | Req for dismissal, correction/rejection and override where specified. Select an approved configured reason; `Other` requires nonblank long text. Optional elaboration otherwise. No preselected reason. Missing approved reason catalog blocks the governed action rather than inventing a taxonomy. |
| Date / date-time | Real calendar date; display explicit timezone for date-time. No fabricated transcript owner/due date or hawl date. Future-only for snooze; dates in source content may be past and show overdue rather than being silently changed. Invalid local/DST times require correction; date-only due dates stay date-only. |
| Decimal / money / percentage | Finite numeric input, no NaN/infinity. Currency required with money, from the permitted currency list; no bare `$` assumption. Amounts >0 for ticket/investment/notice amount; zero permitted only where a source/method allows it. Precision, ranges, conversion and rounding come from product/provider/approved methodology, displayed to RM; unknown required rules block finalization, not invent precision. Percent type is explicit; monetary totals do not sum different currencies without sourced FX/as-of. |
| Choice / multi-choice | Values only from the page-defined set or institution-approved policy/provider catalog. Unknown legacy values display as `Needs review`, not silently mapped. Blank/unknown is distinct from false/no preference. |
| Email / SMS destination | Req for send; derived from entitled contact record when possible but explicitly confirmed. Email must be syntactically valid and allowed by channel policy. SMS uses validated international destination format/provider rules. No default additional recipients; do not suggest unauthorized contacts. Changed recipients invalidate approval and recheck DNC/consent. |
| Evidence/source reference | RO or Req evidence selector from entitled sources. Shows source name/record, as-of, retrieved time where available, version, freshness/SLA owner, and Recorded/Derived/RM-entered origin. Missing provenance blocks the corresponding material AI assertion. Do not synthesize a source timestamp from browser time. |
| Version / actor / status | RO, system-confirmed actual value only. Approver is authenticated actor, never an editable name. Absent timestamp/reference shows `Not yet recorded`, not a made-up identifier. Concurrent change requires re-review. |
| Policy-controlled attachment | Allowed type, size, residency and retention rules must be configured and visible before choosing/uploading. No upload while policy/provider unavailable. Failed/unsupported files remain explicitly unprocessed; no extracted result claim. |

**Universal page-state contract U:** Every list/detail page P-002–019 implements all rows below, specialized per page in §4.1 onward. P-001/020 have their own boundary states. Each card/subsection can fail independently.

| State | Presentation / action |
|---|---|
| Initial loading | Labeled skeleton in the affected region, stable headings; no old-context content, fake counters or approval CTA. `Loading…` announced politely once. |
| Refresh with existing data | Retain only same-context last confirmed data labeled with its actual as-of; show refresh status. Failed refresh leaves stale label + error, never a newer source time. |
| Empty (successful zero result) | Specific explanation, relevant safe next step and actual evaluation/as-of when available. Never substitute success prose such as `No risks` for a failed/missing evaluation. |
| Error | Plain-language failure, retained permitted edits, `Retry` or `Check status` according to action safety; actual tenant-safe support reference if available. No raw stack, secrets or unauthorized source names. |
| Degraded / partial / stale | Inline affected sections, show missing dependencies and last verified evidence; keep independent client lookup/manual work available. Disable only dependent unsafe actions. |
| Blocked / no permission | Visible reason category and safe resolution path; no approval bypass. Missing rights may use nondisclosing `Record unavailable`. Recheck before context assembly and before actions; remove revoked protected data. |
| Unconfigured provider | `Unavailable — [capability] is not configured`; no synthetic fallback. Configuration link only to authorized admin, otherwise `Contact your administrator`. |
| Submitting / saving | Button states exact action (`Saving draft…`, `Approving…`, `Checking status…`); avoid duplicate clicks. On failure retain inputs and show last durable state, never optimistic success for writes/sends. |
| Offline / session expired | Show disconnected/session boundary; no external action. Stop capture if consent/auth validity cannot be enforced. Do not claim server-saved edits. Reauthenticate then reload authorization and reconcile actual status. |

**Provenance:** Three independent labels: environment `FIXTURE` or authorized production/test environment; data availability `Available / Stale / Unavailable / Conflict`; origin `Recorded / Derived / RM-entered`. `LIVE` is permitted only for the actual successful, authorized provider data response it describes, with genuine source/as-of—not a global green market chip or a running clock. LIVE does not imply current suitability, fresh evidence or production certification. Fixture artifacts carry `FIXTURE — synthetic, not for client use`, cannot write/send/handoff into live systems and do not count as live acceptance or metric successes. Unknown confidence displays `Confidence not supplied`; never invent a percentage. Partial evidence and low confidence remain distinct.

### 4.1 P-001 · Sign in and session recovery

- **Layout:** compact institutional sign-in card; app identity, session message, one `Continue with institutional sign-in` button. No local password form or self-registration requirement.
- **Fields:** tenant/institution choice Cond only if the institutional identity flow requires it; approved choices, no free text/default tenant. Return destination RO, application-local and sanitized. Identity, role and book RO after successful authentication.
- **Actions:** sign-in → reload current permissions → original allowed destination; if not allowed, P-002 or P-020. `Cancel` from a failed identity handoff returns a nonsensitive start state. Logout ends visible session and clears protected UI; no promise that a provider-side operation was canceled.
- **States:** redirecting; canceled; identity provider unavailable + Retry; authenticated but no assigned scope → P-020. Reauthentication never automatically retries an uncertain send or starts recording. Draft recovery only from permitted durable state under institution policy.

### 4.2 P-002 · My Day and single copilot entry

- **Layout:** existing branded header; navigation My Day/Clients/Calendar/Priorities; entitlement-gated Administration/Oversight. Main top row: localized date/timezone and session RM name; `Start workflow` launcher. Next: resume workflow cards and daily priorities; then today's schedule. Existing KPI, allocation/performance and relevant news cards remain secondary, only with actual available data. No invented deltas, totals, next meeting, names or ready status.
- **Fields:** displayed date/time RO from session timezone; counts/AUM/performance RO with definitions/currency/source/as-of. Unknown amounts `—` + reason, confirmed zero `0`. Launcher: task Req choice Prepare meeting/Follow up meeting/Draft outreach/Find products, plus permitted pilot tasks only when enabled; client Req except daily-book priorities; meeting Cond for a meeting-specific task. No generic `Ask anything` field.
- **Actions:** task selection + entitled context → create/resume P-006; exact event card → P-003/P-007; selected priority → P-013 reason or P-005; resume shows actual outstanding decision. Generation is explicit and not triggered by render/open/reload. `Refresh` independently refreshes My Day sections without rerunning business actions.
- **U specialization:** no assigned clients → `No clients are available in your assigned book`; no workflows → `Start a workflow`; no events → `No eligible meetings for this date`. Missing portfolio/news does not erase priorities/calendar. A whole service outage still leaves shell/status and safe navigation; no populated demo cards beneath an error. No creation/assignment CTA outside scope.

### 4.3 P-003 · Calendar and identity resolution

- **Layout:** date selector and timezone, day agenda list; each event shows entitled title, start/end, known attendee hints, match status and `Prepare meeting`. No calendar create/edit functionality added.
- **Fields:** selected date Req valid date, defaults current local day; timezone RO session setting; event reference RO provider identity/version; client selection Cond Req when not uniquely verified, approved search choices. No automatic attendee-to-household merge; ambiguous choices have only permitted distinguishing information.
- **Actions:** unique authorized verified match → confirm visible client → P-006/P-007. Ambiguity → dialog lists candidates, `Use selected client` or `Cancel`; preserve event reference. No match → `Find client` P-004; no permitted match blocks generation. Canceled/ineligible event shows status and no active prepare action.
- **U specialization:** loading agenda; successful no events; calendar unavailable + client lookup fallback; identity source conflict → show authorized conflicting records and block suitability/ticket until authoritative resolution. Never bind event to `rankedClients[index]`.

### 4.4 P-004 · Client lookup

- **Layout:** labeled search and entitled client list; rows show name, permitted identifier, book/context and data state; mobile stacked cards. Search results never expose another book/tenant.
- **Fields:** search Opt short text, defaults blank; scope RO assigned book. Empty search lists allowed records, not a fabricated sample. Paging uses permitted available results; selection is an entitled reference. Client type/risk labels only from sources, not assumed Moderate/Private Wealth.
- **Actions:** select row → P-005; if launched by context picker, explicit `Use client` returns context to the originating workflow; cancel restores original selection. Context switch uses §2.2 and never reuses prior client artifact content.
- **U specialization:** empty book distinct from no search match; clear search CTA; query failure Retry, never `No clients` on exception; source unconfigured unavailable, not empty.

### 4.5 P-005 · Client workspace and persistent memory

- **Layout:** authoritative identity header and entitled account context; tabs Overview / Interactions & actions / Client memory / Briefs & workflows. Portfolio/AUM, profile freshness, contact permissions and latest accepted preferences have source links. Pilot preference/entity entry appears only to enabled cohorts. Existing charts may be reused with accessible tabular equivalents.
- **Fields:** identity, account, holdings, balances, risk/KYC, DNC/channel choices RO from authoritative sources. Memory items RO text/type, source, confirmation state, confirmed actor/time, current/conflicting/superseded state; **no invented universal memory editor**. Proposed preference corrections are Req text + entitled evidence/reference if sourced, reviewed via P-010 old/new preview; RM-entered facts are labeled as such. Shariah sensitivity pilot choice uses institution-approved values including explicit unknown; default unknown, never inferred from religion/name. A preference change requires preview/explicit confirmation and propagates only after durable acceptance.
- **Actions:** `Prepare meeting`, `Follow up`, `Draft outreach`, `Find products` → same P-006 launcher; opening existing brief → P-007 view-only until explicit regenerate. `Review proposed change` → P-010. Source → shared drawer; authoritative conflicting record links for resolution. No client-account creation, bulk deletion, automatic memory training or silent back-propagation of rejected items.
- **U specialization:** no holdings/actions/interactions/memory each has honest empty subsection; expired KYC prominent and ticket unavailable; memory provider failure does not label context confirmed; conflicting facts remain unresolved, block dependent assessment/ticket. Unknown contact policy blocks send, not client viewing.

### 4.6 P-006 · Workflow workspace and stage strip

- **Layout:** client/context identity always visible; workflow type/reference and actual last saved time; primary task view with compact stage strip. Detail region shows stages with concise rationale, needed inputs, generated artifact links and human decision. Right/secondary drawer provides entitled context/evidence. Stage names follow the task, not the existing hardcoded four-step header.
- **Fields:** task/client/meeting Req references inherited from launcher; stage/artifact/version/actor/status RO; optional task context text only for the selected RM task, no unrestricted chatbot history. Inputs already known from the same authorized memory are reused visibly; unknown fields stay blank. Versioned skill/stage names and actual invocation chain visible in expandable workflow activity without hidden chain-of-thought.
- **Actions:** `Continue` goes to actual next pending stage; `Review` opens the relevant artifact; `Pause workflow` persists workflow state, not cancellation of an already approved provider action; `Abandon workflow` confirmation records abandonment and leaves completed actions/audit intact. `Use manual workflow` opens notes/search/draft appropriate to the failed stage and records a manual intervention, rather than fake cross-skill completion.
- **U specialization:** no stages yet → not started + task input; startup failure → Retry launch using same intended request; partial completed stages remain; stage disabled by operator → `This copilot stage is paused; manual work is available`. Unsupported task → safe launcher, not a fallback generic answer. Missing persistence/audit gates disable approval; workflows do not acquire fake IDs.

### 4.7 P-007 · Canonical brief

- **Layout:** context header: client, meeting time or `No meeting linked`, source cutoff/as-of, generated by actual RM, version and review state. Five ordered cards: (1) Portfolio/AUM & allocation; (2) Material changes & risk; (3) Recent interactions & open actions; (4) Relevant entitled market news; (5) Proposed agenda. Every material item has evidence access and Recorded/Derived distinction. Persistent bottom action bar does not obscure content.
- **Fields:** agenda Opt long text/list, initially actual generated result or blank—not a hardcoded agenda; per-section decision Req before section approval, defaults unreviewed, choices Approve/Reject. Edit applies to generated narrative/agenda, not authoritative holdings. Feedback choice Opt Helpful/Not helpful, structured reason Req for submitted feedback under approved catalog. Version selector Opt existing actual versions, default latest available; historical versions read-only with prior approvals. Current version IDs/source times/approver RO.
- **Actions:** `Generate brief` only when no selected brief and context is verified; `Regenerate` creates a new audited draft version, never overwrites approved evidence or writes CRM. `Retry section` preserves other cards and records revised version basis; `Review sections` → individual approvals/rejections, `Approve reviewed sections` commits only explicitly selected current sections. `Continue to meeting` → P-008; partial-data limitations remain visible and unapproved/unsupported material is excluded from downstream client-facing artifacts. No auto-start recording.
- **U specialization:** section loading/empty/error independent; successful no news → `No relevant entitled news found`, failed feed → `Market news unavailable`. Source failure never becomes `No significant changes`. Generation failure no new brief → Error + retry, approval disabled. Prior approved version remains clearly prior. Unavailable source/provenance disables approval of affected unsupported assertions, not browsing unaffected cards. Fixture notice follows every presentation.

### 4.8 P-008 · Consent, capture and manual notes

- **Layout:** meeting/client header; policy panel with jurisdiction, approved consent text/version and retention explanation; explicit consent controls before recording controls. Persistent textual recording state and elapsed confirmed capture; transcript status/last confirmed time. Manual notes panel always reachable.
- **Fields:** jurisdiction Cond Req approved choice when not authoritative, no guessed default; meeting format/language Req approved supported options, default verified meeting metadata only if supported. Consent decision Req explicit Accepted/Declined, initially not recorded; method Req from allowed policy methods, not default verbal; applicable participants Req per approved consent policy, unknown coverage blocks capture. Consent actor/time/policy version RO server-confirmed. Manual notes Opt long text, starts blank or last saved draft; `Save notes draft` enabled for nonblank valid notes. Consent withdrawal reason Opt unless policy requires. No editable consent timestamp.
- **Actions:** `Record consent` persists decision; only valid accepted consent + permission + provider/policy readiness enables `Start recording`. `Pause`, `Resume`, `Stop recording` operate on the existing meeting. `Withdraw consent` stops capture immediately and audits state; reviewed downstream artifacts affected by policy/consent are invalidated or blocked until re-reviewed with permitted content. `Continue with manual notes` → P-010; note saving alone does not submit CRM changes. `Review transcript` → P-009.
- **U specialization:** unknown consent policy → capture blocked/manual notes; declined → capture unavailable/manual notes; microphone denied/audio loss → recover controls with confirmed position, manual notes retained; provider disconnected → partial transcript label, no `Complete`. Save failure notes remain in session only with `Not saved` warning; no uncontrolled local sensitive caching. Deletion/retention follows approved policy/legal hold; UI does not promise erasure of audit or stored audio by deleting text.

### 4.9 P-009 · Transcript and evidence-linked extraction

- **Layout:** desktop transcript left, extracted items right; linked selection highlights timestamped speaker excerpt. Mobile (if permitted) sequential evidence panels. Banner distinguishes partial transcript/processing/complete verified provider result. Manual notes appear with RM-entered origin, never speech timestamps.
- **Fields:** transcript search Opt short text, default blank. Transcript excerpt RO speaker/start/end/text/confidence if supplied; RM correction editor Cond long text, nonblank to replace; source original and edited versions remain distinguishable under retention policy. Item type Req approved choices Decision/Action/Preference/Commitment/Follow-up topic. Item content Req long text; owner Opt entitled person/reference or explicit RM-entered owner per mapping; due date Opt valid date; source Req evidence link for transcript-derived item, inherited and inspectable. Owner/date remain blank when not spoken; RM additions are labeled. Item decision Req before downstream use: Accept/Reject; edited items need explicit acceptance. Correction/rejection reason Req structured reason when submitting the corresponding change.
- **Actions:** `Edit`, `Accept`, `Reject`, `Delete sensitive content` with impact confirmation; delete excludes content from regenerated follow-up context subject to retention/legal hold, not an audit purge. Low confidence → `Needs review`; acceptance does not transform unsupported inference into a sourced client fact. `Continue to review` → P-010 using only accepted permitted items; all rejected → manual review/empty output, not artificial notes.
- **U specialization:** empty transcript → manual notes, no extraction; partial extraction valid items preserved; failed model → manual structured notes fallback; source excerpt unavailable or consent withdrawn → dependent item blocked. Processing uses actual progress/last confirmed time, no fake percent. Sensitive deletion lists affected drafts and invalidates approvals before regenerating.

### 4.10 P-010 · Unified post-meeting review and action status

- **Layout:** single review workspace with adjacent/stacked artifact cards: Notes / CRM field diff / Tasks / Client preferences & memory / Email draft / Eligible ticket fields. Evidence drawer stays in place. Summary shows accepted/rejected/pending item counts and no hidden actions. Separate per-action result timeline below.
- **Fields:** each artifact decision Req accept/reject, default unreviewed; notes Req nonblank for approved notes; CRM fields Cond per approved mapping, authoritative old value RO, proposed value typed to mapped field. Tasks: title Req nonblank, owner/due date Opt unless configured provider mandates them, never guessed; mandatory absent provider fields block task creation until RM supplies explicit value. Preferences: proposed text/value Req, previous canonical value RO, origin/evidence Req if derived. Opportunity fields appear only when accepted content and configured mappings support them—no new sales pipeline UI. Email/ticket summaries RO current draft/version/blockers; edit links to P-011/012. Approval actor/time and exact artifact versions RO.
- **Actions:** individual `Accept`, `Edit`, `Reject`, `Reject all` (confirmation, no external effect). `Preview selected changes` shows old/new values, correct client/destination, task fields, memory consequences and explicit **no email send/no trade execution** scope. `Approve selected changes` authorizes only previewed notes/CRM/tasks/memory; subsequent execution reports each result. Message saving/approval never sends via this button. `Review email`/`Review handoff` opens dedicated gate. Every AI brief/note/recommendation/message/write/handoff has persisted identifiable review state.
- **U specialization:** no accepted items → `No changes selected` + return to transcript/manual notes; mappings unavailable → affected action blocked. CRM conflict → show new authoritative old value vs proposal, require re-review. Partial writes show exact succeeded/pending/failed artifacts, not `All updated`; safe retry only failed reconcilable actions. Memory confirmation pending does not appear as confirmed in next brief/ranking. Approved results remain visible after reload with readback; missing readback → reconciling, not success.

### 4.11 P-011 · Message draft and approved send

- **Layout:** contact policy/context banner; channel/template row; draft editor; evidence-linked facts/accepted meeting outcomes; required disclosure panel; final send preview and delivery status. A brief reason summary remains above the editor for outreach; post-meeting mode uses accepted decisions/actions only. No unsupported sensitive text is added to fill a template.
- **Fields:** channel Req Email/SMS only when configured and consented; template Req from approved templates for channel/jurisdiction, no default unapproved template. Approved reason Req for priority-based outreach, actual reason reference inherited; meeting outcomes Req basis for post-meeting draft. Recipients Req explicitly confirmed permitted destination(s); subject Req for email unless provider policy explicitly does not require it, not shown for SMS; body Req long text; disclosure Cond Req policy-approved text/version, cannot remove mandatory disclosure and retain send eligibility. All source-backed facts have evidence references; unsupported fact warnings require removal/correction. Final preview confirmation Req unchecked, actor/version RO. No new scheduling fields.
- **Actions:** `Generate draft` → same copilot stage; `Save draft` stays draft. Edits invalidate approval. `Review send` checks current DNC/channel consent/disclosures/restricted content/entitlements/evidence and shows exact recipients/content/channel/client. `Approve and send` is the only client-send action and records authenticated RM approval of that exact preview. Provider unavailable disables send but preserves permitted draft. `Record outcome` → shared outcome dialog on P-013 after appropriate event; a sent message alone is not a meaningful touchpoint.
- **U specialization:** no grounded basis → empty draft/manual editor with limitations, not invention; DNC/opt-out/unknown policy → blocked with no bypass or alternative nonconsented channel. Policy changed after preview → invalidate send approval. Provider failure safe retry; outcome unknown Check status. `Sent` only with authoritative confirmed outcome; existing provider scheduled status accurately labeled, not treated as sent. Approval never substitutes for a compliance/provider gate.

### 4.12 P-012 · Ticket prefill and external handoff

- **Layout:** emphatic `Prefill only — no trade is submitted or executed`; evidence of explicit meeting discussion; current assessment summary; required product/account/amount fields; destination preview; blocker list. Trade tool remains a separate entitled authoritative system.
- **Fields:** product Req entitled current product explicitly supported by discussed evidence; account Req eligible authorized account; amount Req money >0 within product/account/policy rules with required currency; suitability assessment Req current for exact client/product/account and material inputs. Additional mandatory ticket fields Cond as supplied by approved entitled handoff integration, typed/validated there; no speculative order-side/limit-price schema or inferred mandatory values. Meeting evidence Req link; destination and action outcome RO.
- **Actions:** edit permitted prefilled values with RM-attribution; changed material inputs invalidate assessment and handoff approval → P-015. `Review handoff` displays actual destination and fields, constraints and evidence. `Approve and open ticket tool` transfers only approved eligible prefill; label outcome `Handoff confirmed`, never `Trade placed`. No submit/execute/AI-trade-approval control.
- **U specialization:** no discussion evidence → `No eligible ticket to prefill`; no provider → unavailable; missing account/mandatory field/current suitability/conflicting identity → blocked with links to permitted source/assessment; hard stop no bypass. Failed handoff retains prefill; uncertain launch status not a trade success. Desktop-only when approved device policy so requires.

### 4.13 P-013 · Daily priorities, reasons and RM controls

- **Layout:** evaluated local date/time/timezone and ranking-policy version; up to **10 unique authorized eligible clients**, with rank, Risk/Opportunity/Retention labels, concise main reason, supporting signals and last evaluation. One-click reason drawer includes source/as-of, freshness and why rank changed. Public rules summary explains RM controls; no protected-attribute inputs or opaque score-only UI.
- **Fields/dialogs:** snooze-until Req future date-time, no preset duration until approved ranking policy defines one; dismiss reason Req structured reason; pin Req explicit on/off action, defaults actual persisted state; contact outcome Req one of Contacted/Meeting booked/No response/Not relevant, defaults unselected; occurred-at Req valid actual date-time not future, defaults current session time clearly editable/confirmed; optional outcome note long text, meeting reference Cond when a booked/attended event can be linked. Do not infer two-way contact or attendance from `Contacted`; meaningful-touchpoint classification uses confirmed evidence/approved definition, otherwise not counted.
- **Actions:** `Why this client?` → reason drawer; client → P-005; `Draft outreach` starts/resumes shared P-006/P-011 with approved eligible reason; snooze/dismiss/pin/contact controls show save status and re-evaluation results. Pin never bypasses eligibility, DNC, entitlement or the ten-client cap; policy must define placement/cap conflicts before activating pin behavior. Contact outcomes persist with original recommendation and actor, not overwritten client intent.
- **U specialization:** no eligible clients → criteria + actual last evaluation + Refresh, no weak leads. Refresh failure → prior list marked stale/error, not an empty success. Strict safe default: DNC clients excluded from default Top 10/outreach (FR-11); a later restriction blocks an already-open draft even if a prior risk reason still exists in audit. No separate contactable risk list added to resolve B-07 wording. Material policy unresolved → unconfigured ranking/manual client lookup rather than guessed priorities.

### 4.14 P-014 · Product discovery, filters, results and comparison

- **Layout:** client/current profile banner; task query; interpreted editable filter chips/form; `Search with these filters`; sourced results; comparison tray. Same copilot workflow retains context into assessment; no independent recommendation agent.
- **Fields:** NL query Req nonblank long text for interpretation; client Req for client-specific search, selected context visible. Interpreted filters Cond values supported by current entitled universe: product/asset class, currency, investment amount, risk constraint, yield/return metric + minimum, liquidity, fees/minimum investment constraints, verified ESG attributes if requested. Every numeric filter names its metric/unit; query ambiguity leaves unconfirmed filter requiring correction, no guessed profile age/risk. Authoritative suitability/hard restrictions RO, cannot be relaxed with a chip. Risk/KYC profile is RO; client facts in query do not overwrite it. Sort Opt available supported metric, default provider/published relevance order visibly identified; comparison selection Opt entitled returned products, no new arbitrary product-count business cap.
- **Actions:** `Interpret request` shows what will run; `Search with these filters` uses exactly displayed confirmed filters. Later changes mark results `Filters changed — run search`; no falsely current results. Edit/remove soft filter → explicit rerun. Result → P-015; `Compare selected` shows same metric definitions/as-of/fees/liquidity/minimums/risk/ESG evidence/source side by side. `Select candidate` records reviewed choice, not trade approval.
- **U specialization:** product search <5s p95 target, actual long job status otherwise; no results explain active constraints and suggest explicit soft-filter edits. No products/unconfigured license distinction. Missing metric displays unavailable, not zero yield; no guaranteed label unless terms support it. Noncurrent/unentitled offerings excluded. Pilot Shariah restrictions propagate by construction; non-compliant candidates not shown as recommendations with disclaimer.

### 4.15 P-015 · Suitability assessment and permitted override

- **Layout:** client/product/account context, profile and evidence freshness; rating as icon + color + text: `Green — no detected conflict`, `Yellow — review required`, `Red — conflict/prohibition`; always `Pre-screen, not compliance approval`. Factor table names rule, evidence/time, detected issue and hard/soft classification. Assessment version and relevant input changes visible.
- **Fields:** product/client Req inherited; account Cond when required by assessment/handoff; rating/factors/policy version/currentness RO. RM decision Req explicit Reviewed/Rejected for proposed recommendation; soft-override reason Req structured reason + nonblank rationale, no default; original rating immutable in history. Override privilege/policy eligibility RO. No editable rating field, no checkbox that turns missing KYC Green.
- **Actions:** `Reassess` on material input change; `Review recommendation` persists review of exact version. `Request permitted override` shown only where policy permits that warning and actor is authorized; preview shows original rating, rationale, policy, scope and final action; `Confirm permitted override` audits it without rewriting original rating. Hard prohibitions show `Blocked — cannot be overridden` and no override action. Overrides do not cure missing current KYC/account requirements for ticket handoff.
- **U specialization:** no selected candidate → P-014; failure → no valid rating, not Green; missing/expired profile Yellow at best + ticket blocked; unknown policy/owner → assessment unavailable, no invented hard/soft classification. Changed inputs invalidate prior result/approval and return to review.

### 4.16 P-016 · Shariah-sensitive pilot task view (default off)

- **Entry gate:** enabled cohort + entitled client + approved jurisdiction/SSB rule pack/methodology/evidence sources + rollback/readiness evidence. Off/non-cohort direct link → P-020; flag is not toggled by RM. Same workflow and memory as core.
- **Layout:** pilot banner `Calculation and evidence assistant — not a fatwa`; three task sections Screening / Zakat & purification / Proposal evidence. Client preference and rule-pack/SSB version always visible. Existing holdings that fail screening may be inspected as risk evidence but are never offered as compliant recommendations.
- **Fields:** preference Cond Req approved values, default unknown and confirmed via P-005/P-010; rule pack Req approved version for jurisdiction, no automatic unapproved fallback. Screening criterion RO name, pass/fail/insufficient evidence, business-activity/ratio values and thresholds, source/as-of/SSB reference; drift result links to prior screen and required policy action. Estimate fields: methodology Req approved choice; asset valuations Req sourced permitted holdings with zakatable/excluded classification and methodology basis; nisab Req sourced value/currency/date; hawl start/anniversary Req where method needs it; lunar/solar convention Req approved method value; purification ratio Req sourced/date per affected instrument; all unknown inputs blank. No universal zakat rate/threshold fabricated. Advisor confirmation Cond Req for a `Confirmed by advisor` claim, actual entitled recorded confirmation/reference and date—not an RM tick pretending religious authority.
- **Actions:** `Run screening` creates evidence-linked version; drift can feed a Risk reason through the shared copilot policy, never automatic trade/rebalance. `Generate discussion estimate` only with required approved inputs; itemizes included/excluded assets, assumptions, methodology and purification; every output says `Estimate for discussion — confirm with your Shariah advisor`. `Prepare evidence pack` collects per-holding screen, SSB approvals, purification/zakat notes; `Review finalization` checklist → explicit authorized finalize only if complete/current/versioned and archived/readback confirmed. Finalization is not send, advice approval or a religious ruling. Hawl conversation reminders are shared task/priority suggestions requiring RM confirmation before any calendar/CRM write or client send.
- **U specialization:** no holdings → honest empty; missing/stale source → insufficient evidence, never compliant; non-compliant candidate excluded from recommendation; incomplete pack → named checklist blockers + source actions, finalization disabled. Unknown method/nisab/hawl → estimate unavailable, no fake total. Pack archive failure → not finalized. Pilot disabled mid-workflow preserves permitted historical artifacts/audit, blocks new pilot actions and leaves core/manual workflows usable.

### 4.17 P-017 · Family/entity pilot task view (default off)

- **Entry gate:** enabled cohort + approved entity/custodian coverage + entitlement matrix + extraction quality/tolerance policy + governance readiness. Unauthorized nodes/edges must be excluded **before** copilot context assembly; UI hiding alone does not satisfy entry.
- **Layout:** pilot banner; tabs Structure & holdings / Governance packs & scenarios / Capital calls & 90-day liquidity. Entitled graph has accessible equivalent node/relationship table; no placeholder nodes, redacted labels/counts or total assets that reveal unauthorized entities. This is a relationship graph, not a geographical map.
- **Fields — structure/consolidation:** household Req entitled reference; document Cond policy-controlled attachment or existing entitled source; proposed node type/name/relationship Req for accepted extraction, allowed types from approved entity catalog; evidence Req document/page/excerpt, confidence if supplied; RM confirm/reject Req per node/edge before canonical use. Custodian/account/currency/holding/source/FX as-of RO; base currency Req supported currency, default existing approved household setting only; reconciliation difference/tolerance/version RO from approved policy. No invented conversion or automatic reconciliation.
- **Fields — governance:** attendee set Req entitled participants; attendee-class/pack-scope RO evaluated entitlement, no manual privilege expansion. Commitment text Req, owner/due date Opt unless spoken/explicitly entered, evidence Req for derived content. Scenario type Req institution-supported succession/transfer choice; jurisdiction Req approved choice; assumptions Req itemized user-reviewed values with source or illustrative origin; outputs always illustrative with caveats, never full financial planning. Next-gen engagement/outcomes use confirmed permitted interactions, not inferred sensitive demographics; family retention reasons use approved minimized policy.
- **Fields — capital calls:** commitment/fund Req entitled records; unfunded balance RO sourced; notice Req entitled document; extracted call amount/currency/due date/fund/recipient account Cond Req as required by approved notice method and explicitly RM-verified, not defaulted from pattern. Forecast window RO **90 days**; model pattern/assumptions/source history/as-of RO; actual call amount/date Cond when verified actual is available for comparison. Forecast remains forecast, not instruction to transfer funds.
- **Actions:** `Extract structure` → inspect proposals → `Preview confirmed structure` → approve canonical changes; unconfirmed nodes never enter consolidation. `Consolidate holdings` shows actual tolerance reconciliation and look-through evidence. `Preview attendee pack` evaluates selected attendee **before generation**, creates separate per-entitled-class versions; changes to attendee/scope invalidate previews/approvals. `Review pack` approval does not send. `Model illustrative scenario` requires reviewed assumptions. `Verify notice` preview → approval → forecast refresh → evidence-based Risk reasons in P-013. Any suggested system/calendar/task write still uses shared approval preview.
- **U specialization:** no household data → no sample graph; missing permission/source → exclude/blocked without disclosing hidden records. Graph loading/error separate from holdings data. Missing FX/custodian feed/tolerance → partial/unreconciled, no complete consolidated total. Unknown attendee entitlement → pack blocked before AI. Unverified notice → excluded from verified forecast inputs; insufficient history → no spurious confident window; forecast-vs-actual `Not yet observed` when actual absent, not zero error. No alternative-investment marketplace or auto-capital-call payment.

### 4.18 P-018 · Runtime administration, stage controls and readiness

- **Layout:** administrative scope banner; five configuration tabs sharing one versioned editor/diff/approval/history pattern. Separate operational section for model-feature/stage switches, pilot cohorts and release evidence. No client data unless expressly required/entitled; secrets never appear in version diffs or audit content.
- **Shared config fields:** class Req one of five below; tenant/book/jurisdiction scope Req from operator entitlements, default explicit current scope; status/version/current actor/time RO. Change reason Req nonblank; effective config values typed below; validation and required approval evidence Cond based on governing policy. Save draft does not activate a policy. Model/prompt/template/ranking/rule-pack versions reference evaluated artifacts; model/prompt selection is controlled change management, not an unrestricted prompt editor or new training feature.

| Configuration class | Editable fields / validation / default |
|---|---|
| Field mappings | Authoritative source/target Req approved connector/catalog; entity and source/target fields Req known allowed fields, field type compatibility and required target coverage validated. Write permission RO; no default arbitrary mapping or unknown-field pass-through. Old/new preview required. |
| Ranking/reason policies | Objective/version Req approved policy artifact; reason codes/signal sources/freshness/control effects Req per published approved rule catalog; weights/thresholds typed numbers within policy limits, no invented weights. DNC exclusion/protected-attribute prohibition non-overridable. Missing DEC-03 keeps ranking inactive. |
| Templates/disclosures | Name/channel/jurisdiction Req approved choices, template text Req nonblank, allowed tokens only from permitted mapped context; mandatory disclosure Req when policy says so. Unresolved tokens block generated client-facing use, never fill invented facts. Version/evaluation/Legal approval evidence Req for activation as governed. |
| Consent rules | Jurisdiction/methods/participant coverage/platform/language/retention-disclosure references Req as approved; consent text Req approved version; explicit Legal/Security policy references Req before activation. Unknown policy fail closed; no default accepted consent. Retention/legal hold are governance inputs, not free RM deletion preferences. |
| Integration credentials | Capability/provider/environment Req institutional approved connector configuration; scopes/authoritative owner/freshness SLA/API limits Req where integration applies; secret fields Cond required for configure/replace, masked, blank means **unchanged**, never clear implicitly. Removal/revocation explicit confirmed action respecting pending operation safety; no secret echo, history or prefilled browser secret. Provider entitlement/readiness status RO actual verification, absent configuration unavailable. No external live validation is authorized by this design-phase document. |

- **Switch/readiness fields:** model-feature or single stage Req selected existing versioned capability; enabled status Req explicit toggle with confirmation/reason; affected cohort/scope Req permitted set. Pilot defaults **off**, activation requires all approved pilot evidence/cohort/rollback gates; there is no admin override of missing readiness. Re-enable requires current evidence, not just reversing a checkbox. Release evidence items show accountable owner, jurisdiction/environment, reference/version/date, approval/expiry/blocker state from authorized source; no invented signatories or `SOC 2 certified` badge from code. External acceptance may be recorded as evidence references, not fabricated in-app certification.
- **Actions:** edit → `Validate changes` → diff/impacts → `Save draft`; `Activate approved version` only for authorized capability and evidence; show readback of active version. `Restore prior approved version` is a new audited activation with confirmation/current gates, not deletion of history. Stage disable preserves drafts/manual workflows/audit and identifies in-flight action status, never claims to unsend/undo a confirmed provider result. Pilot enable/disable is audited separately from core release gates.
- **U specialization:** no config → unconfigured values, no enabled defaults; invalid mapping → field errors; unavailable readiness → no optimistic `System ready`; config conflict → current-vs-edited diff and re-review; audit unavailable → activation blocked. Missing external provider/contracts/legal gates stay visibly unresolved. Operations monitoring/backup evidence is read-only status/reference, not new deployment or destructive database console.

### 4.19 P-019 · Audit and measurement (minimal control visibility)

- **Layout:** three scoped tabs Audit / Workflow measurement / Guardrails & gate evidence; filter bar; list/detail drawer. Reuse the operational tables/card vocabulary, not a new general BI/report builder. RM accesses own permitted workflow activity; broader compliance/security/operations views require explicit entitlement. No audio/transcript payload in analytics.
- **Fields:** period Req valid start≤end, default current local day; workflow/client filter Opt entitled reference; event family/status/version filter Opt approved known values, default all in permitted scope; audit reference RO tenant-safe actual ID; source/model/prompt/template/rule version, actor/time/approval/action outcome RO actual record. Detail access is permission-filtered; no raw secrets, hidden family nodes or chain-of-thought. Pagination shows actual count only when authorized/known; no invented totals.
- **Metric cards:** M-01 comparable prep duration; M-02 approved post-meeting admin duration excluding client wait; M-03 verified meaningful two-way/attended touchpoints; M-04 monthly brief numerator/denominator + per-eligible-meeting count; M-05 copilot workflow rate; M-06 cross-skill completion/manual-stitch interventions; M-07 matched/book-adjusted retention only after method/window/baseline; M-08 search-to-selected efficiency with baseline first; M-09 current Shariah screening coverage only in active pilot; M-10 family effort with baseline first. Cards show definition, window, inclusion/exclusion, sample/denominator, source update time, baseline status, observed value and separate **validation target**. No data is `Not measured`, never 0% success or a business claim.
- **Actions:** audit row → source/approval/change/outcome lineage; workflow row → entitled P-006; report unsupported fact from any artifact → structured feedback with actual artifact version, visible in GRD-09 review. Guardrail/gate item → evidence/owner/state, not `Mark all passed`. No automatic tuning, training, certification, unrestricted data export or in-app incident-response suite added.
- **U specialization:** loading; no authorized audit events in window; collection unavailable/error distinctly labeled; small/unknown cohort or absent baseline → no comparative claim. Fixture telemetry visibly segregated/excluded from live outcomes. Missing gate evidence remains pending/blocked. Unsupported-fact/correction rates have denominators and baseline; no causal retention headline from raw differences.

### 4.20 P-020 · Boundary and recoverable application failure

- **Layout:** shell where safe; one clear heading, nondisclosing explanation and safe actions. Cases: `Sign-in required`; `Record unavailable`; `Feature not available for this rollout`; `Capability not configured`; `We couldn't load this page`; `This device isn't approved for this task`.
- **Fields:** reason category RO; permitted safe destination; actual support reference Opt RO. Do not expose the existence/name/count of an unauthorized client/entity. A browser route ID is not trusted authorization.
- **Actions:** `Sign in`, `Back to My Day`, `Retry page`, `Use manual workflow`, or `Contact administrator`, only when relevant. Application-level exception preserves last durable same-scope artifacts, not fictitious local success. No automatic POST replay on reload, retry or session recovery.

## 5. Shared components and reuse rules

Props below describe **UI inputs/outputs conceptually**, not frozen programming interfaces. Exact component contracts follow architecture freeze. Every component uses common validation, copy and state primitives; no per-feature duplicate loaders/modals/forms.

| Component | Purpose | Reuse | Key conceptual props / events |
|---|---|---|---|
| ApplicationShell | Header/nav/session/scope/environment; safe responsive layout | P-002–019 | userDisplay, allowedNavigation, currentScope, environment, sessionState |
| CopilotTaskLauncher | Single task/context launch/resume | P-002/003/005/013 | allowedTasks, entitledContext, existingWorkflow, launch/resume/cancel |
| ClientContextHeader | Prevent cross-client confusion; source/profile state | all workflow/client views | clientIdentity, meeting, authorizedContext, profileFreshness |
| WorkflowStageStrip | Actual lifecycle, next decision, invocation activity | P-006–017 | stages, activeStage, confirmedOutcomes, blockedReason, nextAction |
| AsyncRegion / StatePanel | Shared loading/empty/error/degraded/unavailable/no-access display | every list/detail | state, actualAsOf, title, explanation, safeAction, supportReference |
| ProvenanceChip + SourceDetail | Verifiable sources/versions/as-of/SLA ownership, origin and limitations | briefs, memory, reasons, products, pilots, audit | entitledSources, freshness, recordedOrDerived, sourceVersion, sourceOpen |
| ReviewableArtifact | One per-section/item review pattern | P-007/009/010/011/015/016/017 | artifactVersion, sourceBasis, reviewState, actor/time, edit/accept/reject |
| CanonicalBriefView | The single five-section brief renderer and controls | route/full page/optional route-backed panel/mobile | selectedBrief, sectionStates, versions, reviewCapabilities, feedback |
| PolicyCheckPanel | Consent/DNC/disclosure/suitability/entitlement/readiness blockers | P-008/010–018 | namedChecks, policyVersions, allowedActions, blockedReasons |
| ApprovalPreview + Diff | Exact old/new/recipient/destination/version/action scope | review, send, ticket, memory, pilot, admin | currentVersion, proposedChanges, exclusions, actor, approve/cancel |
| DeliveryStatus | Durable per-action outcomes, safe reconciliation/retry | P-006/010/011/012/018 | intendedAction, provider/readbackEvidence, confirmedState, retry/checkStatus |
| StructuredReasonDialog | Dismissal/correction/override/feedback reasons | P-007/009/013/015 | reasonCatalog, otherRequired, explanationRules, confirm/cancel |
| ConsentRecordingPanel | Policy/consent state and unmistakable capture controls | P-008 and compact active workflow indicator | approvedPolicy, consentCoverage, captureState, confirmedPosition, stop/pause |
| EvidenceLinkedItemEditor | Extraction/manual item evidence and explicit corrections | P-009/010/017 | itemType, content, owner?, date?, evidence, confidence?, reviewState |
| MessageComposer | Post-meeting and outreach modes share one editor/send gate | P-011 desktop/mobile | permittedBasis, channel, template, destinations, disclosures, draftVersion |
| VersionHistory / ConflictDialog | Non-destructive versions; stale edit reconciliation | all generated/config artifacts | selected/currentVersion, priorDecisions, diff, refresh/review |
| AccessibleDataTable / ResultCard | List/detail/paging + mobile card mode | clients/calendar/priorities/products/audit/admin | columns, entitledRows, rowActions, sort, pageState |
| AccessibleChart / GraphWithTable | Chart/graph with same-data textual/table alternative | P-002/005/017 | verifiedData, units/currency, provenance, altTable, empty/error |
| AccessibleDialog / Drawer | Shared focus/keyboard behavior and safe dismissal | all overlays | title, initialFocus, dirtyState, confirm/cancel, focusReturn |
| ConfigEditor | Five config classes share version/diff/activation pattern | P-018 | typedFields, scope, currentVersion, validation, requiredEvidence |
| MetricCard / GateChecklist | Definitions/baselines/denominators/readiness evidence | P-018/019 | observed?, target?, baselineState, window, denominator?, evidenceOwner |

**Reuse enforcement:** The brief modal must not own a second request/state/approval implementation. Message variants share one composer and policy gate. All source links use SourceDetail. All versioned approvals use ApprovalPreview; all failures use the shared state vocabulary. Reusing a component must not combine distinct business approvals into one ambiguous button.

## 6. Copy specification

English is the interface baseline. Centralized copy keys/templates should be used across shared components; jurisdiction-specific consent/disclosure text is approved configuration, not designer-authored legal text. Square brackets are actual values when available, never placeholders filled with invented content.

| Context | Exact baseline copy |
|---|---|
| Primary launch / resume | `Start workflow` / `Resume workflow` |
| Contextual task | `Prepare meeting` / `Follow up meeting` / `Draft outreach` / `Find products` |
| Draft save | `Save draft` → `Saving draft…` → `Draft saved` only after durable confirmation |
| Unsaved edits | `Your changes haven't been saved.` Actions: `Keep editing`, `Save draft`, `Discard changes` where permitted |
| Missing source | `[Section] is unavailable. Other sections remain available.` |
| Stale source | `Stale data · As of [source time]. Review before use.` |
| Missing provenance | `Source evidence is missing. This item cannot be approved for client use.` |
| Origin | `Recorded fact` / `Derived summary` / `RM-entered` |
| Fixture | `FIXTURE — synthetic data, not for client use` |
| Unconfigured | `Unavailable — [capability] is not configured.` |
| Partial brief | `This brief uses partial data. Review the unavailable and stale sections.` |
| Brief empty / action | `No brief has been generated for this context.` / `Generate brief` / `Regenerate` |
| Review state | `Unreviewed` / `Needs review` / `Approved version` / `Rejected` |
| Brief approval | `Approve reviewed sections` / `Continue to meeting` |
| Ambiguous client | `More than one client matches this meeting. Select the correct client to continue.` |
| No access/not found | `Record unavailable. You may not have access, or the record may no longer be available.` |
| Consent not inferred | `Calendar acceptance is not recording consent.` |
| Unknown consent policy | `Recording is unavailable until an approved consent policy is configured. You can use manual notes.` |
| Declined / withdrawn | `Recording consent was declined. Use manual notes.` / `Consent withdrawn. Capture has stopped.` |
| Capture active | `Recording in progress` / `Recording paused` / `Capture stopped` |
| Partial transcript | `Partial transcript · Last confirmed position [time].` |
| No transcript | `No transcript is available. Continue with manual notes.` |
| Low confidence | `Needs review — confidence or evidence is insufficient.` |
| Blank owner/date | `Not stated` (display); editable input remains blank |
| Sensitive deletion | `Remove this content from future drafts. Retention and legal-hold rules still apply.` |
| Unified approval scope | `Approve selected changes` / `This does not send a message or execute a trade.` |
| Outage draft | `We couldn't complete [action]. Your draft is retained. Check the action status before retrying.` |
| Unknown action outcome | `Outcome not yet confirmed. Checking status prevents duplicate actions.` / `Check status` |
| Confirmed action | `CRM changes confirmed` / `Message sent` / `Handoff confirmed` only with actual evidence |
| Changed approval basis | `This item changed after approval. Review the latest version before continuing.` |
| Priority empty | `No eligible high-priority clients. Review the criteria and last evaluation below.` |
| DNC / opt-out | `Sending is blocked by contact policy.` / `This channel is not consented.` |
| Final send | `Review send` / `Approve and send` / `Sending…` |
| No product results | `No products match the current filters and eligibility requirements. You can edit soft filters; suitability restrictions remain in place.` |
| Suitability meaning | `Pre-screen, not compliance approval` |
| Rating labels | `Green — no detected conflict` / `Yellow — review required` / `Red — conflict/prohibition` |
| Missing profile | `Current suitability data is required. Ticket handoff is blocked.` |
| Hard stop | `Blocked — cannot be overridden.` |
| Soft override | `Confirm permitted override` / `The original assessment remains in the audit record.` |
| Ticket | `Prefill only — no trade is submitted or executed.` / `Approve and open ticket tool` |
| Pilot off | `This pilot is not available for your current rollout.` |
| Shariah caveat | `Calculation and evidence assistant — not a fatwa` |
| Estimate caveat | `Estimate for discussion — confirm with your Shariah advisor` (institution-approved localized wording remains DEC-05 gate) |
| Shariah evidence missing | `Current SSB-reviewed evidence is incomplete. Compliant labeling and proposal finalization are blocked.` |
| Family unreconciled | `Consolidation is incomplete. Review unresolved reconciliation differences.` |
| Scenario | `Illustrative scenario — review assumptions and jurisdiction caveats.` |
| Stage switch off | `This copilot stage is paused. Manual work remains available.` |
| Config activation | `Activate approved version` / `Restore prior approved version` |
| No measurement / baseline | `Not measured` / `Baseline required before comparison` / `Validation target — not an observed result` |
| Metric denominator absent | `Insufficient evidence to calculate this measure.` |
| Session expiry | `Your session expired. Sign in again to continue. Pending action status will be checked.` |
| Generic recoverable error | `We couldn't load [section]. Try again or continue with an available manual workflow.` |

Validation appears adjacent to the relevant field and in a linked summary after attempted submission: `Select [field].`, `Enter [field].`, `Use a valid [field].`, `Choose a future time.`, `This value exceeds the permitted [rule].`, `Field rules are not configured.` Disabled risky actions always have a visible reason; do not rely on hover-only tooltips.

## 7. Responsive behavior and accessibility

- **Design widths:** small <768px; medium 768–1199px; large ≥1200px. These are layout decisions, not supported-device certification. Validate at 320px and 200% zoom without page-level horizontal overflow. Approved device/OS and caching requirements remain DEC-08.
- **Large:** existing header/navigation; one main task pane plus evidence drawer/column; two-column charts; review diff/evidence adjacent. **Medium:** two-column dashboard cards, evidence drawer overlay. **Small:** compact header/menu, one-column cards, task launcher first, priorities/schedule before secondary charts; status text wraps; tables become labeled cards or explicitly scrollable tables without hiding actions. No fixed footer that masks content.
- Mobile must support client lookup, brief reading, priority evidence/controls and editing/approving outreach with the same preview and policy checks. Recipient/content/disclosure review remains complete on small screens; a sticky action bar reserves content space and never bypasses review. Recording/ticket can be desktop-only only under approved policy, with a clear explanation—not broken controls. Other advanced/admin workflows may be desktop-optimized, not silently approved on unsupported devices.
- Target **WCAG 2.1 AA**: semantic headings, landmarks, form labels and associated errors; keyboard-operable navigation, tabs, lists, menus and all chart/graph alternatives. Text contrast ≥4.5:1 (large text ≥3:1), control/focus contrast ≥3:1; validate actual colors rather than assume existing gray styles comply.
- Every icon-only control has an accessible name. Visible focus is never obscured. Dialogs have named dialog semantics, focus containment, safe initial focus, Escape/cancel when not in an irreversible transaction, and focus return. Backdrop click is not the only dismissal. Dirty-editor dismissal uses the common confirmation; capture continues only under explicit valid state, never hidden by accidentally closing a panel.
- Red/Yellow/Green and all environment/delivery states use text and icon in addition to color. Recording has persistent text and an assistive announcement, not only a blinking dot. Respect reduced motion; no animated LIVE clock suggesting freshness.
- Announce loading/saving/result changes through appropriate status regions; urgent access/capture/policy failures use concise alerts. Do not announce a running timer every second. Error summary receives focus on invalid submit and links to fields; user inputs retained when safe.
- Evidence chips are keyboard links/buttons; source drawer can open the entitled originating record or in-app detail without revealing unauthorized metadata. Graph has equivalent node/edge/evidence table; comparison tables retain headers; charts disclose units, date ranges and accessible data. Tooltips are not the sole evidence path.
- Format actual currency, number, date and timezone using session/institution locale. Show ISO currency when symbols ambiguous. Source times and RM-local display times are distinguishable; never re-stamp provider timestamps or mix calendar dates across timezones. Interface copy is centralized for future approved localization; translation scope is not added here.
- No sensitive service-worker/browser persistence or unapproved local storage/export is prescribed. Session/device controls, secure caching/retention, print/download and mobile authorization remain institutional decisions; unavailable policy blocks sensitive distribution, not a promise of safety from frontend behavior alone.

## 8. Traceability and control coverage

### 8.1 All 28 functional groups

| Stable ID | Page/flow implementation-facing coverage |
|---|---|
| FR-01 | P-002/003/004/006/007; verified client/event selection, explicit generation and real header/context |
| FR-02 | P-007 five sections and shared SourceDetail, Recorded/Derived origin |
| FR-03 | P-007 section states, regeneration/version/feedback |
| FR-04 | P-008 consent before capture, indicator/pause/stop and audit |
| FR-05 | P-009 speaker/time evidence, structured extraction, explicit owner/date corrections/deletion |
| FR-06 | P-008/009 last confirmed position, partial/failure/manual notes recovery |
| FR-07 | P-010 unified per-artifact review with side-by-side evidence and separate approvals |
| FR-08 | P-010 mapped old/new CRM/tasks, actual durable per-action status and safe retry |
| FR-09 | P-011 meeting follow-up mode using accepted outcomes, disclosures and confirmed recipients |
| FR-10 | P-012 evidence-backed product/account/amount prefill, current suitability and no execution |
| FR-11 | P-002/013 ≤10 unique eligible clients, local evaluation and material refresh |
| FR-12 | P-013 reason classes/evidence/rank-change explanation; P-005 one-click context |
| FR-13 | P-013 persistent snooze/dismiss/pin/outcome controls and public policy effects |
| FR-14 | P-011 priority outreach mode, grounded reason/permitted facts/opener and editable draft |
| FR-15 | P-011 policy recheck/exact explicit approved send/provider status; no auto-send |
| FR-16 | P-014 NL interpretation, editable actual filters and entitled current products |
| FR-17 | P-014 sourced metric definitions/as-of, fees/liquidity/minimums/risk/ESG and comparison |
| FR-18 | P-015 R/Y/G factors/freshness/reassessment and pre-screen caveat |
| FR-19 | P-015 policy-permitted soft override with rationale, hard stop non-overridable |
| FR-20 | Shared review/version/approval pattern across P-007/009/010/011/012/015/016/017 |
| FR-21 | §7 mobile lookup/brief/priorities/outreach parity, secure-session/device gate |
| FR-22 | P-018 all five runtime configuration classes, version/diff/activation/audit |
| FR-4.1 | P-005/016 preference propagation, criteria/SSB evidence, exclusions/drift risks |
| FR-4.2 | P-016 sourced itemized estimate, method/nisab/hawl/convention/purification and conversation suggestion |
| FR-4.3 | P-016 complete versioned archived proposal evidence, explicit finalization gate |
| FR-5.1 | P-017 entitled graph/extraction confirmation/consolidation/look-through/reconciliation |
| FR-5.2 | P-017 attendee-specific packs/commitments/illustrative scenarios/engagement outcomes |
| FR-5.3 | P-017 verified notices/unfunded commitments/90-day forecast-vs-actual and P-013 Risk reasons |

### 8.2 Cross-cutting controls: user-visible enforcement and evidence handoff

This is a design coverage map, not replacement acceptance text. The frozen inventory controls and tier definitions still govern acceptance. Infrastructure/contractual controls cannot be proven by a screen.

| Control set | Required UX and verification surface |
|---|---|
| D0–D5 | Session/scoped data before context; source identity resolution; consent before capture; current entitled products/KYC; correlated outcomes; one persistent confirmed client memory, all visible in P-005/006/018/019. Dependencies missing → honest unavailable/blocked paths. |
| B-01–B-04 | Partial/stale sections, conflicting sources, declined/withdrawn consent, insufficient confidence/evidence states in P-007–010/015. |
| B-05–B-10 | Durable action status and reconciliation P-010–012; empty priorities, DNC/channel checks P-013/011; no-product/current-profile restrictions P-014/015; model failure preserves manual work P-006/008. |
| B-11–B-12 | P-016 excludes non-compliant recommendations; P-017 pre-generation node/attendee entitlement filter and blocked audit event; pilot-only. |
| NFR-01/02/03 | Region-level loading, real progress and partial independence; performance/availability targets separately measured, capacity/uptime not certified by UI. P-018 readiness and P-019 evidence. |
| NFR-04/05 | SSO/session/device boundary, no secret exposure/uncontrolled caching; region/retention/Legal/Security/provider approval evidence P-018. Contractual residency/encryption/security approval remains external. |
| NFR-06/07 | Immutable-history presentation; actual sources/versions/actor/approvals/readback; concise explainability without chain-of-thought P-019/shared components. |
| NFR-08/09 | §7 mobile defined-task parity and WCAG interaction contract. |
| NFR-10/11 | Actual provider/staleness/error states and safe support reference; no false recovery success. P-018/019 observability, backup/restore/DR evidence references; restore execution not designed here. |
| GOV-01–04 | Exact human approvals/no autonomous effects, externally verified provider retention/training gate, grounded explanations and structured feedback; no automatic tuning from feedback. |
| GOV-05–08 | P-018 version/evaluation/approval/rollback and stage kill switches; P-019 monitored quality/block/conflict/drift and minimized lawful fairness evidence. No protected ranking features. |
| INT-01–06 | Shared source labels for core identity/portfolio/market/CRM/calendar; exact provider scopes/readiness; ambiguity resolution; approved CRM/send outcomes only. |
| INT-07–11 | Current suitability/product evidence; SSB/custodian data gated to pilot; identity revocation invalidates context; every data-as-of detail shows actual owner/freshness SLA/source lineage, unknown explicitly labeled. |
| M-01–10 | P-019 metric definitions, baselines, sample/denominator/window/limitations, observed-vs-target distinction; pilot metrics only in pilot context. No causal retention claim. |
| TEL-01 | P-007 request/generated/view/section completeness/latency/regenerate/feedback distinguishable; actual view is not approval. |
| TEL-02/03 | P-008 shown/accepted/declined/withdrawn/capture start/stop/failure; P-009 item acceptance/edit/rejection/correction reason. No sensitive audio in analytics. |
| TEL-04 | P-010 CRM preview/approved/confirmed/failed; P-011 email edited/approved/sent/failed; P-012 handoff blocked/confirmed. Timeout ≠ confirmed success. |
| TEL-05/06 | P-013 viewed/reason opened/control/outcome/time-to-contact; P-011 outreach generated/edited/approved/blocked/sent plus response/meeting outcome. |
| TEL-07/08 | P-014 query/filter correction/results/no-result and P-015 rating/override/hard-stop; P-006 workflow started/stage-approved/completed/abandoned + skill chain/manual interventions. User-visible labels never fake orchestration metrics with chat volume. |
| TEL-09/10 | Pilot screening/drift/estimate/advisor confirmation/consolidation/entitlement blocks; actual version/source/correlation tags on relevant lifecycle events. Hidden denied context does not appear in telemetry content. |
| GRD-01–10 | P-019 baselines/denominators and monitored privacy/access/recording/hard-stop/send/pilot evidence/leakage/correction/unsupported-fact/meaningful-contact metrics. Alert delivery/threshold approval is operational governance, not fabricated safe defaults. |
| GATE-01–04, GATE-X | P-018/readiness separates runnable baseline, P0, core GA, pilot and externally certified production evidence; representative two-persona trust/value review/training/support evidence before expansion. No checkbox expansion around a missing legal/SSB/security gate. |
| C-01–05 | Single task launcher/workflow, shared client context and memory; identifiable versioned stages; closed loop P-010→005→013→007. Five-layer architecture and persistence are architect-owned verification, not UI-only claims. |
| C-06–09 | Workflow-based completion/manual-stitch measurement, sourced explanations and per-artifact exact human approvals; numeric percentages remain targets with actual measurement path. |
| C-10–14 | Version/evaluation/rollback/stage disable and external provider controls evidence; actual core foundation release evidence. Design does not retroactively claim the Q1 release occurred. |
| C-15–18 | Pilots are same copilot/memory/task components, not independent modules/chatbots; quality not chat volume; node filtering and non-fatwa assistant limits. C-17/18 pilot-only, no core-GA scope inflation. |

## 9. Design decisions, open inputs and handoff boundaries

### 9.1 Decided within product-design authority

- Preserve useful current visual structure; prioritize truthful data/state rendering and complete workflows over decorative redesign.
- Canonical route-based brief + one shared renderer; optional quick panel cannot diverge from the page. No generation on mere view/navigation, no fake IDs, actor names, source stamps or fallback client content.
- Default Top 10 excludes DNC clients in accordance with strict FR-11. B-07 still blocks newly restricted drafts; an audit reason is not permission to contact. Any proposal for a separate noncontactable risk queue requires requirements clarification, not silent scope addition.
- Explicit independent human decisions for CRM/memory changes, client sends and ticket handoffs. Approval never means provider completion; retry is reconciled and never duplicates confirmed effects.
- Pilots off by default, with governance/entitlement/cohort/readiness and rollback prerequisites. No production, compliance, religious or financial assurance is inferred from the interface.

### 9.2 Institutional inputs that remain unresolved, not invented requirements

| Input | Design behavior until supplied | Owner / downstream handoff |
|---|---|---|
| DEC-01 platforms/languages/participant consent/retention | Capture blocked; manual notes/review remain available | Legal/Security/institution; exact approved config and validation rules before activation |
| DEC-02 providers/field ownership/write scope/retry owner | Honest unavailable integrations; drafts retained; no real sends/writes promised | Architecture/Operations/institution; contract freeze must define real outcome/reconciliation/readback |
| DEC-03 ranking weights/freshness/control effects/reasons | No invented ranking/control effects; published approved policy required before pilot use | Product/Data/Compliance; lead relays unresolved policy to requirements analyst |
| DEC-04 product universe/current KYC/hard-stop matrix | No Green on missing profile; no unconfigured override; ticket blocked | Compliance/Product/provider owner |
| DEC-05 SSB standard/estimate method/wording | Pilot off; no compliant label/estimate/final evidence claim | SSB/Legal/pilot owner |
| DEC-06 entity/custodian/attendee rights/tolerance/quality | Pilot off; exclude unknown access; no canonical extracted graph/reconciled claim | Institution/data owners/pilot governance |
| DEC-07 retention window/baseline/matched method | Measurement pending; no causal or improvement claim | Product/analytics/institution |
| DEC-08 approved OS/device/cache/approval rules | Responsive design can be tested; mobile release remains gated, sensitive unsupported actions blocked | Security/Product |
| Technical brief envelope and lifecycle contracts | Single conceptual brief UI only; no frontend workarounds for conflicting shapes | Architect chooses/finalizes API/models before implementation; `response.brief.sections` remains a proposal |
| Exact historical G-label register | No guessed G-to-FR map | User/lead may later supply; stable FR/control scope already covered |

Where policy catalogs, numeric field limits or provider-specific mandatory fields are not defined in the approved requirements, this design defines validation behavior and a visible unavailable gate, **not arbitrary business values**. These inputs must be resolved with the requirements owner through the lead before activating the affected feature. They do not prevent implementing/reviewing the common fail-closed interaction pattern. No new business capability is assumed to fill a gap.

### 9.3 Phase-2 completeness and next gate

All 28 FR groups have page/flow coverage; all list/detail pages inherit loading, empty, error, degraded, blocked and unconfigured states with page-specific outcomes. Canonical components, exact approval scopes, origin/provenance, mobile/accessibility, audit/measurement and default-off pilot behavior are specified. This is **design completeness**, not evidence that the application boots, persists data, passes tests, integrates live providers or meets release targets.

**Next:** Lead reviews this persisted deliverable; architect freezes APIs/models/action lifecycle/source provenance/permission and policy contracts; delivery batches follow that freeze. Implementers must not independently choose competing brief shapes, invent policy defaults or bypass the freeze. Preserve all existing data and audit history; schema/migration and production decisions remain outside product-design authority.

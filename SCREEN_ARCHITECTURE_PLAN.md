# Capco RM Workbench MVP - Screen Architecture Plan

## Overview
Based on the Product Design Specification, this is a **single-window, state-driven application** with 14 screens designed for a leadership demo. The system demonstrates a live market event propagating through the entire advisory workflow with human approval gates.

---

## Screen Inventory

### **Projected Screens (On-Camera for Demo)**

#### **SCR-01: Persistent Copilot Frame** *(Always Visible)*
**Purpose:** Single-screen chrome that appears on EVERY screen
**Components:**
- Mode chip: `LIVE` / `REPLAY — recorded 09:58`
- Synthetic data label: `SYNTHETIC DEMO DATA`
- Workflow trace: Shows correlation_id and current stage
- SGT clock: Real-time Singapore time
- Health anchor: System status indicator

**Key Features:**
- Never changes between screens
- Read-only on presenter surface
- Honest labeling (no hiding demo nature)

---

#### **SCR-02: My Day Home** *(Entry Point / Hub)*
**Purpose:** Top N priority clients with live market events and reason codes
**Layout Regions:**
1. Day summary strip (date, meetings, RM name)
2. Live market event banner (transient, ≥2.5s hold)
3. Priority client list (≤10 clients)
4. Proactive cards
5. Workflow stage trace (compact)

**Key Data Per Client Row:**
- Rank number + rank delta (e.g., "↑3 from 4")
- Client name + meeting time
- Reason code (Risk/Opportunity/Retention)
- Contributing signal (e.g., "Portfolio drifted 6%")
- Evidence chips with timestamps
- Confidence level
- DNC/consent status

**Actions:**
- Click client card → Go to SCR-03
- Click rank change → Open SCR-05 (drawer)
- Click market event banner → Open SCR-04 (drawer)
- Click any source chip → Open CMP-02 (drawer)
- Pin/Snooze/Dismiss/Mark contacted

**Conversation History Features (Missing in Original):**
- Recent conversations section per client
- Last 3-5 interactions with dates and topics
- Client sentiment notes
- Anticipated needs based on history

---

#### **SCR-03: Client Workspace & Five-Section Brief**
**Purpose:** Pre-meeting brief with sourced information
**Layout Regions:**
1. Client header (name, AUM, entitlement scope)
2. Brief metadata bar (version, state, correlation_id)
3. Five section blocks with per-section status
4. Evidence chips on every fact
5. Editable agenda field
6. Approval bar (Gate 1)
7. Memory chips panel

**Five Brief Sections:**
1. **Portfolio Overview** - AUM, allocation vs targets
2. **Material Changes & Risk Alerts** - Live market events, drift
3. **Recent Interactions & Open Actions** - CRM history, tasks
4. **Entitled Market News** - Licensed news headlines
5. **Proposed Agenda** - AI-generated, editable suggestions

**Key Features:**
- Every fact has source chip + timestamp
- Per-section status: `available` / `stale` / `unavailable`
- Memory correction capability (click chip → edit)
- Version history
- Regenerate section capability

**Actions:**
- Edit agenda line
- **Approve brief (Gate 1)** → Proceeds to meeting
- Regenerate/retry section
- View version history
- Correct/delete memory fact
- Capture feedback (Helpful/Not helpful)

---

#### **SCR-07: Consent Banner & Capture State**
**Purpose:** Recording consent gate during meeting
**Layout:** Banner overlay on current screen

**Flow:**
1. Meeting opens → Consent banner appears
2. Client decides: Accept / Decline / Withdraw
3. If accepted: Recording indicator ON, transcript capture enabled
4. If declined/withdrawn: `MANUAL NOTES` mode, no audio

**Key Features:**
- Consent language versioned
- Method + timestamp recorded
- Can withdraw mid-meeting
- Stub declaration visible (no real ASR)

**Actions:**
- Accept consent (Gate 2) → Recording starts
- Decline → Manual notes only
- Withdraw mid-meeting → Capture stops

---

#### **SCR-06: Unified Post-Meeting Review & Approve** *(Centerpiece)*
**Purpose:** ONE surface showing all meeting outcomes for single approval
**Layout:** Six blocks in one screen

**Six Blocks:**
1. **B1: Notes/Extracted Items**
   - Preferences noted (e.g., "Family: daughter added")
   - Action items extracted from transcript
   - Manual notes if no consent
   - Each with confidence level

2. **B2: CRM Updates (Old→New)**
   - Field-by-field diff preview
   - Per-item Accept/Edit/Reject
   - Shows what will be written to CRM

3. **B3: Tasks**
   - Extracted commitments
   - Owner + due date (blank if not specified)

4. **B4: Follow-up Email Draft**
   - Fully editable draft
   - `DEMO SINK — not delivered` label
   - Recipients confirmed by RM

5. **B5: Rebalancing Proposal + Trade Ticket**
   - Pre-filled ticket (NO execute button)
   - Suitability check status
   - If expired: `HANDOFF BLOCKED`

6. **B6: Tomorrow's Re-Ranked Priorities**
   - Preview of how priorities will change
   - Shows loop closure

**Key Principle:** 
- Per-item edits are NOT approvals (just edits)
- **ONE Approve button** at bottom (Gate 3 - The Decisive Gate)
- Before tap: ZERO writes to CRM, ZERO sends
- After tap: CRM write succeeds, email stays draft, re-rank executes

**Actions:**
- Accept/Edit/Reject per item (edits only)
- Edit any draft line
- **Approve (Gate 3)** → Commits everything with C-3 token
- Reject all
- View evidence/source
- Safe retry (if failed)

---

#### **SCR-08: Outreach Draft & Approved Send**
**Purpose:** Send outreach to clients from approved reasons
**Key Features:**
- Grounded in approved meeting outcomes
- Fully editable draft
- Policy checks before send
- Demo sink (not actually delivered)
- `DEMO SINK — not delivered` label permanent

---

#### **SCR-09: Family Entity Graph & Entitled Pack Versions** *(Range Beat)*
**Purpose:** Show multi-generational family office capability (30s beat)
**Layout:**
- Visual entity graph (7 entities for Tan Family)
- Node-level entitlement visualization
- Consolidated view across entities
- Per-attendee meeting pack versions

**Key Features:**
- Different family members see different data
- Entitlements enforced in copilot assembly
- Consolidated AUM calculation
- Individual entity breakdowns

---

#### **SCR-10: Demo Health / Status Bar** *(Always Visible Bottom)*
**Purpose:** System health and honesty labels
**Fields (8 total):**
1. Ready badge: `READY` / `NOT READY`
2. Mode: `LIVE` / `REPLAY`
3. Source: Feed vendor name
4. Last tick as-of: Timestamp
5. Feed age: `3s` / `STALE 47s` / `>120s outage`
6. Scenario: `S1 Wong Drift`
7. Workflow stage: Current orchestration stage
8. Blocked-attempt count: Auto-send/trade attempts blocked

**Labels:**
- `SYNTHETIC DEMO DATA` (permanent)
- Feed status with age
- Integrity verification status

---

#### **SCR-12: Compliance / Audit Viewer**
**Purpose:** Read-only audit trail (on request, role-switched)
**Key Features:**
- Append-only audit events
- Consent records
- Version stamps
- Blocked attempt logs
- Entitlement leakage test results
- Every view emits C-4 read-access event

---

#### **SCR-14: Tagline / End Card**
**Purpose:** Final screen after demo completes
**Content:**
- "AI orchestrates the workflow. You orchestrate the relationship."
- "Human-approved. Always."
- Honesty labels persist to last frame

---

### **Backstage Screens (Not Projected)**

#### **SCR-11: Demo Operator Console** *(Second Output)*
**Purpose:** Control panel for demo operator (backstage)
**Key Sections:**
1. Scenario picker (S1-S4)
2. Seed input & schema version (read-only)
3. Mode control: `seed` / `replay` / `live` (SOLE WRITER)
4. Generate button + progress
5. Reset button (one-click with confirmation)
6. Feature flags (Shariah beat ON/OFF)
7. Config versions
8. Kill switch per workflow stage
9. What-is-real legend
10. No-real-data guard
11. Health mirror

**Critical Constraint:**
- **NO Approve button** (operator cannot act as RM approver)
- Separation of duties enforced in UI
- Mode changes announced on-camera

**Actions:**
- Load scenario
- Generate (files + database)
- Validate/re-validate
- Switch mode → Triggers on-camera announcement
- **Reset** (Gate 3 - Archive-audit confirmation)
- Toggle feature flags
- Apply config versions

---

#### **SCR-13: Generator Manifest / Integrity Report**
**Purpose:** Show generated data integrity (drill-down from SCR-11)
**Key Features:**
- Manifest with checksums
- Flat file listing (CSV/JSON/Parquet)
- Postgres load status with row counts
- Schema validation results
- Fail-loud on mismatch (no auto-repair)
- Offending record named if failure

---

### **Overlay Drawers (Right-side, not new screens)**

#### **SCR-04: Live Market Event & Signal Evidence Drawer**
**Purpose:** Deep-dive into market event that triggered re-ranking
**Content:**
- Tick details (instrument, price, source, as-of)
- Signal detection (rule pack version, threshold, actual drift)
- Copilot workflow initiation
- Priority re-ranking explanation
- Timeline view of propagation

---

#### **SCR-05: Reason Code & Rank-Change Drill-down**
**Purpose:** Explain why a client moved in ranking
**Content:**
- Contributing signals with weights
- Policy feature list
- Rank-change explanation (4→1 why?)
- Rule pack version
- Evidence chain

---

#### **CMP-02: Source Drawer** *(Universal Component)*
**Purpose:** Click-through from ANY chip to see source details
**Modes:**
- Read-only: View source evidence
- Correctable: Edit memory facts (from SCR-03)

**Content:**
- Source system name
- As-of timestamp
- Confidence level
- Original record
- Provenance chain
- Version stamps

---

## Navigation Flow

```
Entry: SCR-02 (My Day)
  │
  ├─ Click client → SCR-03 (Brief)
  │   │
  │   └─ Approve (Gate 1) → SCR-07 (Consent)
  │       │
  │       └─ Accept → Meeting → SCR-06 (Review)
  │           │
  │           └─ Approve (Gate 3) → Back to SCR-02 (Re-ranked)
  │
  ├─ Click market event → SCR-04 (Drawer overlay)
  ├─ Click rank change → SCR-05 (Drawer overlay)
  ├─ Click any chip → CMP-02 (Drawer overlay)
  │
  └─ Optional: SCR-09 (Family Graph - 30s beat)

Backstage: SCR-11 (Operator Console)
  └─ Drill-down → SCR-13 (Manifest)

On Request: SCR-12 (Audit Viewer)

End: SCR-14 (End Card)
```

---

## Key Interaction Patterns

### **Human Approval Gates (3 Total)**
1. **Gate 1** (SCR-03): RM approves brief before meeting
2. **Gate 2** (SCR-07): Client consents to recording
3. **Gate 3** (SCR-06): RM approves all meeting outcomes (THE decisive tap)

### **Provenance Pattern**
- Every AI statement has visible source chip
- Click chip → Opens CMP-02 drawer with full provenance
- Chips show: `Source • Timestamp` format
- Never hide in tooltip

### **Honest Degradation**
- Feed stale: Show `STALE • age 47s`
- Feed outage: Show `UNAVAILABLE` (never invent data)
- No consent: Show `MANUAL NOTES`
- All states explicit, never blank that looks like zero

### **Motion Rules**
- Motion connects flow between stages
- **Stops at approval gate** (motion ≠ autonomous action)
- No pulsing "thinking" animations
- Transient states held ≥2.5s

---

## What Was Missing (User's Feedback)

### **Conversation History Context** *(Critical Gap)*
Each client card on SCR-02 should include:
1. **Recent Conversations** (last 3-5 interactions)
   - Dates and specific topics discussed
   - "15 Oct 2024: Discussed quarterly rebalancing preferences"
   
2. **Anticipated Needs** (proactive suggestions)
   - Based on conversation history
   - "Client mentioned tech sector interest → prepare opportunities"

3. **Client Sentiment / Preference**
   - How they prefer to communicate
   - "Values data-driven recommendations"
   - "Prefers detailed methodology explanations"

4. **Relationship Context**
   - Family dynamics (for family offices)
   - Communication preferences
   - Risk tolerance evolution

This context should be:
- Visible on SCR-02 (not hidden in drawers)
- Sourced from D5 Client Memory with chips
- Editable/correctable by RM
- Fed into brief generation (SCR-03)

---

## Design Principles Summary

1. **Provenance first-class visual** (not tooltip)
2. **One approval moment** (not five)
3. **Honest degradation is a feature** (show stale/unavailable)
4. **Mode labeling always visible** (LIVE/REPLAY permanent)
5. **Density for RM, legibility for room** (progressive disclosure)
6. **No dark patterns** (never imply AI decided)
7. **Motion is causal, never decorative** (stops at gates)

---

## Total Screen Count: 14

**Projected:** 9 screens (SCR-01, 02, 03, 06, 07, 08, 09, 10, 12, 14)
**Backstage:** 2 screens (SCR-11, 13)
**Overlays:** 3 drawers (SCR-04, 05, CMP-02)

**Single window, state-driven, no tab explosion**

---

## Next Steps for Implementation

1. Build SCR-02 (My Day) with conversation history
2. Build SCR-03 (Five-section brief)
3. Build SCR-06 (Unified review - the centerpiece)
4. Add SCR-04, SCR-05 drawers
5. Build SCR-11 operator console
6. Add charts and visualizations
7. Integrate Unsplash images
8. Add interactive state transitions

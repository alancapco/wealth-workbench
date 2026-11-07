# RM Workbench MVP - UI Design Strategy
**UI Design Expert Team - Design Strategy Document**

---

## Executive Summary

This document outlines the comprehensive design strategy for creating high-fidelity HTML mockups of the RM Workbench MVP - a next-generation wealth management platform for senior leadership demonstration. The design system is based on Capco's professional, clean, black-and-white aesthetic and follows strict requirements for provenance-first UI, human approval gates, and honest degradation patterns.

**Key Deliverables:** 14 screens total (9 projected, 2 backstage, 3 overlay drawers)  
**Design Language:** Capco.com inspired - professional, minimal, black & white  
**Technical Approach:** Static HTML/CSS/JS mockups with realistic interactions  
**Timeline:** Systematic screen-by-screen implementation

---

## 1. Design Principles

### Core Visual Principles (from Product Design Specification)

**P1: Provenance First-Class Visual**
- Every AI statement carries a visible source/timestamp chip
- No hover-to-reveal patterns - chips must be immediately visible
- Minimum 24px font size for chips on projected surface
- Click-through opens source drawer with full provenance

**P2: One Approval Moment**
- Per-item edits are NOT approvals
- Single "Approve" button commits everything with one C-3 token
- No granular approve buttons scattered across the interface

**P3: Honest Degradation as Feature**
- `FEED STALE`, `MANUAL NOTES`, `UNAVAILABLE` are visible, not hidden
- Never show `0` for unavailable data
- Explicit state labels with timestamps

**P4: Permanent Mode Labeling**
- `LIVE`, `REPLAY — recorded <time>`, `SYNTHETIC DEMO DATA` always visible
- Never cuttable by configuration
- Chrome persists across all screens

**P5: Density for RM, Legibility for Room**
- Dense data for operator productivity
- Large, sourced, singular claims for projected viewing
- Progressive disclosure via drawers

**P6: No Dark Patterns**
- Never imply AI decided autonomously
- Never show `sent` for demo sink
- Never auto-advance past approval gate
- Honest labels about what is simulated vs real

**P7: Motion is Causal, Never Decorative**
- Motion connects visible workflow stages
- Motion STOPS at approval gates
- No pulsing "thinking" animations
- No ambient glow or auto-scroll

---

## 2. Capco Brand System

### Logo Analysis
The Capco logo is a clean, professional black text mark. For this mockup system:
- **File:** `/mockup/assets/images/capco_logo.png`
- **Usage:** Header left, paired with product name
- **Alternative:** SVG text rendering for crisp display

### Color Palette

**Primary Colors:**
```
--capco-black: #000000
--capco-white: #FFFFFF
```

**Gray Scale (Professional):**
```
--capco-gray-900: #0A0A0A
--capco-gray-800: #1A1A1A
--capco-gray-700: #2A2A2A
--capco-gray-600: #3A3A3A
--capco-gray-500: #666666
--capco-gray-400: #999999
--capco-gray-300: #CCCCCC
--capco-gray-200: #E5E5E5
--capco-gray-100: #F5F5F5
--capco-gray-50: #FAFAFA
```

**Semantic State Colors (for badges/chips):**
```
Green (Ready/Success): #2E7D32 with white text
Amber (Warning/Stale): #F57C00 with white text
Red (Error/Blocked): #C62828 with white text
Blue (Replay): #1565C0 with white text
```

### Typography

**Font Family:** Inter (Google Fonts)
- Weights: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semi-Bold), 700 (Bold)
- Fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

**Type Scale (for 1920×1080 projected display):**
```
Heading 1: 40px (2.5rem), weight 300, -0.02em letter-spacing
Heading 2: 32px (2rem), weight 300, -0.01em letter-spacing
Heading 3: 20px (1.25rem), weight 500
Heading 4: 12px (0.75rem), weight 600, uppercase, 0.05em letter-spacing
Body Large: 28px (1.75rem) - main claims on projected surface
Body: 16px (1rem)
Body Small: 14px (0.875rem)
Chips/Labels: 24px minimum (1.5rem) for projected visibility
Metadata: 12px (0.75rem)
```

**Minimum Contrast:** 7:1 for chips/states (exceeds WCAG AA requirement of 4.5:1)

### Spacing System
```
--space-1: 4px (0.25rem)
--space-2: 8px (0.5rem)
--space-3: 12px (0.75rem)
--space-4: 16px (1rem)
--space-6: 24px (1.5rem)
--space-8: 32px (2rem)
--space-12: 48px (3rem)
--space-16: 64px (4rem)
```

### Elevation & Shadows
```
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04)
--shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08)
--shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.12)
```

---

## 3. Component Library

### CMP-01: Evidence Chip (Critical)
**Purpose:** Source/timestamp on every AI statement

**Variants:**
1. **LIVE** - `● LIVE · <source> · as-of 09:58:14 SGT`
   - Green dot + text, non-color encoding
   - Click-through to source drawer

2. **REPLAY** - `⏵ REPLAY — recorded 09:58`
   - Blue icon + text
   - Permanent once in replay mode

3. **SEEDED** - `◈ Portfolio, as of prior close`
   - Gray icon + descriptive text
   - Indicates synthetic demo data

4. **RM_MANUAL** - `✎ RM manual · Sarah · 10:14:32`
   - Gray icon + actor + timestamp
   - User-corrected data

5. **DERIVED** - `ƒ Derived · rule-pack v1 · 10:00:02`
   - Gray icon + version + timestamp
   - AI-generated with policy version

6. **STALE** - `⚠ STALE · as-of 09:58:14 · age 47s`
   - Amber warning + timestamp + age
   - Data beyond freshness threshold

7. **UNAVAILABLE** - `⊘ UNAVAILABLE · <reason>`
   - Amber icon + reason text
   - Feed outage or missing data

**Critical Rule:** Missing provenance = statement suppressed. Never render bare text.

### CMP-02: Source Drawer
**Purpose:** Universal chip click-through for provenance details

**Layout:** Right-side overlay (400px wide)
- Header: Source type + timestamp
- Body: Full record details
- Footer: Version history + close button

**Modes:**
- `view` - Read-only evidence inspection
- `correctable` - RM can edit/delete memory facts (FR-07)

### CMP-03: Approval Bar
**Purpose:** Single decisive approval action (C-3 gate)

**States:**
- Disabled: Gray button + "Pending review required"
- Ready: Black button + "Approve as Sarah (RM)"
- Blocked: Red badge + block reason + NO bypass button
- Success: Green confirmation + timestamp

**Behavior:**
- Enter/Space keyboard operable
- 3px focus ring (black)
- No timer-based auto-approve
- Writes C-3 token on tap

### CMP-04: Diff Field
**Purpose:** Old→New CRM preview with per-item disposition

**Visual Pattern:**
```
[Old Value strikethrough] → [New Value bold]
[Old Chip]                   [New Chip]
[Accept] [Edit] [Reject]
```

**Accessibility:** Both values present as text, not color-only indication

### CMP-05: State Badge
**Purpose:** Red/Yellow/Green status indicators

**Color + Text + Icon Pattern:**
- Green `✓ READY` / `✓ VERIFIED` / `✓ SUCCEEDED`
- Yellow `⚠ STALE` / `⚠ PENDING` / `⚠ LOW CONFIDENCE`
- Red `⊘ BLOCKED` / `⊘ FAILED` / `⊘ OUTAGE`

**Never color-only:** Always includes text label and icon/shape

### CMP-06: Consent Banner
**Purpose:** Recording consent gate (Gate 2)

**Layout:** Full-width banner overlay at meeting start
- Language version display
- Accept / Decline / Withdraw buttons
- Method + timestamp recording
- Stub declaration: "This demo uses scripted transcript — no real ASR"

**Cannot be suppressed or disabled** (FR-33 boundary)

### CMP-07: Mode Chip
**Purpose:** Permanent LIVE/REPLAY label (read-only on presenter surface)

**Always Visible In:**
- Header (SCR-01)
- Health bar (SCR-10)
- End card (SCR-14)

**Variants:**
- `LIVE · <source> · as-of 09:58:14 SGT`
- `REPLAY — recorded 09:58`

**Critical:** Operator console is SOLE WRITER, presenter frame is read-only

### CMP-08: Health Bar (8 Fields)
**Purpose:** System health and honesty labels

**Required Fields:**
1. Ready badge: `READY` / `NOT READY`
2. Mode: `LIVE` / `REPLAY`
3. Source: Feed vendor name
4. Last tick as-of: Timestamp
5. Feed age: `3s` / `STALE 47s` / `>120s outage`
6. Scenario: `S1 Wong Drift`
7. Workflow stage: Current orchestration stage
8. Blocked-attempt count: Auto-send/trade attempts blocked

**Persistent Labels:**
- `SYNTHETIC DEMO DATA` (permanent, cannot be disabled)

### CMP-09: Workflow Stage Trace
**Purpose:** Shows C-5 stage sequence with correlation_id

**Visual:** Horizontal breadcrumb with current stage highlighted
```
rank.clients → brief.generate → meeting.capture → review.approve
             [current]
corr_id: 8f21a4b2...
```

### CMP-10: Reason Code Card
**Purpose:** Risk/Opportunity/Retention reason display

**Layout:**
- Code badge (Opportunity / Risk / Retention)
- Contributing signals list (each with chip)
- Policy version stamp
- Confidence level

### CMP-11: Entity Graph Node
**Purpose:** Family office entity visualization

**Display:**
- Node circle with entity name
- Entitlement class label
- Source document reference
- Connection edges with relationship types

### CMP-12: Audit Table
**Purpose:** Append-only C-4 audit log

**Columns:**
- Event ID
- Actor + Role
- Timestamp
- Action
- Target
- Outcome
- Version stamps
- Correlation ID

**Proper table semantics** with `<th>`, scope attributes for screen readers

### CMP-13: Scenario Picker
**Purpose:** S1-S4 scenario selection (operator console)

**Display:** Radio group with:
- Scenario ID
- Triggering event description
- Seed value
- Current state indicator

### CMP-14: Integrity Report
**Purpose:** Manifest + checksum + fail-loud validation

**Display:**
- Manifest header (seed, schema version, generated timestamp)
- File listing with row counts
- Postgres load status
- Integrity checks (orphans, provenance gaps)
- Checksum
- Verdict: `VERIFIED` / `FAILED`
- Offending record (if failed)

### CMP-15: Empty State
**Purpose:** Honest empty/unavailable/no-result messaging

**Never show:**
- Blank spaces that look like zero
- Auto-padded fake data
- Generic "no data" without criteria

**Always show:**
- Clear title
- Evaluation criteria
- Last evaluated timestamp
- Reason for empty state
- Optional single action

### CMP-16: Toast / Status Banner
**Purpose:** Mode-switch announcements, blocked notifications

**Behavior:**
- `aria-live` for screen readers
- Minimum hold: 2.5 seconds
- **Never auto-dismisses** when error/blocked
- Reduced-motion users get instant display

---

## 4. Screen Architecture & Organization

### File Structure
```
/mockup/
├── index.html                      # SCR-02: My Day Home (entry point)
├── screens/
│   ├── scr-01-frame.html          # Persistent Copilot Frame (chrome)
│   ├── scr-02-my-day.html         # My Day Home
│   ├── scr-03-brief.html          # Client Workspace & Five-Section Brief
│   ├── scr-06-review.html         # Unified Post-Meeting Review (centerpiece)
│   ├── scr-07-consent.html        # Consent Banner
│   ├── scr-08-outreach.html       # Outreach Draft & Approved Send
│   ├── scr-09-family-graph.html   # Family Entity Graph
│   ├── scr-10-health-bar.html     # Demo Health / Status Bar
│   ├── scr-11-console.html        # Demo Operator Console (backstage)
│   ├── scr-12-audit.html          # Compliance / Audit Viewer
│   ├── scr-13-manifest.html       # Generator Manifest
│   └── scr-14-end-card.html       # Tagline / End Card
├── components/
│   ├── drawers/
│   │   ├── scr-04-market-event.html    # Live Market Event Drawer
│   │   ├── scr-05-reason-code.html     # Reason Code Drill-down
│   │   └── cmp-02-source-drawer.html   # Universal Source Drawer
│   └── shared/
│       ├── cmp-01-evidence-chip.js
│       ├── cmp-03-approval-bar.js
│       ├── cmp-04-diff-field.js
│       ├── cmp-05-state-badge.js
│       ├── cmp-06-consent-banner.js
│       ├── cmp-07-mode-chip.js
│       ├── cmp-08-health-bar.js
│       └── cmp-09-workflow-trace.js
├── assets/
│   ├── css/
│   │   ├── capco-design.css       # Main design system (existing, to enhance)
│   │   ├── components.css         # Shared component styles
│   │   ├── screens.css            # Screen-specific styles
│   │   └── dark-mode.css          # Dark mode support
│   ├── js/
│   │   ├── app.js                 # Main application logic
│   │   ├── state-manager.js       # Demo state management
│   │   └── interactions.js        # UI interactions
│   └── images/
│       └── capco_logo.png         # Real Capco logo (existing)
└── data/
    ├── demo-seed-s1.json          # Scenario 1: Wong Drift
    ├── demo-seed-s2.json          # Scenario 2
    ├── demo-seed-s3.json          # Scenario 3
    └── demo-seed-s4.json          # Scenario 4
```

### Screen Inventory with Priority

**Phase 1 - Core Flow (Highest Priority):**
1. **SCR-02: My Day Home** - Entry point, priority clients with conversation history
2. **SCR-03: Client Workspace & Five-Section Brief** - Pre-meeting brief with Gate 1
3. **SCR-06: Unified Post-Meeting Review** - Centerpiece with Gate 3, six blocks
4. **SCR-01: Persistent Copilot Frame** - Chrome appearing on all screens

**Phase 2 - Supporting Screens:**
5. **SCR-07: Consent Banner** - Gate 2 overlay
6. **SCR-10: Demo Health/Status Bar** - Persistent footer with 8 fields
7. **SCR-14: End Card** - Terminal state with locked tagline

**Phase 3 - Overlay Drawers:**
8. **SCR-04: Live Market Event Drawer** - Right-side overlay
9. **SCR-05: Reason Code Drill-down** - Right-side overlay
10. **CMP-02: Source Drawer** - Universal provenance viewer

**Phase 4 - Extended Screens:**
11. **SCR-08: Outreach Draft** - Approved send workflow
12. **SCR-09: Family Entity Graph** - 30-second range beat

**Phase 5 - Backstage Screens:**
13. **SCR-11: Demo Operator Console** - Non-projected control panel
14. **SCR-12: Compliance/Audit Viewer** - Role-switched audit trail
15. **SCR-13: Generator Manifest** - Integrity report

---

## 5. Conversation History Context (Critical Gap Addressed)

**Problem:** Original index-v2.html lacked conversation history context per client card.

**Solution:** Each client card on SCR-02 MUST include:

### 1. Recent Conversations (Last 3-5 Interactions)
```html
<div class="context-section">
    <h4>Recent Conversations</h4>
    <ul class="conversation-history">
        <li>
            <span class="conv-date">15 Oct 2024</span>
            <span class="conv-topic">Discussed quarterly rebalancing preferences</span>
        </li>
        <!-- More conversations -->
    </ul>
</div>
```

### 2. Anticipated Needs (Proactive Suggestions)
```html
<div class="context-section">
    <h4>Anticipated Needs</h4>
    <ul class="anticipated-needs">
        <li>Rebalancing discussion triggered by market movement</li>
        <li>Tech sector opportunities (mentioned interest 22 Sep)</li>
    </ul>
</div>
```

### 3. Client Sentiment / Communication Preferences
```html
<div class="context-section">
    <h4>Client Profile</h4>
    <p>Values data-driven recommendations with detailed methodology. Prefers conservative growth strategy.</p>
    <span class="context-meta">Risk Profile: Moderate • Last Updated: 10 Aug 2024</span>
</div>
```

### 4. Relationship Context
- Family dynamics visualization
- Communication channel preferences
- Risk tolerance evolution
- Meeting frequency patterns

**Data Source:** All context sourced from D5 Client Memory with evidence chips

---

## 6. Critical UI Requirements

### Provenance First-Class Visual
- **Every AI statement** gets a visible chip (24px minimum)
- Chips show: `Source · Timestamp` format
- Click opens CMP-02 Source Drawer
- Missing provenance = statement suppressed (fail loud)

### Three Human Approval Gates
1. **Gate 1 (SCR-03):** RM approves brief before meeting
2. **Gate 2 (SCR-07):** Client consents to recording
3. **Gate 3 (SCR-06):** RM approves all meeting outcomes - THE decisive tap

### Honest Degradation Patterns
- Feed stale: Show `STALE · age 47s` (never hide)
- Feed outage: Show `UNAVAILABLE` with reason
- No consent: Show `MANUAL NOTES` badge
- Never show `0` that looks like zero - show `N/A — no data`

### Motion Rules
- Motion connects workflow stages visually
- Motion **STOPS at approval gates** (no autonomous action implied)
- No pulsing animations
- Transient states held ≥2.5 seconds
- Reduced-motion users get instant transitions

### Accessibility Baseline (WCAG 2.1 AA)
- ≥7:1 contrast for chips/states (exceeds 4.5:1 requirement)
- Color + text + icon (never color-only)
- Keyboard operable (Enter/Space for buttons)
- 3px focus rings (black or white depending on background)
- `aria-live` regions for state changes
- Proper semantic HTML (`<button>`, `<th>`, role attributes)
- Screen reader alternatives for graphs

---

## 7. Dark Mode Support

### Strategy: User Preference Toggle
Dark mode is a design specification requirement. Implementation approach:

**CSS Custom Properties Pattern:**
```css
[data-theme="light"] {
    --surface-bg: #FFFFFF;
    --text-primary: #000000;
    --border-default: #E5E5E5;
}

[data-theme="dark"] {
    --surface-bg: #0A0A0A;
    --text-primary: #FFFFFF;
    --border-default: #3A3A3A;
}
```

**Key Adjustments for Dark Mode:**
- Header: Inverted (white header with black text)
- Cards: `--capco-gray-900` background
- Chips: Maintain contrast ratios (≥7:1)
- Focus rings: White on dark backgrounds
- Shadows: Adjusted for visibility

**Toggle Location:** User profile menu (header right)

---

## 8. State Management & Interactions

### Demo State System
```javascript
const demoState = {
    mode: 'LIVE' | 'REPLAY',
    scenario: 'S1' | 'S2' | 'S3' | 'S4',
    currentScreen: 'SCR-02' | 'SCR-03' | ...,
    workflowStage: 'rank.clients' | 'brief.generate' | ...,
    correlationId: 'uuid',
    feedAge: number, // seconds
    feedStatus: 'fresh' | 'stale' | 'outage',
    blockedAttempts: number,
    integrityStatus: 'verified' | 'failed',
    approvalGates: {
        gate1_brief: false,
        gate2_consent: false,
        gate3_review: false
    }
};
```

### Navigation Flow
```
SCR-02 (My Day)
  │
  ├─→ Click client card → SCR-03 (Brief)
  │                         │
  │                         └─→ Approve (Gate 1) → SCR-07 (Consent)
  │                                                   │
  │                                                   └─→ Accept → Meeting → SCR-06 (Review)
  │                                                                            │
  │                                                                            └─→ Approve (Gate 3) → Back to SCR-02
  │
  ├─→ Click market event → SCR-04 (Drawer overlay)
  ├─→ Click rank change → SCR-05 (Drawer overlay)
  └─→ Click any chip → CMP-02 (Drawer overlay)
```

### Interactive Elements
- **Client cards:** Hover state, click to navigate
- **Evidence chips:** Click-through to source drawer
- **Approval buttons:** Keyboard operable, focus visible
- **Drawers:** Escape to close, focus trap, backdrop click
- **State badges:** Tooltip on hover for full reason
- **Diff fields:** Per-item Accept/Edit/Reject

---

## 9. Data & Content Strategy

### Synthetic Demo Data Requirements
**Four Scenarios (S1-S4) Seeded:**
- **S1 Wong Drift:** Portfolio drift triggered by HSBC +2.3% market event
- **S2-S4:** Additional scenarios to demonstrate range

**Data Files (JSON):**
```json
{
  "scenario": "S1",
  "seed": "S1-2026-0316-01",
  "clients": [...],
  "holdings": [...],
  "market_ticks": [...],
  "conversations": [...],
  "preferences": [...]
}
```

### Content Copy Requirements
- **Locked Tagline:** "AI orchestrates the workflow. You orchestrate the relationship."
- **Locked Subline:** "Human-approved. Always."
- **Synthetic Label:** "SYNTHETIC DEMO DATA" (permanent)
- **Demo Sink Label:** "DEMO SINK — not delivered" (permanent)

### Realistic Sample Content
- Client names: Kenneth Wong, Mr. Tan Family, etc.
- AUM values: HKD 45.2M, SGD 12.4M range
- Timestamps: Singapore time zone (SGT)
- Market data: HSBC Holdings, realistic price movements
- Conversation topics: Real wealth management scenarios

---

## 10. Technical Implementation Notes

### Browser Target
- **Primary:** Modern evergreen browsers (Chrome, Edge, Safari, Firefox)
- **Resolution:** Optimized for 1920×1080 projected display
- **Responsive:** Down to 1024px width minimum

### Dependencies (Minimal)
- **Google Fonts:** Inter (300, 400, 500, 600, 700)
- **Icons:** Lucide Icons (lightweight, SVG-based)
- **Charts:** Chart.js (for portfolio visualizations)
- **No heavy frameworks:** Vanilla JS for interactions

### Performance Considerations
- Lazy load drawer content
- CSS transitions for smooth interactions
- Debounced search/filter inputs
- Minimal JavaScript dependencies
- Optimized images (Capco logo)

### Code Organization
- **Separation of concerns:** HTML structure, CSS styling, JS behavior
- **Component modularity:** Reusable components as JS classes
- **State management:** Centralized demo state
- **Event delegation:** Efficient event handling

---

## 11. Design-to-Code Handoff

### CSS Variable Usage
All colors, spacing, and typography defined as CSS custom properties for easy theming and maintenance.

### Component Class Naming (BEM-inspired)
```css
.client-card { }
.client-card__header { }
.client-card__body { }
.client-card--high-priority { }
```

### Accessibility Attributes
```html
<button 
    class="btn-primary" 
    aria-label="Approve brief as Sarah (RM)"
    type="button">
    Approve
</button>
```

### State Classes
```css
.state-ready { }
.state-stale { }
.state-blocked { }
.state-loading { }
```

---

## 12. Quality Assurance Checklist

### Visual QA
- [ ] Capco logo displays correctly
- [ ] Black & white theme consistent
- [ ] Typography hierarchy clear
- [ ] Spacing rhythm maintained
- [ ] Card hover states smooth
- [ ] Focus states visible (3px rings)

### Functional QA
- [ ] Navigation flow works
- [ ] Drawers open/close correctly
- [ ] Chips click-through to source drawer
- [ ] Approval gates block until ready
- [ ] State badges update correctly
- [ ] Mode switching announced

### Content QA
- [ ] All AI statements have chips
- [ ] Conversation history visible per client
- [ ] Anticipated needs displayed
- [ ] Timestamps in SGT
- [ ] No repetitive information
- [ ] Locked taglines correct

### Accessibility QA
- [ ] Keyboard navigation complete
- [ ] Screen reader labels present
- [ ] Contrast ratios ≥7:1 for chips
- [ ] Color not sole differentiator
- [ ] Focus order logical
- [ ] aria-live regions work

### Honest Labeling QA
- [ ] `SYNTHETIC DEMO DATA` always visible
- [ ] `DEMO SINK — not delivered` on sends
- [ ] Mode chip (`LIVE`/`REPLAY`) permanent
- [ ] Stale/unavailable states explicit
- [ ] No fake zeros or blanks

---

## 13. Implementation Roadmap

### Week 1: Foundation
- Day 1-2: Enhance CSS framework, build component library
- Day 3-4: Build SCR-02 (My Day) with conversation history
- Day 5: Build SCR-01 (Persistent Frame) and SCR-10 (Health Bar)

### Week 2: Core Screens
- Day 1-2: Build SCR-03 (Five-Section Brief)
- Day 3-5: Build SCR-06 (Unified Review) - the centerpiece

### Week 3: Supporting Elements
- Day 1: Build SCR-07 (Consent), SCR-14 (End Card)
- Day 2-3: Build overlay drawers (SCR-04, 05, CMP-02)
- Day 4-5: Build SCR-08 (Outreach), SCR-09 (Family Graph)

### Week 4: Backstage & Polish
- Day 1-2: Build SCR-11 (Console), SCR-12 (Audit), SCR-13 (Manifest)
- Day 3-4: Interactive state management, navigation flow
- Day 5: QA, refinement, dark mode

---

## 14. Risk Mitigation

### Known Challenges

**Challenge 1: Conversation History Complexity**
- **Risk:** Overwhelming information density on client cards
- **Mitigation:** Progressive disclosure, collapsible sections, clear visual hierarchy

**Challenge 2: Evidence Chip Proliferation**
- **Risk:** Too many chips create visual clutter
- **Mitigation:** Group related chips, consistent sizing (24px min), smart positioning

**Challenge 3: Dark Mode Contrast**
- **Risk:** Chips lose visibility in dark mode
- **Mitigation:** Pre-defined dark variants with tested contrast ratios

**Challenge 4: Backstage/Projected Separation**
- **Risk:** Unclear which screens are projected vs backstage
- **Mitigation:** Clear file naming, documentation, visual indicators in mockups

---

## 15. Success Criteria

### Functional Success
✓ All 14 screens built and navigable  
✓ Three approval gates implemented  
✓ Evidence chips on every AI statement  
✓ Conversation history visible per client  
✓ Honest degradation patterns working  
✓ Mode switching with announcements  

### Visual Success
✓ Capco branding consistent throughout  
✓ Clean, professional, uncluttered UI  
✓ NO repetitive information  
✓ Clear information hierarchy  
✓ Legible from 3-8m viewing distance  

### Technical Success
✓ Accessible (WCAG 2.1 AA)  
✓ Keyboard navigable  
✓ Dark mode supported  
✓ Performant (no lag on transitions)  
✓ Well-organized codebase  

### Stakeholder Success
✓ Senior leadership demo-ready  
✓ Shows live market event propagation  
✓ Demonstrates human approval gates  
✓ Proves provenance-first design  
✓ Honest about what is simulated  

---

## Conclusion

This design strategy provides a comprehensive blueprint for creating high-fidelity HTML mockups of the RM Workbench MVP. The approach prioritizes:

1. **Capco's professional aesthetic** - Clean black & white design
2. **Provenance-first UI** - Evidence chips on every AI statement
3. **Conversation history context** - Addressing the critical gap
4. **Human approval gates** - Three clear decision points
5. **Honest degradation** - Explicit state labeling
6. **Accessibility** - WCAG 2.1 AA compliance

The implementation will be systematic, starting with core flow screens (SCR-02, 03, 06) before building supporting screens and backstage controls. All designs follow the strict requirements from the Product Design Specification while applying Capco's visual identity.

---

**Document Owner:** UI Design Expert Team (ui-design-lead)  
**Status:** Design Strategy Complete - Ready for Implementation  
**Next Steps:** Begin Phase 1 - Foundation (CSS framework & component library)

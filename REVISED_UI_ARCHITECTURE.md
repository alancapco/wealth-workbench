# Capco RM Workbench - Revised UI Architecture

## Design Philosophy

**Problem:** Too much information density, overwhelming cards
**Solution:** 
- Iconic representation with progressive disclosure
- Scrollable panels for deep information
- Visual hierarchy with grouping
- Hover/expand for details

---

## SCR-02: My Day - Revised Layout

### **Compact Card View (Default)**

```
┌─────────────────────────────────────────────────────────┐
│ KW  Kenneth Wong                          ↑ 4→1  [RISK] │
│     HKD 45.2M                                            │
│                                                          │
│  🎯 Portfolio drift 6%  •  💬 3 notes  •  📅 Last: 15 Oct│
│                                                          │
│  [View Brief] ──────────────────────────────────────────→│
└─────────────────────────────────────────────────────────┘
```

**Compact shows:**
- Client identity (initials, name, AUM)
- Priority indicator (rank change with arrow)
- Reason badge (RISK/OPPORTUNITY/RETENTION)
- 3 key icons with counts: Target, Conversations, Calendar
- One action button

### **Expanded Card View (Click to expand)**

```
┌─────────────────────────────────────────────────────────────────────┐
│ KW  Kenneth Wong                              ↑ 4→1  [RISK]         │
│     HKD 45.2M AUM                                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ ⚡ MARKET EVENT                                                      │
│ HSBC Holdings +2.3% → Portfolio drift 6% from target                │
│ Source: Reuters • 10:14:18                                          │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ 💬 RECENT CONVERSATIONS                          [View All Timeline]│
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────┐   │
│ │ 📅 15 Oct 2024                                               │   │
│ │ Discussed quarterly rebalancing • Prefers HK equities        │   │
│ │                                                              │   │
│ │ 📅 22 Sep 2024                                               │   │
│ │ Expressed interest in tech sector exposure                   │   │
│ │                                                              │   │
│ │ 📅 10 Aug 2024                                               │   │
│ │ Risk tolerance review • Confirmed moderate growth            │   │
│ └──────────────────────────────────────────────────────────────┘   │
│   ↑ Scrollable (5 conversations total)                              │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ 💡 ANTICIPATED NEEDS                                                │
│                                                                      │
│ • Rebalancing discussion (triggered by market)                      │
│ • Tech sector opportunities (mentioned interest)                    │
│ • Q4 portfolio review preparation                                   │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ 👤 CLIENT PROFILE                                                   │
│ Risk: Moderate | Style: Growth | Liquidity: Low                     │
│ Sentiment: Values data-driven recommendations                       │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ [Prepare Brief] ─────────────────────────→  [View Full Profile] → │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Icon System

### **Status Icons (Always Visible)**
- 🎯 Target/Alert (portfolio drift, risk)
- 💬 Conversations (count of recent interactions)
- 📅 Calendar (last contact date)
- ⚡ Market Event (live trigger)
- 💡 Anticipated Needs (proactive suggestions)
- 👤 Client Profile (quick facts)
- 📊 Portfolio (performance data)
- 🌙 Faith-based (Islamic investing)
- 👨‍👩‍👧 Family Office (multi-generational)

### **Action Icons**
- → View/Open (primary action)
- ↗ External link
- ⟳ Refresh/Regenerate
- ✓ Approve
- ✎ Edit
- ⋮ More options

---

## SCR-03: Five-Section Brief - Revised Layout

### **Tabbed Sections (Top)**

```
┌──────────────────────────────────────────────────────────────────┐
│ Kenneth Wong • HKD 45.2M                        [Approve Brief] ✓ │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ [📊 Portfolio]  [⚡ Alerts]  [💬 History]  [📰 News]  [📋 Agenda]│
│   ─────────                                                       │
│                                                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                                                         │   │
│   │  PORTFOLIO OVERVIEW                  ✓ Available       │   │
│   │  As of: 10:14:18 • Portfolio System                    │   │
│   │                                                         │   │
│   │  ┌────────────────────────────────────────────────┐   │   │
│   │  │  Current AUM: HKD 45.2M  (-2.3% MTD)          │   │   │
│   │  │                                                │   │   │
│   │  │  Asset Allocation vs Target:                  │   │   │
│   │  │                                                │   │   │
│   │  │  [Pie Chart: Equities 58% / Target 55%]      │   │   │
│   │  │  [Pie Chart: Fixed Income 28% / Target 30%]  │   │   │
│   │  │  [Pie Chart: Cash 14% / Target 15%]          │   │   │
│   │  │                                                │   │   │
│   │  │  ⚠️ HSBC Holdings: 18% (Target: 12%)          │   │   │
│   │  │     Drift: 6% over target                     │   │   │
│   │  │                                                │   │   │
│   │  └────────────────────────────────────────────────┘   │   │
│   │                                                         │   │
│   │  Source: Portfolio Mgmt System • 10:14:18 ──────→     │   │
│   │                                                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│     ↑ Each tab = separate scrollable panel                      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### **Visual Representation per Tab**

**Tab 1: 📊 Portfolio**
- Pie charts for allocation
- Bar charts for drift
- Key metrics in cards
- Color: Green (on target) / Red (drift)

**Tab 2: ⚡ Alerts**
- Timeline view of market events
- Visual indicator of trigger
- Drift visualization (gauge)
- Live tick animation

**Tab 3: 💬 History**
- Vertical timeline
- Conversation bubbles
- Action items with checkboxes
- Expandable details

**Tab 4: 📰 News**
- Card-based news items
- Headlines + source icons
- Time-sorted
- Licensed badge

**Tab 5: 📋 Agenda**
- Checklist format
- Editable items
- AI-generated badge
- Drag to reorder

---

## SCR-06: Unified Review - Revised Layout

### **Accordion Sections (Collapsed by Default)**

```
┌────────────────────────────────────────────────────────────────┐
│ Meeting Review • Kenneth Wong                                   │
│ Correlation ID: WF-2024-001 • Recording: ✓ Consented          │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ▼ 1. NOTES & PREFERENCES                            [3 items] │
│   ┌─────────────────────────────────────────────────────────┐ │
│   │ ✓ Family: Daughter to join next meeting               │ │
│   │   Confidence: High • Transcript 10:06:12                │ │
│   │                                                         │ │
│   │ ✓ Prefers quarterly rebalancing                        │ │
│   │   Confidence: High • Transcript 10:07:22                │ │
│   │                                                         │ │
│   │ ✎ Send consolidated statement (owner blank)            │ │
│   │   Confidence: Medium • Requires review                  │ │
│   └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│ ▶ 2. CRM UPDATES                                     [2 changes]│
│                                                                 │
│ ▶ 3. TASKS                                            [1 task] │
│                                                                 │
│ ▶ 4. FOLLOW-UP EMAIL                                   [Draft] │
│                                                                 │
│ ▶ 5. REBALANCING PROPOSAL                         [Pre-filled] │
│                                                                 │
│ ▶ 6. TOMORROW'S PRIORITIES                        [Wong → #1] │
│                                                                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Per-item edits above • One approval below:                     │
│                                                                 │
│              [Approve All Changes] ──────────→                 │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

**Interaction:**
- Click section header → Expands/collapses
- Shows count in collapsed state
- Scroll within expanded section
- Visual checkmarks for reviewed items

---

## Information Density Solutions

### **1. Progressive Disclosure**
```
Compact → Hover → Click → Drawer
  🎯      [Tooltip]  [Card]   [Full Details]
```

### **2. Grouping Strategies**

**By Time:**
- Today / This Week / This Month
- Recent / Older

**By Type:**
- Market Events
- Client Requests
- Scheduled Reviews
- Proactive Opportunities

**By Status:**
- Urgent (red)
- Important (amber)
- Routine (gray)

### **3. Visual Hierarchy**

**Level 1: Glanceable (Icons + Numbers)**
```
🎯 3  💬 5  📅 2d
```

**Level 2: Scannable (One-line summaries)**
```
Portfolio drift 6% • 3 conversations • Last contact 2d ago
```

**Level 3: Readable (Expanded details)**
```
┌─────────────────────────────────────┐
│ Market Event: HSBC +2.3%            │
│ Impact: Portfolio drift 6% from tgt │
│ Action: Rebalancing recommended     │
└─────────────────────────────────────┘
```

**Level 4: Deep (Drawer/Modal)**
```
Full timeline, evidence chain, source documents
```

---

## Scrollable Panel Design

### **Conversation Timeline (Vertical Scroll)**

```
┌────────────────────────────────────┐  ↑
│ 📅 15 Oct 2024                    │  │ Scroll
│ ┌────────────────────────────────┐│  │ 5 items
│ │ Quarterly rebalancing          ││  │
│ │ • Prefers HK equities          ││  │
│ │ • Mentioned tech interest      ││  │
│ └────────────────────────────────┘│  │
│                                    │  │
│ 📅 22 Sep 2024                    │  │
│ ┌────────────────────────────────┐│  │
│ │ Tech sector exposure           ││  ↓
│ │ • Looking for growth           ││
│ └────────────────────────────────┘│
│ ...                                │
└────────────────────────────────────┘
```

### **Horizontal Tab Scroll (Too many tabs)**

```
← [Portfolio] [Alerts] [History] [News] [Agenda] [More →]
```

---

## Capco Black & White Visual System

### **Card States (Using Borders & Fills)**

```
Default:     Border: #E5E5E5  Background: #FFFFFF
Hover:       Border: #000000  Background: #FAFAFA
Active:      Border: #000000  Background: #000000 (inverse)
Disabled:    Border: #E5E5E5  Background: #F5F5F5  Opacity: 0.5
```

### **Icon Style**
- Outline icons (not filled)
- Consistent weight: 1.5px stroke
- Size: 20px default, 16px small, 24px large
- Color: #000000 primary, #666666 secondary

### **Typography Weights**
- Light (300): Large headings
- Regular (400): Body text
- Medium (500): Labels
- Semibold (600): Emphasis
- Bold (700): Rare, only for alerts

---

## Next Implementation Approach

### **Phase 1: Build Compact View**
1. Minimal cards with icons + counts
2. Clean grid layout
3. Hover states

### **Phase 2: Add Expansion**
1. Click to expand card
2. Scrollable conversation panel
3. Accordion sections

### **Phase 3: Add Drawer Details**
1. Right-side drawer for deep-dive
2. Evidence chains
3. Full timeline

### **Phase 4: Add Charts**
1. Portfolio allocation (pie/donut)
2. Drift visualization (gauge)
3. Timeline visualization

Should I now build the actual mockup with:
1. **Compact cards with icon summary**?
2. **Expandable panels with scroll**?
3. **Capco black & white styling**?

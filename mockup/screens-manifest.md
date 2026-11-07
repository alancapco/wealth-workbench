# RM Workbench - Complete System Screens

## Screen Structure

### Core Flow (Main User Journey)
1. **index.html** - SCR-02: My Day (Entry point) ✓
2. **brief.html** - SCR-03: Client Brief (Gate 1)
3. **consent.html** - SCR-07: Consent Banner (Gate 2)
4. **review.html** - SCR-06: Meeting Review (Gate 3 - Centerpiece)
5. **outreach.html** - SCR-08: Outreach Draft

### Supporting Screens
6. **family-graph.html** - SCR-09: Family Entity Graph
7. **audit.html** - SCR-12: Compliance Audit Viewer
8. **end-card.html** - SCR-14: End Card

### Operator/Backstage
9. **operator.html** - SCR-11: Operator Console
10. **manifest.html** - SCR-13: Generator Manifest

### Overlays (Drawers)
- Market Event Drawer (SCR-04)
- Reason Code Drawer (SCR-05)
- Source Drawer (CMP-02)

### Shared Components
- **app.js** - Navigation & state management ✓
- **Persistent Header** (SCR-01) - On all screens
- **Health Footer** (SCR-10) - On all screens

## Implementation Strategy

Build as single-page application (SPA) with:
- All screens in one HTML file
- JavaScript navigation between screens
- Persistent header/footer
- Overlay drawers
- Complete workflow from My Day → Brief → Consent → Review → Back to My Day


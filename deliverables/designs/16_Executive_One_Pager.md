# Next-Generation RM Workbench — MVP Demo
## Executive One-Pager

**Purpose.** Demonstrate the *envisioned RM journey* and how AI is used inside a next-generation Relationship Manager workbench. Audience: company senior leadership. **Status: design complete — zero open design decisions; no application code written.**

**One sentence.** A single-screen AI workbench that turns a live market event into one sourced, RM-approved action — with the Relationship Manager as the *only* human user and the client represented entirely by synthetic data.

---

### The demo journey (the leadership story)
1. **Live market tick** (Tiger paper-trading feed, real-time quotes) →
2. **Signal** ("Wong portfolio drifted 6% from target") →
3. **Copilot Core** assembles context →
4. **My Day** re-ranks the RM's priorities →
5. **Sourced brief** (every fact carries a provenance chip) →
6. **Consent / scripted capture** →
7. **One decisive Approve** (RM edits two lines → single tap) →
8. **Loop closes** (new priority list + tomorrow's brief).

End-to-end loop within the **≤10s p95 budget (NFR-1)**; the offline `REPLAY` binding is the guaranteed fallback.

### Honesty contract (non-negotiable)
- **REAL / SIMULATED / STUBBED / HARD-BLOCKED** labelled on every element. Live data uses real quotes but is **never attributed on stage** (Tiger is data-only).
- **100% synthetic + AI-generated** demo data (`SYNTHETIC DEMO DATA · AI-GENERATED`); **0 sends, 0 trades, 0 real dialled calls**.
- **Single Approve gate (C-3)** stops every client-facing / system-writing action. **Trade execution has no table, endpoint, or code path** (HARD-BLOCKED).

### Architecture at a glance
- **Postgres 16, one instance**: 8 frozen schemas / 40 tables + additive `crm` (6 tables). TimescaleDB + `file_fdw`; G8 `CHECK` blocks `LIVE` while bound to replay.
- **Two BFFs**: read-only Presenter + sole-writer Operator — now on a **single screen** (off-camera console dropped).
- **AI generator**: one deterministic seed → flat files → one-transaction load → integrity validation → reset ≤60s. All demo data is AI-generated, then frozen and replayed.

### External adapters (all resolved)
| Adapter | Role in demo | Posture |
|---|---|---|
| **Tiger Brokers paper-trading API** | Live market quotes (data-only) | Real-time; **not named on stage**; API provided by Alan |
| **HubSpot Free** | Demo CRM + sandbox write-back | `REAL (SANDBOXED)` post-Approve; 0 sends; optional overlay |
| **ElevenLabs** | ASR (Speech-to-Text) + TTS | Real RM voice in/out; key placeholder only |
| **Retell AI** | Client voice agent | **Deferred to MVP2** (webhook + consent artefacts now in scope) |

### What is demoable today
Full advisory loop on synthetic AI-generated data; live (Tiger) and offline (replay) bindings; single screen; CRM sandbox write-back; sampled relationship graph + family beat; multi-currency *schema* (HKD/SGD/USD row content pending build).

### Go / no-go
**Go** if: sandbox portal + Tiger API reachable; ≤10-property mapping loaded; read-after-write verifies; offline rehearsal passes with reset ≤60s; native Retell→HubSpot OFF; zero counters hold; `SYNTHETIC DEMO DATA` visible to the last frame.
**If the live feed fails → run entirely on `REPLAY`** — the journey is unchanged, only the honesty chip changes.

### Status & next steps
- **Design decisions: 100% closed** — base `Q1–Q3` / `OD-1–11`, enhancement `DI-01–25` / `OQ-1–13`, vendor `E-9–E-16`.
- **Only build-phase work left**: (1) multi-currency seed amendment (HKD/USD rows); (2) *optional* Retell runtime.
- **No code exists today.** Authorising a build is a separate, explicit decision.

*Full detail: `RM_Workbench_MVP_Design_Package.md` (base) + `10`–`15` (addendum). Decision log: `14_…` §8.1–§8.4.*

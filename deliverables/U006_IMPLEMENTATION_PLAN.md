# U-006 Implementation Plan: Workflow Orchestration & Client Context

**Status:** Ready to implement, blocked waiting for U-005 persistence models
**Owner:** workflow-context-owner
**Created:** 2026-01-09

## Scope Summary

Per REMEDIATION_04_Implementation_Batches.md §3 U-006:
- Workflow create/list/get with durable state
- Stage dispatch/pause/resume/abandon
- Client context assembly with entitled data aggregation
- Calendar event resolution with ambiguity handling
- Versioned skill catalog and registry
- NO brief generation (U-007), NO action dispatch (U-009)

## Dependencies

### ✅ Complete
- U-003: Common schemas (common.py with Envelope, Source, ArtifactRef, etc.)
- U-001: Backend boot and readiness
- U-002: Alembic configuration

### ❌ Blocked - U-005 Missing
Required models from REMEDIATION_03A_Additive_Schema.sql:
- `workflows` table (lines 229-242)
- `stage_runs` table (lines 251-261)
- `skill_versions` table (lines 244-250)
- `artifact_lineages` table (lines 264-277)
- `artifact_revisions` table (lines 279-288)
- `meetings` table (lines 217-228)
- `calendar_events` table (lines 208-216)
- `client_scope` table (lines 111-117)
- `books` table (lines 106-110)
- `client_assignments` table (lines 118-124)

Required repositories (not present):
- Base repository with transaction support
- Artifact repository with lineage/revision handling
- Workflow repository
- Context assembly utilities

## API Contracts (Architecture §6.1, §6.2)

### Client & Context APIs
- **API-001** GET `/session` → `{principal, csrf_token, capabilities, active_workflows}`
- **API-002** GET `/clients` → `{items: ClientSummary[], next_cursor}`
- **API-003** GET `/clients/{c}` → `{client: ClientDetail}`
- **API-020** GET `/clients/{c}/portfolio` → `{snapshot: Portfolio}`
- **API-021** GET `/dashboard/my-day` → `{date, timezone, priorities, calendar, workflows, book_stats, news}`

### Calendar APIs
- **API-022** GET `/calendar/events` → `{items: CalendarEvent[], next_cursor, capability_state}`
- **API-023** POST `/calendar/events/{e}/resolutions` → `{meeting: Meeting}`
- **API-024** GET `/meetings/{m}` → `{meeting: Meeting}`

### Workflow APIs
- **API-007** POST `/workflows` → `{workflow: Workflow}` (201)
- **API-008** GET `/workflows/{w}` → `{workflow: Workflow}`
- **API-025** GET `/workflows` → `{items: Workflow[], next_cursor}`
- **API-009** POST `/workflows/{w}/stages/{stage}/runs` → `{run: StageRun}` (202)
- **API-026** POST `/workflows/{w}/pause` → `{workflow: Workflow}`
- **API-027** POST `/workflows/{w}/resume` → `{workflow: Workflow}`
- **API-028** POST `/workflows/{w}/abandon` → `{workflow: Workflow, continuing_action_ids}`
- **API-029** GET `/workflows/{w}/runs/{r}` → `{run: StageRun}`
- **API-030** GET `/skills` → `{items: SkillDescriptor[]}`

## File Ownership

### Schemas (new files)
- `backend/app/schemas/client.py` - ClientSummary, ClientDetail, Portfolio, Profile types
- `backend/app/schemas/workflow.py` - Workflow, StageRun, StartWorkflow, SkillDescriptor
- `backend/app/schemas/calendar.py` - CalendarEvent, Meeting types

### Services (new directories)
- `backend/app/services/context/` - Client context assembly
  - `client_service.py` - Entitled client lookup/detail
  - `context_assembler.py` - Aggregate profile/holdings/interactions/memory
  - `__init__.py`
- `backend/app/services/calendar/` - Calendar resolution
  - `calendar_service.py` - Event list, ambiguity detection
  - `resolution_service.py` - Explicit client selection
  - `__init__.py`
- `backend/app/services/workflow/` - Orchestrator (replace existing)
  - `workflow_orchestrator.py` - Launch/resume with frozen context
  - `registry.py` - Versioned skill catalog
  - `stage_runner.py` - Stage dispatch/lease/retry
  - `__init__.py`

### API Endpoints (modify existing + new)
- `backend/app/api/v1/endpoints/clients.py` - Modify for API-002, API-003, API-020
- `backend/app/api/v1/endpoints/workflow.py` - Replace with API-007..009, 025..030
- `backend/app/api/v1/endpoints/calendar.py` - NEW for API-022..024

### Adapters (FIXTURE only)
- `backend/app/adapters/identity/` - Identity adapter interface
  - `base.py` - Abstract identity adapter
  - `fixture.py` - Synthetic tenant/book/entitlement
  - `__init__.py`
- `backend/app/adapters/calendar/` - Calendar adapter interface
  - `base.py` - Abstract calendar adapter
  - `fixture.py` - Synthetic events with ambiguity scenarios
  - `unavailable.py` - UNCONFIGURED state
  - `__init__.py`
- `backend/app/adapters/portfolio/` - Portfolio adapter interface
  - `base.py` - Abstract portfolio adapter
  - `fixture.py` - Synthetic holdings/allocations
  - `unavailable.py` - UNCONFIGURED state
  - `__init__.py`

### Tests
- `backend/tests/context/` - Context assembly tests
  - `test_client_service.py`
  - `test_context_freeze.py`
- `backend/tests/workflow/` - Workflow orchestration tests
  - `test_workflow_orchestration.py`
  - `test_stage_runs.py`
  - `test_registry.py`
  - `test_pause_resume.py`
  - `test_stale_context.py`

## Key Implementation Rules

### Context Freeze (Architecture §6.2)
- Context revision increments on any client/memory/entitlement change
- Workflow snapshots context_revision at creation
- Stage runs validate context_revision before execution
- Stale context → 409 CONTEXT_CHANGED

### Stage Idempotency
- Unique `(workflow_id, stage_key, stage_version)`
- Retry uses same run ID, increments attempt
- Expired lease → FAILED (preserves output, not counted as completion)
- Manual intervention flag preserved

### Memory Proposal Workflow
- MEMORY_WRITE is an action class requiring separate authorization (U-009)
- Workflow can propose memory via artifacts
- Confirmation flows through action preview/authorization
- No direct canonical write from workflow

### Fixture Adapters
- Environment kind FIXTURE required in `APP_ENV=local|test`
- FIXTURE adapters rejected when `APP_ENV=production`
- Synthetic data with explicit FIXTURE origin/environment
- Unavailable adapters return UNCONFIGURED/UNAVAILABLE capability state

### No Auto-Execution
- GET never starts runs
- Resume reauthorizes without auto-running
- Empty results ≠ dependency outage (explicit states)

## Acceptance Tests

### Context Tests
1. Eligible client returned with sources
2. Revoked client → 404
3. Wrong-book client → 404
4. Context revision increments on memory change
5. Fixture adapter in production → rejected

### Calendar Tests
1. Ambiguous event requires explicit resolution (API-023)
2. Event version conflict → 409
3. Canceled event → 409
4. UNCONFIGURED provider → 409 CONFIG_UNCONFIGURED

### Workflow Tests
1. Create workflow freezes context_revision
2. Stage run idempotency (same run_id on retry)
3. Pause → status PAUSED, no new stages
4. Resume → reauthorize, no auto-run
5. Abandon → status ABANDONED, continuing actions listed
6. Stale context → 409 CONTEXT_CHANGED
7. GET /workflows/{id} never starts run
8. Restart preserves persisted status/version/output refs

### Negative Tests
1. Unknown pilot/stage → disabled
2. Missing provider → UNCONFIGURED
3. Stage expiry preserves prior output
4. Fixture adapter rejected in production

## Test Commands
```bash
cd backend
uv run pytest tests/context tests/workflow -q
```

## NO-GO Items
- ❌ No provider keys/calls
- ❌ No client creation/merge endpoint
- ❌ No inferred profile defaults
- ❌ No parallel orchestrator
- ❌ No pilot activation
- ❌ No brief generation (that's U-007)
- ❌ No action dispatch (that's U-009)

## Implementation Strategy (Once Unblocked)

### Option A: Full Implementation (Preferred)
1. Wait for U-005 models to be complete
2. Implement schemas referencing U-005 models
3. Implement services with real persistence
4. Write tests against actual PostgreSQL
5. Single clean implementation, no rewrites

### Option B: Parallel Track (If Directed)
1. Implement U-005 models myself (coordinate with persistence-owner)
2. Implement U-006 on top
3. Risk: duplication/conflicts if persistence-owner working simultaneously

### Option C: Stub Implementation (Not Recommended)
1. Implement with in-memory storage
2. Full rewrite required when U-005 lands
3. Tests won't validate persistence/restart behavior

## Current Status: BLOCKED

Waiting for team-lead decision on how to proceed given U-005 is incomplete.

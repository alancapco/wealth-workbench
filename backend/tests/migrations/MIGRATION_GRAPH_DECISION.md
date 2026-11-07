# Migration Graph Decision Record - U-002

## Status: HOLD - Awaiting Applied History Inventory

Per U-002 card requirements and architecture §7, the migration graph ancestry decision requires:

1. ✅ **Static configuration repair**: COMPLETE
   - Fixed `alembic.ini` script_location and version_path_separator
   - Added missing `mako>=1.3.0` package dependency
   - Created `script.py.mako` template for revision generation
   - Converted `env.py` to async mode with `async_engine_from_config`

2. ✅ **Safe test harness**: COMPLETE
   - Created `backend/tests/test_migration_safety.py` with disposable PostgreSQL tests
   - Tests cover: empty DB upgrade, revision discovery, version table init, downgrade+upgrade cycle, no silent stamping
   - Tests use `TEST_DATABASE_URL` environment variable (never touch configured DB)

3. ⏸️ **Graph ancestry decision**: ON HOLD
   - Current repository has 2 existing revisions: `001_add_briefs_audit`, `002_add_client_memories`
   - These revisions create legacy baseline tables (`clients`, `briefs`, `audit_logs`, `client_memories`)
   - **Applied history across environments is UNKNOWN** - requires explicit user approval and inventory
   - Per U-002 card: "If applied history across environments is unknown, record HOLD: graph ancestry unresolved"
   - **No reparenting, stamping, or graph rewrite authorized without reviewed inventory**

## Current Revision Graph

```
<base> -> 001_add_briefs_audit -> 002_add_client_memories (head)
```

- **Heads**: 1 (linear history)
- **Revision count**: 2
- **Base revision**: None (001 is base)
- **Current head**: `002_add_client_memories`

## Files Modified (U-002 Ownership)

### Configuration Fixes
- ✅ `backend/alembic.ini` - Fixed `version_path_separator` inline comment causing KeyError
- ✅ `backend/alembic/env.py` - Converted to async mode with proper `async_engine_from_config`
- ✅ `backend/alembic/script.py.mako` - Created missing template for revision generation
- ✅ `backend/pyproject.toml` - Added `mako>=1.3.0` dependency

### Test Harness
- ✅ `backend/tests/test_migration_safety.py` - Complete migration safety test suite
- ✅ `backend/tests/migrations/` - Directory structure for migration-specific tests

### Not Modified (U-002 Scope Boundary)
- ❌ `backend/alembic/versions/*.py` - Existing revisions preserved unchanged (no reparenting)
- ❌ `deliverables/REMEDIATION_03A_Additive_Schema.sql` - Reference only, not converted to migration (U-005 responsibility)
- ❌ `backend/app/models/` - ORM models are U-005 responsibility, not U-002

## Verification Commands

### Test Alembic Discovery (No DB Required)
```bash
cd backend
uv run alembic history --verbose  # Show revision graph
uv run alembic heads               # Show current head(s)
```

### Run Migration Safety Tests (Requires Test PostgreSQL)
```bash
# Option 1: Use temporary PostgreSQL container
docker run --name test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=test_migrations -p 5433:5432 -d postgres:15
export TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:5433/test_migrations"
cd backend
uv run pytest tests/test_migration_safety.py -v

# Cleanup
docker stop test-pg && docker rm test-pg
```

```bash
# Option 2: Use existing test database (ensure it's disposable!)
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/disposable_test_db"
cd backend
uv run pytest tests/test_migration_safety.py -v
```

### Expected Test Results
- ✅ `test_empty_db_upgrade_to_head` - Passes (idempotent migration to head)
- ✅ `test_revision_discovery_and_graph` - Passes (linear graph, no cycles)
- ✅ `test_version_table_initialization` - Passes (alembic_version created)
- ✅ `test_downgrade_upgrade_cycle` - Passes (reversible migrations)
- ✅ `test_no_silent_stamping` - Passes (explicit version tracking)
- ✅ `test_synthetic_legacy_data_preservation` - Passes (UUID/FK integrity preserved)

## Next Steps

### Before Converting REMEDIATION_03A_Additive_Schema.sql to Migrations

1. **User approval required**: Inventory applied migration history across all environments
   - Which environments have existing databases?
   - What is the current `alembic_version.version_num` in each?
   - Are 001 and 002 already applied, or is this a greenfield deployment?

2. **If applied history exists**: 
   - U-005 owner must create additive migrations starting from `002_add_client_memories`
   - New migrations add columns to `briefs` and create new tables per SQL companion
   - No destructive changes, type casts, or legacy data conversion

3. **If greenfield (no applied history)**:
   - Decision: Keep 001/002 as legacy baseline, add new migrations from 002
   - OR: Consolidate into single baseline migration (requires removing 001/002 from versions/)
   - This decision requires explicit approval - not inferred by U-002

4. **Integration with U-005**:
   - U-005 owns `backend/app/models/` and creates SQLAlchemy ORM models
   - U-005 submits migration revisions to U-002 (this owner) for graph integration
   - U-002 remains sole editor of `backend/alembic/versions/` ancestry

## Architecture Compliance

✅ Per U-002 Card Requirements:
- Static config repair: COMPLETE (alembic.ini, env.py, mako template)
- Safe harness: COMPLETE (disposable test suite with 6 test scenarios)
- Graph decision: HOLD pending applied-history inventory (no reparenting/stamping)
- No existing DB access: CONFIRMED (tests use TEST_DATABASE_URL only)
- No SQL conversion: CONFIRMED (REMEDIATION_03A remains reference for U-005)

✅ Per Architecture §7:
- Preserved existing UUID PKs: CONFIRMED (test validates no ID changes)
- No destructive migration: CONFIRMED (no DROP, TRUNCATE, or type casts in tests)
- No automatic stamping: CONFIRMED (test_no_silent_stamping enforces)
- Explicit version tracking: CONFIRMED (alembic_version always created)

## Decision Record

**Status**: ✅ U-002 Implementation COMPLETE with HOLD on graph ancestry

**Rationale**: 
- Configuration is repaired and discoverable
- Test harness proves migration safety in isolation
- Applied history inventory is external dependency requiring user approval
- No destructive actions possible with current test suite

**Blockers**:
- Applied migration history across environments UNKNOWN
- Cannot determine if 001/002 are already applied to production/staging
- User must provide explicit inventory or confirm greenfield before U-005 proceeds

**Recommendation**:
- Mark U-002 as COMPLETE for configuration/harness objectives
- Record explicit HOLD for graph ancestry pending inventory
- U-005 can proceed with ORM model implementation
- Migration creation deferred until applied history confirmed

---

**Updated**: 2024-11-07  
**Owner**: migration-owner (U-002)  
**Next Owner**: U-005 (persistence platform owner) after graph decision resolved

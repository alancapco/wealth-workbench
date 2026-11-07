# Known Issues · RM Workbench Remediation

**Last Updated:** 7 November 2026  
**QA Lead:** qa-owner  

---

## Issue Classification

- **CRITICAL:** Prevents production deployment; must be fixed before release
- **HIGH:** Major functionality broken or security concern; blocks testing
- **MEDIUM:** Feature incomplete or quality issue; should be fixed before release
- **LOW:** Minor issue or technical debt; can be addressed post-release

---

## Critical Issues

### CRIT-001: Database Migrations Not Implemented
**Severity:** CRITICAL  
**Affected Batch:** U-002  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
Alembic migration files do not exist or are not discoverable. All migration safety tests fail with "No migration files found" or similar errors.

**Impact:**
- Cannot upgrade empty database to current schema
- Cannot test migration safety (downgrade/upgrade cycles)
- Cannot verify schema version tracking
- Production deployment impossible without migrations

**Test Evidence:**
```
ERROR at setup of test_empty_db_upgrade_to_head
ERROR at setup of test_version_table_initialization
ERROR at setup of test_downgrade_upgrade_cycle
ERROR at setup of test_no_silent_stamping
```

**Remediation Plan:**
1. Complete U-002 batch: create Alembic migration files
2. Test empty PostgreSQL database upgrade to head
3. Verify migration graph and ancestry
4. Test downgrade/upgrade cycles
5. Verify no silent stamping behavior

**Assigned To:** migration-owner (U-002 batch owner)  
**Priority:** P0 - Must fix before any deployment

---

### CRIT-002: Tests Running on SQLite Instead of PostgreSQL
**Severity:** CRITICAL  
**Affected Batches:** Multiple (U-005, U-007, U-008, U-010, U-011, U-016)  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
72 tests fail because they run against SQLite, which doesn't support PostgreSQL ARRAY types. Architecture explicitly states "No SQLite migration substitute."

**Error Pattern:**
```
sqlalchemy.exc.CompileError: (in table 'shariah_estimates', column 'evidence_ids'): 
Compiler can't render element of type ARRAY
```

**Affected Tables:**
- `shariah_estimates.evidence_ids` (ARRAY)
- `shariah_screens.non_compliant_holdings` (ARRAY)
- `priorities.reason_keys` (ARRAY)
- `artifact_items` and related tables

**Impact:**
- 72 of 196 tests cannot run (36.7% test failure rate)
- Cannot verify critical functionality:
  - Brief generation and review
  - Meeting capture and extraction
  - Priority evaluation
  - Message drafting
  - Persistence contracts
  - Workflow orchestration

**Remediation Plan:**
1. Set up PostgreSQL 15+ test database (Docker or local)
2. Update pytest configuration to use PostgreSQL
3. Update test fixtures and database URLs
4. Re-run full test suite
5. Expected result: 170-180 of 196 tests passing

**Assigned To:** backend-runtime-owner + persistence-owner  
**Priority:** P0 - Must fix to verify functionality

---

### CRIT-003: Authentication Endpoints Not Implemented
**Severity:** CRITICAL  
**Affected Batch:** U-003  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
Authentication endpoints (AUTH-01, AUTH-02, AUTH-03) are not implemented. Cannot verify login, logout, or session management.

**Missing Endpoints:**
- `GET /auth/login` (AUTH-01) - OIDC initiation
- `GET /auth/callback` (AUTH-02) - OIDC callback handler
- `POST /auth/logout` (AUTH-03) - Session termination

**Impact:**
- Cannot test end-to-end user flows
- Cannot verify session management
- Cannot verify CSRF protection
- Cannot verify tenant/book/client authorization
- Security verification blocked

**Remediation Plan:**
1. Implement OIDC authorization code flow with PKCE
2. Add login/callback/logout endpoints
3. Implement session cookie management
4. Add CSRF token generation and validation
5. Test with fixture OIDC provider

**Assigned To:** backend-security-owner (U-003 batch owner)  
**Priority:** P0 - Required for security verification

---

### CRIT-004: Test Syntax Errors in Message Tests
**Severity:** CRITICAL (now FIXED)  
**Affected Batch:** U-011  
**Discovered:** QA verification, 7 Nov 2026  
**Status:** ✅ FIXED during QA

**Description:**  
`tests/messaging/test_message_drafts.py` had 14 unterminated string literals preventing test collection.

**Error:**
```python
mode="OUTREACH,      # Missing closing quote
channel="EMAIL,      # Missing closing quote
```

**Fix Applied:**
All instances of `mode="VALUE,` changed to `mode="VALUE",` (added closing quote before comma).

**Impact:** Prevented entire test file from running (8 tests).

**Resolution:** Fixed using sed during QA verification. All syntax errors corrected.

---

## High-Priority Issues

### HIGH-001: Missing Core API Endpoints
**Severity:** HIGH  
**Affected Batches:** U-003, U-006, U-007, U-008  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
Several core API endpoint groups are missing or incomplete:

**Missing Endpoints:**
- `GET /session` (API-001) - Current session info
- `GET /calendar/events` (API-022) - Calendar listing
- `POST /calendar/events/{e}/resolutions` (API-023) - Event resolution
- `GET /meetings/{m}` (API-024) - Meeting detail
- `GET /clients/{c}/memory` (API-013) - Memory read
- `POST /clients/{c}/memory/proposals` (API-014) - Memory propose
- `GET /artifacts/{a}` (API-045) - Generic artifact get
- `PATCH /artifacts/{a}` (API-046) - Generic artifact edit
- `POST /telemetry/events` (API-074) - Telemetry recording
- `GET /health/live`, `GET /health/ready` (API-017) - Health checks

**Impact:**
- Cannot test calendar-driven workflows
- Cannot test meeting resolution flow
- Cannot test memory management
- Cannot test artifact versioning
- Cannot record telemetry events
- Cannot verify health/readiness

**Remediation Plan:**
1. Implement session endpoint (U-003)
2. Implement calendar endpoints (U-006)
3. Implement meetings endpoint (U-006)
4. Implement memory endpoints (U-007)
5. Implement generic artifact endpoints (U-005)
6. Implement telemetry endpoint (U-013)
7. Implement health endpoints (U-001)

**Assigned To:** Respective batch owners  
**Priority:** P0 - Required for feature completeness

---

### HIGH-002: Frontend Implementation Minimal
**Severity:** HIGH  
**Affected Batches:** U-004, U-007, U-008, U-011, U-014, U-015, U-016  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
Only 3 frontend pages exist; ~17+ pages expected from requirements.

**Implemented:**
- `app/layout.tsx` - Main layout
- `app/page.tsx` - Home page  
- `app/brief/[clientId]/page.tsx` - Brief detail

**Missing:**
- Client list page
- Dashboard/My Day page
- Priority list page
- Meeting capture UI
- Transcript review UI
- Message composer UI
- Product search UI
- Workflow pages
- Admin configuration UI
- Shariah review UI
- Family/household UI
- All shared components

**Impact:**
- Cannot perform end-to-end UI testing
- Cannot verify user workflows
- Cannot verify accessibility
- Cannot verify mobile responsiveness
- Production UI not ready

**Remediation Plan:**
1. Complete U-004 shared components
2. Complete U-007 brief UI
3. Complete U-008 capture UI
4. Complete U-010 priority UI
5. Complete U-011 message UI
6. Complete U-012 product UI
7. Complete U-013 admin UI
8. Complete U-014 mobile responsiveness
9. Complete U-015 Shariah UI
10. Complete U-016 family UI

**Assigned To:** Frontend owners for each batch  
**Priority:** P0 - UI required for production

---

### HIGH-003: No Frontend Tests
**Severity:** HIGH  
**Affected Batch:** U-004  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
No frontend unit tests, component tests, or E2E tests found.

**Impact:**
- Cannot verify UI functionality
- Cannot catch regressions
- Cannot verify accessibility
- No component contract tests
- No integration tests

**Remediation Plan:**
1. Set up Jest/React Testing Library for unit tests
2. Set up Playwright or Cypress for E2E tests
3. Write component tests for shared components
4. Write page tests for each route
5. Write E2E tests for critical user flows
6. Add accessibility tests (axe-core)

**Assigned To:** frontend-foundation-owner (U-004)  
**Priority:** P1 - Required before production

---

## Medium-Priority Issues

### MED-001: Deprecated datetime.utcnow() Usage
**Severity:** MEDIUM  
**Affected Batches:** Multiple  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
39 deprecation warnings for `datetime.utcnow()` usage. Python 3.13 will remove this function.

**Affected Files:**
- `app/services/config/telemetry_service.py:56`
- `app/services/product/suitability_service.py:87, 168`
- `tests/test_config_audit.py:281`
- And others (39 total occurrences)

**Remediation:**
Replace all instances:
```python
# Old (deprecated)
datetime.utcnow()

# New (correct)
datetime.now(datetime.UTC)
```

**Impact:**
- Code will break in future Python versions
- Warnings clutter test output

**Assigned To:** All batch owners  
**Priority:** P2 - Technical debt cleanup

---

### MED-002: Pytest Asyncio Configuration Warning
**Severity:** MEDIUM  
**Affected Batch:** U-001  
**Discovered:** QA verification, 7 Nov 2026

**Description:**
```
PytestDeprecationWarning: The configuration option "asyncio_default_fixture_loop_scope" is unset.
```

**Remediation:**
Add to `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
```

**Impact:** Future pytest-asyncio versions may behave differently

**Assigned To:** backend-runtime-owner  
**Priority:** P2 - Configuration cleanup

---

### MED-003: Alembic Configuration Deprecations
**Severity:** MEDIUM  
**Affected Batch:** U-002  
**Discovered:** QA verification, 7 Nov 2026

**Description:**
Two Alembic deprecation warnings:
```
DeprecationWarning: No path_separator found in configuration
DeprecationWarning: The version_path_separator configuration parameter is deprecated
```

**Remediation:**
Add to `alembic.ini`:
```ini
path_separator = os
# Remove version_path_separator if present
```

**Impact:** Future Alembic versions may not work correctly

**Assigned To:** migration-owner (U-002)  
**Priority:** P2 - Configuration cleanup

---

### MED-004: Pydantic v2 Migration Warnings
**Severity:** MEDIUM  
**Affected Batches:** Multiple  
**Discovered:** QA verification, 7 Nov 2026

**Description:**
```
PydanticDeprecatedSince20: `__get_validators__` is deprecated and will be removed, 
use `__get_pydantic_core_schema__` instead.
```

**Impact:**
- 3 warnings in test output
- May break with Pydantic v3

**Remediation:**
- Identify which models use old Pydantic v1 API
- Update to Pydantic v2 API
- Or update dependencies if from third-party packages

**Assigned To:** backend-platform-owner  
**Priority:** P2 - Dependency maintenance

---

### MED-005: pyproject.toml Deprecation Warning
**Severity:** MEDIUM  
**Affected Batch:** U-001  
**Discovered:** QA verification, 7 Nov 2026

**Description:**
```
warning: The `tool.uv.dev-dependencies` field (used in `pyproject.toml`) is deprecated 
and will be removed in a future release; use `dependency-groups.dev` instead
```

**Remediation:**
Update `backend/pyproject.toml`:
```toml
# Old
[tool.uv.dev-dependencies]

# New
[dependency-groups]
dev = [...]
```

**Impact:** Future uv versions may not recognize dev dependencies

**Assigned To:** backend-runtime-owner  
**Priority:** P2 - Configuration cleanup

---

## Low-Priority Issues

### LOW-001: No API Documentation
**Severity:** LOW  
**Affected Batches:** All  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
No OpenAPI/Swagger documentation found or accessible.

**Remediation:**
- FastAPI auto-generates OpenAPI schema
- Expose at `/docs` endpoint
- Add descriptions to all endpoints
- Add request/response examples

**Impact:** Developers/QA cannot easily explore API

**Assigned To:** backend-platform-owner  
**Priority:** P3 - Documentation

---

### LOW-002: No Deployment Scripts
**Severity:** LOW  
**Affected Batches:** U-017  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
No deployment scripts, Docker files, or infrastructure-as-code found.

**Remediation:**
- Create Dockerfile for backend
- Create Dockerfile for frontend
- Create docker-compose for local development
- Create deployment scripts for production
- Document environment variables

**Impact:** Manual deployment error-prone

**Assigned To:** DevOps/SRE (external)  
**Priority:** P3 - Pre-deployment

---

### LOW-003: No Monitoring/Logging Setup
**Severity:** LOW  
**Affected Batches:** U-013  
**Discovered:** QA verification, 7 Nov 2026

**Description:**  
No structured logging, no monitoring integration, no alerting setup.

**Remediation:**
- Add structured JSON logging
- Integrate with monitoring service (DataDog, New Relic, etc.)
- Set up error tracking (Sentry)
- Configure alerts for critical errors

**Impact:** Cannot monitor production health

**Assigned To:** DevOps/SRE (external)  
**Priority:** P3 - Operations readiness

---

## Issue Statistics

**Total Issues:** 16  
- Critical: 4 (1 fixed)
- High: 3  
- Medium: 5  
- Low: 3  

**By Status:**
- Open: 15
- Fixed: 1

**By Category:**
- Testing: 4
- Implementation: 5
- Configuration: 4
- Documentation: 1
- Infrastructure: 2

---

## Resolution Tracking

| Issue | Severity | Status | Assigned To | Target Date | Resolved Date |
|-------|----------|--------|-------------|-------------|---------------|
| CRIT-001 | CRITICAL | Open | migration-owner | TBD | - |
| CRIT-002 | CRITICAL | Open | backend-runtime-owner | TBD | - |
| CRIT-003 | CRITICAL | Open | backend-security-owner | TBD | - |
| CRIT-004 | CRITICAL | ✅ Fixed | qa-owner | - | 2026-11-07 |
| HIGH-001 | HIGH | Open | Multiple owners | TBD | - |
| HIGH-002 | HIGH | Open | Frontend owners | TBD | - |
| HIGH-003 | HIGH | Open | frontend-foundation-owner | TBD | - |
| MED-001 | MEDIUM | Open | All owners | TBD | - |
| MED-002 | MEDIUM | Open | backend-runtime-owner | TBD | - |
| MED-003 | MEDIUM | Open | migration-owner | TBD | - |
| MED-004 | MEDIUM | Open | backend-platform-owner | TBD | - |
| MED-005 | MEDIUM | Open | backend-runtime-owner | TBD | - |
| LOW-001 | LOW | Open | backend-platform-owner | TBD | - |
| LOW-002 | LOW | Open | DevOps/SRE | TBD | - |
| LOW-003 | LOW | Open | DevOps/SRE | TBD | - |

---

## Next Steps

1. **Immediate:** Fix CRIT-001, CRIT-002, CRIT-003 (P0 blockers)
2. **Week 1:** Complete HIGH-001 missing endpoints
3. **Weeks 2-4:** Complete HIGH-002 frontend implementation
4. **Week 5:** Add HIGH-003 frontend tests
5. **Week 6:** Fix all MEDIUM issues (deprecations, config)
6. **Pre-deployment:** Address LOW issues (docs, deployment, monitoring)

---

**Report Generated:** 7 November 2026  
**Next Update:** After P0 issues resolved

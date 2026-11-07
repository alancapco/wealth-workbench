# Testing Guide - RM Workbench Backend

## Overview

The RM Workbench backend uses **PostgreSQL 15+** for testing to ensure compatibility with production ARRAY types and other PostgreSQL-specific features. Tests run against a containerized PostgreSQL instance.

## Prerequisites

- Docker (for PostgreSQL test container)
- Python 3.11+ 
- uv package manager

## Quick Start

### Run All Tests

```bash
cd backend
./scripts/run_tests.sh
```

This script will:
1. Start PostgreSQL test container on port 5433
2. Run the full test suite
3. Stop the container when done

### Run Tests Manually

If you prefer to manage the container separately:

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.test.yml up -d

# Wait for PostgreSQL to be ready (about 5 seconds)
sleep 5

# Run tests
uv run pytest --tb=short -v

# Stop container when done
docker-compose -f docker-compose.test.yml down
```

### Run Specific Tests

```bash
# Single test file
uv run pytest tests/test_readiness.py -v

# Single test function
uv run pytest tests/test_readiness.py::test_readiness_degraded_without_db -v

# Tests matching a pattern
uv run pytest -k "workflow" -v
```

## Test Configuration

### Database Connection

Tests use a dedicated PostgreSQL database configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
env = [
    "DATABASE_URL=postgresql+asyncpg://workbench_test:test_password@localhost:5433/workbench_test",
    "AUTH_MODE=fixture",
    "APP_ENV=test",
]
```

### Test Fixtures

**Session-scoped fixtures** (created once per test run):
- `test_engine`: PostgreSQL connection engine with schema initialization

**Function-scoped fixtures** (created/destroyed per test):
- `db_session`: Clean database session with automatic rollback

## Test Database Lifecycle

1. **Session Start**: Drop all tables, recreate schema from SQLAlchemy models
2. **Each Test**: Fresh session with automatic rollback (no data persists between tests)
3. **Session End**: Dispose engine, clean up connections

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: workbench_test
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: workbench_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Run tests
        run: |
          cd backend
          uv run pytest --tb=short -v
```

### GitLab CI Example

```yaml
test:
  image: python:3.11
  services:
    - postgres:15-alpine
  variables:
    POSTGRES_USER: workbench_test
    POSTGRES_PASSWORD: test_password
    POSTGRES_DB: workbench_test
    DATABASE_URL: postgresql+asyncpg://workbench_test:test_password@postgres:5432/workbench_test
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="/root/.cargo/bin:$PATH"
  script:
    - cd backend
    - uv run pytest --tb=short -v
```

## Test Data Management

### Philosophy

- **No persistent test data**: Each test starts with a clean slate
- **Fixture-based setup**: Tests create their own required data
- **Isolation**: Tests never share data or depend on execution order

### Example Test Pattern

```python
async def test_create_client(db_session):
    # Arrange: Create test data
    client = Client(
        name="Test Client",
        email="test@example.com"
    )
    db_session.add(client)
    await db_session.flush()
    
    # Act: Perform operation
    result = await get_client(db_session, client.id)
    
    # Assert: Verify outcome
    assert result.name == "Test Client"
    
    # Cleanup: Automatic via session rollback
```

## Current Test Status

**As of CRIT-002 fix:**
- **Total Tests**: 222
- **Passing**: 150 (67.6%)
- **Errors**: 72 (32.4%)

### Passing Test Categories

✅ Readiness and boot checks
✅ Configuration management and audit
✅ Workflow orchestration
✅ Action approval workflows
✅ Message validation (non-draft tests)
✅ Priority ranking logic
✅ Product suitability checks
✅ Shariah pilot features

### Known Failing Categories

❌ **Schema Issues** (24 tests)
- Missing `tenant_id` column in `clients` table breaks family relationship foreign keys
- Affects: briefs, capture, persistence, family tests

❌ **Implementation Gaps** (48 tests)  
- Features partially implemented or awaiting integration
- Affects: message drafts, migration safety, workflow persistence

## Troubleshooting

### Container Won't Start

```bash
# Check if port 5433 is already in use
lsof -i :5433

# Stop any existing containers
docker-compose -f docker-compose.test.yml down

# Remove old containers and volumes
docker-compose -f docker-compose.test.yml down -v
```

### Connection Refused

```bash
# Check container status
docker-compose -f docker-compose.test.yml ps

# View logs
docker-compose -f docker-compose.test.yml logs

# Wait longer for PostgreSQL to be ready
sleep 10
```

### Schema Errors

If you see foreign key or column errors:

1. Ensure latest migrations are applied
2. Check that test fixtures recreate schema correctly
3. Verify model definitions match foreign key references

## Performance Tips

### Parallel Execution

```bash
# Install pytest-xdist
uv add --dev pytest-xdist

# Run tests in parallel (4 workers)
uv run pytest -n 4
```

**Note**: Session-scoped fixtures may need adjustment for parallel execution.

### Faster Feedback

```bash
# Stop on first failure
uv run pytest -x

# Run only failed tests from last run
uv run pytest --lf

# Run failed tests first, then others
uv run pytest --ff
```

## Next Steps

1. **Fix schema issues**: Add `tenant_id` to `clients` table or adjust family model foreign keys
2. **Complete implementations**: Fill gaps in message drafts, migration, and persistence tests
3. **Enable parallel execution**: Adjust fixtures for `pytest-xdist` compatibility
4. **Add integration tests**: Test full end-to-end workflows with real database transactions

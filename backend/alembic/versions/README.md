# Alembic Migration Configuration

This directory contains database migrations using Alembic.

## Running Migrations

```bash
# Apply all pending migrations
cd backend
source venv/bin/activate
alembic upgrade head

# Create a new migration
alembic revision -m "description"

# Rollback one migration
alembic downgrade -1
```

## Migration History

- `001_add_briefs_audit.py`: Add briefs and audit_logs tables for versioning and compliance

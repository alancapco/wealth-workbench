#!/bin/sh
set -eu

echo "[backend] waiting for database..."
python - <<'PY'
import asyncio
import os
import sys
import time

url = os.environ.get("DATABASE_URL", "").strip()
if not url:
    print("[backend] DATABASE_URL is required", file=sys.stderr)
    sys.exit(1)

async_url = url.replace("postgresql://", "postgresql+asyncpg://", 1) if url.startswith("postgresql://") else url

async def wait() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text

    engine = create_async_engine(async_url, pool_pre_ping=True)
    deadline = time.time() + 90
    last = None
    while time.time() < deadline:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            print("[backend] database is reachable")
            return
        except Exception as exc:  # noqa: BLE001 — retry until deadline
            last = exc
            time.sleep(2)
    await engine.dispose()
    print(f"[backend] database not ready: {last}", file=sys.stderr)
    sys.exit(1)

asyncio.run(wait())
PY

echo "[backend] running migrations..."
alembic upgrade head

if [ "${SEED_DEMO_DATA:-false}" = "true" ] && [ "${AUTH_MODE:-}" = "fixture" ]; then
  echo "[backend] seeding demo data..."
  python -m app.scripts.seed_demo_data || echo "[backend] seed failed (continuing)"
fi

echo "[backend] starting: $*"
exec "$@"

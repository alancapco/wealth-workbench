"""Lazy async database resources.

Importing this module never opens a connection; request/use-case code owns transactions.
"""
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

Base = declarative_base()


def _async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None
if settings.database_configured:
    engine = create_async_engine(
        _async_url(settings.DATABASE_URL),
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session without implicit commit; use cases own transaction boundaries."""
    if async_session_maker is None:
        raise RuntimeError("Database is not configured")
    async with async_session_maker() as session:
        yield session


async def check_database() -> tuple[bool, bool]:
    """Return connectivity and schema-head status without modifying the database."""
    if engine is None:
        return False, False
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            # A configured expected head is required for an honest schema check.
            expected = settings.EXPECTED_SCHEMA_HEAD
            if not expected:
                return True, False
            exists = await connection.execute(
                text("SELECT to_regclass('public.alembic_version')")
            )
            if exists.scalar_one_or_none() is None:
                return True, False
            current = await connection.execute(text("SELECT version_num FROM alembic_version"))
            heads = {str(row[0]) for row in current.fetchall()}
            return True, heads == {expected}
    except Exception:
        return False, False

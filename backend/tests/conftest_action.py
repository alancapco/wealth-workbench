"""Shared test fixtures for action approval tests."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.database import Base


@pytest_asyncio.fixture
async def db_session():
    """
    Create isolated test database session.
    Uses in-memory SQLite for speed in isolated tests.
    """
    # Create async engine with SQLite in-memory
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    await engine.dispose()

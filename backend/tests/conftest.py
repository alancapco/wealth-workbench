"""Pytest fixtures for all tests."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest_asyncio.fixture
async def db_session():
    """Create async test database session with in-memory SQLite.
    
    Note: U-008 spec requires PostgreSQL 15 for real integration tests.
    This is a basic fixture for unit tests only.
    """
    # In-memory SQLite for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
    
    await engine.dispose()

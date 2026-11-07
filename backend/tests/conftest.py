"""Pytest fixtures for all tests."""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base
from app.core.config import settings


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine and initialize schema once per test session."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    
    # Drop and recreate all tables for clean test state
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Provide clean database session for each test with rollback."""
    async_session = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

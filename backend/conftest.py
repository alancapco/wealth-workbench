import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Test database connection - now using same postgres instance, different database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://workbench_test:test_password@localhost:5432/workbench_test"
)

@pytest.fixture(scope="session")
async def engine():
    """Create async engine for tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(engine):
    """Create async session for each test."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

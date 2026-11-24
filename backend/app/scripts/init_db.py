"""
Database initialization - Create tables
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine, Base
import app.models  # noqa: F401  # registers every ORM model with Base.metadata


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # aaoifi_clauses.embedding is VECTOR(1536); the type must exist before
        # create_all compiles that column, so this cannot run after create_all.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully")


if __name__ == "__main__":
    asyncio.run(init_db())

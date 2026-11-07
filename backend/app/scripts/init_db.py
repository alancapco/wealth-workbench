"""
Database initialization - Create tables
"""
import asyncio
from app.core.database import engine, Base
from app.models.models import (
    Client, Holding, MarketTick, Interaction, Brief,
    WorkflowInstance, AuditEvent
)

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Drop all tables (for fresh start in development)
        # Comment this out in production!
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_db())

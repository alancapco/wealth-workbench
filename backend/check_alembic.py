import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://rm_user:demo_password_123@localhost:5432/rm_workbench')
    async with engine.connect() as conn:
        # Check for alembic_version table
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema='public' AND table_name='alembic_version')"
        ))
        exists = result.scalar()
        print(f'alembic_version table exists: {exists}')
        
        if exists:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            print(f'Current version: {version}')
    await engine.dispose()

asyncio.run(check())

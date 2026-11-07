import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine('postgresql+asyncpg://rm_user:demo_password_123@localhost:5432/rm_workbench')
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
        tables = [row[0] for row in result]
        print(f'Tables in DB: {len(tables)}')
        for table in tables:
            print(f'  {table}')
    await engine.dispose()

asyncio.run(check())


import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Connection string
CONN_STR = "postgresql+asyncpg://postgres@localhost:5432/hardipatel"

async def drop_tables():
    print(f"Connecting to {CONN_STR}...")
    try:
        engine = create_async_engine(CONN_STR)
        async with engine.connect() as conn:
            # Drop tables in reverse order of dependency
            print("Dropping 'session_events' just in case (renamed from design doc?)...")
            await conn.execute(text("DROP TABLE IF EXISTS session_events CASCADE"))
            
            print("Dropping 'events' (ADK table)...")
            await conn.execute(text("DROP TABLE IF EXISTS events CASCADE"))
            
            print("Dropping 'sessions'...")
            await conn.execute(text("DROP TABLE IF EXISTS sessions CASCADE"))
            
            print("Tables dropped. Rerunning verification...")
            await conn.commit()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(drop_tables())

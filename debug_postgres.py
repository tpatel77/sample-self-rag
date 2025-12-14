
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Connection string from the failing YAML
CONN_STR = "postgresql+asyncpg://postgres@localhost:5432/hardipatel"

async def test_connection():
    print(f"Connecting to {CONN_STR}...")
    try:
        engine = create_async_engine(CONN_STR)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"Connection successful: {result.scalar()}")
            
            # Check permissions
            await conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id serial PRIMARY KEY)"))
            print("Create table successful.")
            await conn.execute(text("DROP TABLE test_table"))
            print("Drop table successful.")
            
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())

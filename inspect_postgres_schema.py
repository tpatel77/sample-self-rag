
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Connection string
CONN_STR = "postgresql+asyncpg://postgres@localhost:5432/hardipatel"

async def inspect_db():
    print(f"Connecting to {CONN_STR}...")
    try:
        engine = create_async_engine(CONN_STR)
        async with engine.connect() as conn:
            # Check existing tables
            result = await conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ))
            tables = [row[0] for row in result]
            print(f"Tables found: {tables}")
            
            if 'sessions' in tables:
                print("\nColumns in 'sessions':")
                cols = await conn.execute(text(
                     "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='sessions'"
                ))
                for row in cols:
                    print(f" - {row[0]}: {row[1]}")

                # Check constraints/PK
                print("\nConstraints on 'sessions':")
                cons = await conn.execute(text(
                    """
                    SELECT conname, pg_get_constraintdef(oid) 
                    FROM pg_constraint 
                    WHERE conrelid = 'sessions'::regclass
                    """
                ))
                for row in cons:
                    print(f" - {row[0]}: {row[1]}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_db())

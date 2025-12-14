
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

CONN_STR = "postgresql+asyncpg://postgres@localhost:5432/hardipatel"

async def check_data():
    engine = create_async_engine(CONN_STR)
    async with engine.connect() as conn:
        print("Checking Sessions...")
        result = await conn.execute(text("SELECT id, state FROM sessions"))
        sessions = result.fetchall()
        for s in sessions:
            print(f"Session: {s[0]}")
            print(f"State: {s[1]}")
        
        print("\nChecking Events (History)...")
        # ADK events table usually has 'content' or 'input_transcription'
        # The failed SQL earlier showed 'content', 'input_transcription', 'output_transcription' columns
        result = await conn.execute(text("SELECT session_id, timestamp, content, input_transcription FROM events ORDER BY timestamp DESC LIMIT 5"))
        events = result.fetchall()
        for e in events:
            # content is often JSONB
            print(f"Event Time: {e[1]}")
            print(f"Input: {e[3]}")
            print(f"Content: {e[2]}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_data())

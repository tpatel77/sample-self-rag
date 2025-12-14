
import os
from google.adk.sessions.database_session_service import DatabaseSessionService
from sqlalchemy import create_engine, inspect

# Use local sqlite for safety/speed (Sync for inspection)
TEST_DB_URL = "sqlite:///test_schema.db"

# Cleanup previous run
if os.path.exists("test_schema.db"):
    os.remove("test_schema.db")

print(f"Initializing Service with {TEST_DB_URL}...")
# DatabaseSessionService supports sync URLs via internal logic or we might need to patch it?
# Actually DatabaseSessionService EXPECTS async strings usually.
# But for Schema INTROSPECTION we can just CREATE tables using the service. 
# Wait, DatabaseSessionService uses AsyncEngine.
# So we must use async URL for the SERVICE, but Sync Engine for INSPECTION.

# We need TWO URLs.
ASYNC_DB_URL = "sqlite+aiosqlite:///test_schema.db"
SYNC_DB_URL = "sqlite:///test_schema.db"

print(f"Initializing Service with {ASYNC_DB_URL}...")
import asyncio

async def setup():
    svc = DatabaseSessionService(db_url=ASYNC_DB_URL)
    # Force table creation by creating a session
    await svc.create_session("app", "user", "session_1")
    return svc

# Run async setup
asyncio.run(setup())

print("Service Initialized. Checking tables...")
# Use Sync URL for inspection
engine = create_engine(SYNC_DB_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"Tables found: {tables}")

if "sessions" in tables or "adk_sessions" in tables:
    print("SUCCESS: Tables were automatically created.")
    # Print columns to compare with user's design
    for t in tables:
        print(f"\nColumns in {t}:")
        for col in inspector.get_columns(t):
            print(f" - {col['name']} ({col['type']})")
else:
    print("FAILURE: No tables created. Manual schema setup might be required.")

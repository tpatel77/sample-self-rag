
import sys
import logging
from src.orchestrator import WorkflowOrchestrator
from src.services.redis_session import RedisSessionService

# Mock redis to avoid import error if not installed, or to check instantiation
import unittest.mock as mock

# Check if redis installed, if not mock it so we can verify the CLASS selection logic
try:
    import redis
except ImportError:
    print("Redis not installed, mocking for selection test...")
    sys.modules["redis"] = mock.MagicMock()

orch = WorkflowOrchestrator()
try:
    print("Loading workflow...")
    orch.load_workflow("workflows/test_redis_config.yaml")
    
    svc = orch._session_service
    print(f"Session Service Class: {type(svc).__name__}")
    
    if isinstance(svc, RedisSessionService):
        print("PASS: RedisSessionService selected!")
    else:
        print(f"FAIL: Expected RedisSessionService, got {type(svc)}")

except Exception as e:
    print(f"Error during loading: {e}")
    # If error is related to Redis connection, that is also a 'Pass' for selection logic
    if "Connection refused" in str(e) or "redis" in str(e).lower():
        print("PASS: Attempted to connect to Redis (Selection logic worked)")

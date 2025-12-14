import asyncio
import os
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

from src.orchestrator import WorkflowOrchestrator as Orchestrator
from src.core.callbacks.registry import register_callback, CallbackRegistry
from src.tools.registry import ToolRegistry
import src.tools.builtin # Register built-ins
tool_registry = ToolRegistry().get_all()

# --- Define Callbacks ---
LOGS = []

@register_callback("log_agent_start")
def log_agent_start(event_type, agent_name, data):
    print(f"Callback invoked: {event_type} for {agent_name} data: {data}")
    LOGS.append(f"{event_type}:{agent_name}")

@register_callback("log_agent_finish")
def log_agent_finish(event_type, agent_name, data):
    print(f"Callback invoked: {event_type} for {agent_name} data: {data}")
    LOGS.append(f"{event_type}:{agent_name}")

@register_callback("log_tool_start")
def log_tool_start(event_type, tool_name, data):
    print(f"Callback invoked: {event_type} for {tool_name} data: {data}")
    LOGS.append(f"{event_type}:{tool_name}")

@register_callback("log_tool_finish")
def log_tool_finish(event_type, tool_name, data):
    print(f"Callback invoked: {event_type} for {tool_name} data: {data}")
    LOGS.append(f"{event_type}:{tool_name}")

async def test_callbacks():
    print("--- Running Custom Callbacks Test ---")
    
    orchestrator = Orchestrator(
        app_name="adk_callback_test"
    )
    
    yaml_path = "workflows/test_callbacks.yaml"
    print(f"Loading workflow from {yaml_path}...")
    orchestrator.load_workflow(yaml_path)
    
    print("Executing workflow...")
    await orchestrator.run_async(user_input="Test")
    print("Workflow execution completed.")

    print("\nVerifying Callbacks...")
    expected_logs = [
        "agent_start:callback_tester",
        "tool_start:echo_tool",
        "tool_finish:echo_tool",
        "agent_finish:callback_tester"
    ]
    
    passed = True
    for expected in expected_logs:
        if expected in LOGS:
            print(f"[PASS] Found expected log: {expected}")
        else:
            print(f"[FAIL] Missing expected log: {expected}")
            passed = False
            
    if passed:
        print("\n[SUCCESS] All callbacks executed correctly!")
    else:
        print(f"\n[FAIL] Callback logs: {LOGS}")

if __name__ == "__main__":
    asyncio.run(test_callbacks())

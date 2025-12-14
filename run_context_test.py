
import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.getcwd())

from src.orchestrator import WorkflowOrchestrator

async def test_context():
    print("--- Running Context Management Test ---")
    
    orchestrator = WorkflowOrchestrator()
    yaml_path = "workflows/test_context.yaml"
    print(f"Loading workflow from {yaml_path}...")
    orchestrator.load_workflow(yaml_path)
    print(f"DEBUG update_session_state help:")
    # help(orchestrator._session_service._update_session_state)
    from google.adk.events import Event
    print(f"DEBUG Event dir: {dir(Event)}")
    help(Event)
    
    print("Executing workflow with initial state injection...")
    
    # We inject 'injected_var' which isn't used by the YAML explicitely 
    # but demonstrates the mechanism.
    # The YAML uses {status} and {env}.
    # 'env' is set in YAML initial state as 'test'.
    # 'status' is set by pre_hook/post_hook.
    
    # We will also try to override 'env' via injection to see precedence?
    # Logic: Injection happens at 'workflow' scope. 
    # YAML initial state happens at 'global' (if global config) or 'workflow' (if AgentContextConfig?? No, GlobalContextConfig).
    # In my implementation: 
    # StateManager init loads GlobalContextConfig.initial into 'global'.
    # Orchestrator injects initial_state into 'workflow'.
    # StateManager.get checks: Agent -> Workflow -> User -> Global.
    # So Injection (Workflow) should override Global config.
    
    print("Executing workflow with initial state injection...")
    
    final_response = ""
    async for event in orchestrator.run_stream(
        user_input="Start context test",
        user_id="context_tester",
        initial_state={
            "injected_var": "I am here",
            "env": "overridden_by_injection" 
        }
    ):
        if hasattr(event, 'content') and event.content:
             print(f"[Event] Content: {event.content.parts[0].text if event.content.parts else ''}")
             if event.content.parts:
                 final_response = event.content.parts[0].text
        else:
             print(f"[Event] Type: {type(event)}")

    
    print("Workflow Result:")
    print(final_response)
    
    # Internal Inspection of custom StateManager
    print("\nVerifying StateManager (Custom System)...")
    sm = orchestrator.builder.state_manager
    # We expect 'workflow' scope to have 'status' and 'env'
    # Scope ID logic: workflow -> session_id
    # We used session_id="session_test_context" (default) or whatever orchestrator used.
    # Actually orchestrator uses passed session_id which was None -> defaults to f"session_{config.name}" = session_test_context
    
    # But wait, run_stream internal session_id might be session_test_context
    target_session = f"session_{orchestrator.config.name}"
    
    # Correct ID strategy: Check available sessions
    if hasattr(orchestrator._session_service, "sessions") and orchestrator._session_service.sessions:
        # Use the first available session key (likely 'adk_workflow')
        target_session = list(orchestrator._session_service.sessions.keys())[0]
        print(f"DEBUG: derived target_session = {target_session}")

    try:
        # workflow_store = sm.stores["workflow"]
        # print(f"DEBUG StateManager Keys: {list(workflow_store._data.keys())}")
        
        sm_val = sm.get("workflow", "status", session_id=target_session)
        print(f"StateManager 'status': {sm_val}")
        
        sm_env = sm.get("workflow", "env", session_id=target_session)
        print(f"StateManager 'env': {sm_env}")
        
        state_pass = True
        if sm_val == "completed":
            print("[PASS] StateManager captured hook update.")
        else:
             print(f"[FAIL] StateManager missed hook update. Got: {sm_val}")
             state_pass = False
             
        if sm_env == "overridden_by_injection":
            print("[PASS] StateManager captured injection.")
        else:
             print(f"[FAIL] StateManager missed injection. Got: {sm_env}")
             state_pass = False
             
        if state_pass:
            print("[SUCCESS] State Management System verified.")

    except Exception as e:
        print(f"Error inspecting StateManager: {e}")

    print("\nVerifying State (Internal Inspection)...")
    if hasattr(orchestrator._session_service, "sessions"):
        print(f"DEBUG Sessions Keys: {list(orchestrator._session_service.sessions.keys())}")
        # print(f"DEBUG Session Content: {orchestrator._session_service.sessions}")
    
    # Direct access to session service since we are async
    session = await orchestrator._session_service.get_session(
        app_name=orchestrator.app_name,
        user_id="context_tester",
        session_id=f"session_{orchestrator.config.name}"
    )
    state = dict(session.state) if session else {}
    print("Final Session State:", state)
    
    # Verification Logic
    # 1. 'getter' agent output should reflect 'status' set by 'setter' hook.
    # 2. 'env' should be 'overridden_by_injection'.
    
    if "Status: completed" in final_response:
        print("[PASS] Hook execution verified (Status=completed)")
    else:
        print(f"[FAIL] Hook execution failed. Output: {final_response}")
        
    if "Env: overridden_by_injection" in final_response:
         print("[PASS] Initial state injection verified (Env=overridden)")
    else:
         print(f"[FAIL] Injection failed. Output: {final_response}")

if __name__ == "__main__":
    asyncio.run(test_context())


import asyncio
import os
from src.cli import main

# Ensure src is in python path
try:
    from src.orchestrator import WorkflowOrchestrator
except ImportError:
    import sys
    sys.path.append(os.getcwd())
    from src.orchestrator import WorkflowOrchestrator

def run_synchronous_example():
    """
    Example of running a workflow synchronously using the Orchestrator.
    """
    print("--- Running Synchronous Example (Tool Chain) ---")
    
    # 1. Initialize Orchestrator
    orchestrator = WorkflowOrchestrator()
    
    # 2. Load a YAML configuration
    # We use the tool chain example as it doesn't require API keys or input
    yaml_path = "workflows/example_tool_chain.yaml"
    config_name = os.path.basename(yaml_path).replace(".yaml", "") # Added config_name
    print(f"Loading workflow from {yaml_path}...")
    orchestrator.load_workflow(yaml_path)
    
    # 3. Run the workflow
    # For tool chain, input isn't strictly used but we pass something
    print(f"Executing workflow '{config_name}' from {yaml_path}...")
    
    # Example: Injecting initial state context
    initial_context = {
        "user_preference": "verbose",
        "environment": "production"
    }
    
    result = await orchestrator.run_async( # Changed to run_async and await
        user_input="Analyze the dataset", # Changed user_input
        user_id="sdk_user",
        initial_state=initial_context # Added initial_state
    )
    
    print(f"\nFinal Result:\n{result}") # Added this print
    print("Workflow Result:") # Kept existing print for result
    print(result)
    print("---------------------------------------------")

async def run_asynchronous_example():
    """
    Example of running a workflow asynchronously.
    """
    print("\n--- Running Asynchronous Example (Simple Echo) ---")
    
    orchestrator = WorkflowOrchestrator()
    orchestrator.load_workflow("workflows/simple_echo.yaml")
    
    print("Executing workflow async...")
    
    # We can use run_async directly
    # Note: run_async yields events, so we iterate or gather
    # But usually orchestrator.run() handles loop.
    # To run truly async and get events:
    
    final_response = ""
    async for event in orchestrator.run_stream(
        user_input="Hello from Python SDK!",
        user_id="async_sdk_user"
    ):
        # Process events (logs, tool outputs, etc.)
        # Simply print the event type or content
        if hasattr(event, "content") and event.content:
             print(f"[Event] {event.content.parts[0].text if event.content.parts else ''}")
             
    print("Async workflow completed.")

if __name__ == "__main__":
    # Run sync example
    run_synchronous_example()
    main()
    
    # Run async example
    try:
        asyncio.run(run_asynchronous_example())
    except KeyboardInterrupt:
        pass

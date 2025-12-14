
import sys
from pathlib import Path
import asyncio

# Add project root to path
sys.path.append("/Users/hardipatel/Code/sample-self-rag")

from src.orchestrator import WorkflowOrchestrator

async def main():
    print("Initializing Orchestrator...")
    orchestrator = WorkflowOrchestrator()
    
    workflow_path = Path("/Users/hardipatel/Code/sample-self-rag/tests/test_callback_workflow.yaml")
    print(f"Loading workflow: {workflow_path}")
    orchestrator.load_workflow(workflow_path)
    
    print("\nRunning workflow...")
    # input doesn't really matter for this specific prompt
    result = await orchestrator.run_async("Generate the person data now.")
    
    print("\nWorkflow Run Complete.")
    print(f"Final Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())

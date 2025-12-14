
import sys
from pathlib import Path

# Add project root to path
sys.path.append("/Users/hardipatel/Code/sample-self-rag")

from src.core.workflow_builder import WorkflowBuilder

def check_config():
    builder = WorkflowBuilder()
    builder.load_config("/Users/hardipatel/Code/sample-self-rag/rag/document_processor.yaml")
    
    # Manually trigger the build part that configures lifecycle agents
    # We can't call build_from_yaml because it does everything.
    # Let's just create a dummy agent and try to configure logic matching build_from_yaml
    
    print("Debug: Inspecting Config Loader")
    config = builder.get_config()
    if config and config.workflow.lifecycle and config.workflow.lifecycle.exit:
        print(f"YAML Config: emit_full_state = {config.workflow.lifecycle.exit.emit_full_state}")
    
    # Now let's try to simulate what build_from_yaml does to the ExitAgent
    from src.core.lifecycle_agents import ExitAgent
    exit_agent = ExitAgent()
    print(f"Default ExitAgent: emit_full_state = {exit_agent.emit_full_state}")
    
    if config:
        if config.workflow.lifecycle:
            lifecycle = config.workflow.lifecycle
            if lifecycle.exit:
                if lifecycle.exit.emit_full_state:
                    print("Condition 'if lifecycle.exit.emit_full_state' evaluated to TRUE")
                    exit_agent.emit_full_state = lifecycle.exit.emit_full_state
                else:
                    print("Condition 'if lifecycle.exit.emit_full_state' evaluated to FALSE")
    
    print(f"Configured ExitAgent: emit_full_state = {exit_agent.emit_full_state}")

if __name__ == "__main__":
    check_config()

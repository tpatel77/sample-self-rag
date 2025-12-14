
import sys
import os
from pathlib import Path

# Add project root to path (3 levels up from src/adk_agents/name/agent.py)
# src/adk_agents/name -> src -> root
# This allows importing src.orchestrator
sys.path.append(str(Path(__file__).parents[3]))

from src.orchestrator import WorkflowOrchestrator

# Configured YAML path
YAML_PATH = "/Users/hardipatel/Code/sample-self-rag/workflows/simple_echo.yaml"

orchestrator = WorkflowOrchestrator()
orchestrator.load_workflow(YAML_PATH)
# ADK loader expects 'root_agent' variable
root_agent = orchestrator.root_agent

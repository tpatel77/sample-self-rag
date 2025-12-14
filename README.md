# ADK Workflow Framework

A Python framework for orchestrating custom workflows using Google Agent Development Kit (ADK) with YAML-based configuration.

## Features

- **YAML Configuration**: Define agents and workflows in simple YAML files
- **Multiple Workflow Types**: Support for sequential, parallel, and loop workflows
- **Extensible Tools**: Built-in tools and easy custom tool registration
- **Pydantic Validation**: Type-safe configuration validation
- **Native ADK UI**: Integrated with Google ADK Web UI for visualization (`adk web`).
- **CLI Interface**: Easy command-line execution of workflows

## Installation

```bash
# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Quick Start

### 1. Define a Workflow (YAML)

```yaml
# workflows/my_workflow.yaml
name: code_review_pipeline
description: A pipeline that generates, reviews, and refactors code

defaults:
  model: gemini-2.5-flash

agents:
  - name: code_writer
    type: llm
    instruction: |
      Write Python code based on the user's request.
      Output only the code block.
    output_key: generated_code

  - name: code_reviewer
    type: llm
    instruction: |
      Review this code: {generated_code}
      Provide feedback as a bulleted list.
    output_key: review_comments

workflow:
  type: sequential
  agents:
    - code_writer
    - code_reviewer
```

### 2. Run the Workflow

**CLI:**
```bash
python main.py --workflow workflows/example_sequential.yaml --input "Write a fibonacci function"
```

**Visual UI:**
### Running the UI
To launch the Native ADK Web UI:
```bash
python main.py --ui
```
This will generate wrappers for your YAML workflows and launch the ADK dashboard.

**Python:**
```python
from src import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
orchestrator.load_workflow("workflows/example_sequential.yaml")
result = orchestrator.run("Write a fibonacci function")
print(result)
```

## Workflow Types

### Sequential
Executes agents one after another in order:
```yaml
workflow:
  type: sequential
  agents: [agent1, agent2, agent3]
```

### Parallel
Executes all agents concurrently:
```yaml
workflow:
  type: parallel
  agents: [analyzer1, analyzer2, analyzer3]
```

### Loop
Repeats agents until a condition is met:
```yaml
workflow:
  type: loop
  max_iterations: 5
  agents: [improver, validator]
```

## Agent Types

### LLM Agent
Uses an LLM for reasoning and decision making:
```yaml
- name: my_agent
  type: llm
  instruction: "Your instructions here..."
  tools: [tool1, tool2]  # Optional tools
  output_key: result
```

### Tool Agent
Executes a tool directly without LLM (deterministic):
```yaml
- name: save_file_step
  type: tool
  tool_name: write_file
  arguments:
    file_path: "output.txt"
    content: "{previous_output}"  # Uses {state_key} placeholders
  output_key: save_result
```

### Router Agent
Routes execution based on a Python condition:
```yaml
- name: decision_point
  type: router
  condition: "int({sentiment_score}) > 5"  # Evaluated against state
  routes:
    "True": handle_positive_feedback
    "False": handle_negative_feedback
```

### Sub-Workflow Agent
Executes another workflow YAML file as a step:
```yaml
- name: call_child_workflow
  type: workflow
  path: workflows/child_workflow.yaml
  description: "Processes the data using the child pipeline"
```

### External Agent (RPC/HTTP)
Invokes a remote agent or service via HTTP:
```yaml
- name: call_remote_service
  type: external
  url: "https://api.my-service.com/run"
  method: "POST"
  headers:
    Authorization: "Bearer {API_KEY}"
  output_key: api_response
### A2A Agent (Agent-to-Agent Protocol)
Communicates using a standardized JSON envelope (v1):
```yaml
- name: call_agent_smith
  type: a2a
  url: "https://agent-grid.com/api/v1/message"
  target_agent_id: "agent-smith-007"
  output_key: agent_response
```
Wraps the state in `{"protocol": "a2a/1.0", "target": "...", "payload": ...}`.
This allows you to modularize and reuse workflows.

## Custom Tools

Register custom tools using the decorator:

```python
from src.tools.registry import register_tool

@register_tool("my_custom_tool")
def my_tool(arg1: str) -> str:
    """Description for the LLM."""
    return f"Processed: {arg1}"
```

Reference in YAML:
```yaml
tools:
  - name: my_tool
    module: my_module
    function: my_tool

agents:
  - name: agent_with_tool
    type: llm
    tools: [my_tool]
```

## Environment Setup

Ensure you have your Google API key set:
```bash
export GOOGLE_API_KEY="your-api-key"
```

## Project Structure

```
├── main.py                  # CLI entry point
├── pyproject.toml           # Project configuration
├── src/
│   ├── __init__.py
│   ├── orchestrator.py      # High-level workflow execution
│   ├── config/
│   │   ├── __init__.py
│   │   └── schema.py        # Pydantic models for YAML validation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent_factory.py # Creates ADK agents from config
│   │   └── workflow_builder.py # Builds workflows from YAML
│   └── tools/
│       ├── __init__.py
│       ├── registry.py      # Tool registration system
│       └── builtin.py       # Built-in tools
└── workflows/
    ├── example_sequential.yaml
    ├── example_parallel.yaml
    └── example_loop.yaml
```

## License

MIT
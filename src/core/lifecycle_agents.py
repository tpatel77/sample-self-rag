"""Standard lifecycle agents for workflow execution."""

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

class StartAgent(BaseAgent):
    """
    Standard agent that runs at the beginning of every workflow.
    Responsible for initialization tasks and logging start events.
    """
    
    def __init__(self, name: str = "workflow_start"):
        super().__init__(name=name, description="Standard workflow entry point")

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        # Log start
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text="Workflow execution started.")],
            ),
        )

class ExitAgent(BaseAgent):
    """
    Standard agent that runs at the end of every workflow.
    Responsible for cleanup and logging completion events.
    """
    
    def __init__(self, name: str = "workflow_exit"):
        super().__init__(name=name, description="Standard workflow exit point")

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        # Log exit
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text="Workflow execution completed.")],
            ),
        )

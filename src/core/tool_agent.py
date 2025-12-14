"""Custom ToolAgent for direct tool execution in workflows."""

import re
from typing import Any, Callable, AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event, EventActions
from google.genai import types
from pydantic import Field
from src.core.callbacks.registry import CallbackRegistry


class ToolAgent(BaseAgent):
    """
    A custom agent that directly executes a tool without LLM reasoning.
    """
    
    # Pydantic fields for the agent configuration
    tool_func: Callable[..., Any] = Field(..., description="The tool function to execute")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    output_key: str | None = Field(None, description="Key to store result in session state")
    callbacks: Any | None = Field(None, description="Lifecycle callbacks (LifecycleCallbacks object)")
    
    model_config = {"arbitrary_types_allowed": True}
    
    def _resolve_arguments(self, state: dict[str, Any]) -> dict[str, Any]:
        """Resolve argument placeholders using session state."""
        resolved = {}
        
        for key, value in self.arguments.items():
            if isinstance(value, str):
                # Find all {placeholder} patterns and replace with state values
                def replace_placeholder(match: re.Match[str]) -> str:
                    state_key = match.group(1)
                    state_value = state.get(state_key, match.group(0))
                    return str(state_value) if state_value is not None else ""
                
                resolved[key] = re.sub(r'\{(\w+)\}', replace_placeholder, value)
            else:
                resolved[key] = value
        
        return resolved

    async def _run_callbacks(
        self, 
        phase_names: list[str], 
        ctx: InvocationContext, 
        **kwargs
    ) -> EventActions:
        """Execute callbacks and return collected actions (state deltas)."""
        actions = EventActions()
        
        if not phase_names:
            return actions

        # ADK Best Practice: Create a CallbackContext that wraps the current context
        # This allows callbacks to modify state/artifacts via the context object
        cb_ctx = CallbackContext(ctx, event_actions=actions)
        
        for name in phase_names:
            func = CallbackRegistry.get(name)
            if func:
                try:
                    # Pass context if the callback accepts it
                    # Simple heuristic: try passing context, fallback if fails?
                    # Or assume all registered callbacks MUST accept context if they want persistence?
                    # We'll pass it as a keyword arg 'context'
                    # We also pass 'data' or similar for backward compat
                    if 'context' in func.__code__.co_varnames or 'kwargs' in func.__code__.co_varnames:
                        result = func(context=cb_ctx, **kwargs)
                    else:
                        # Fallback for old logging callbacks
                        result = func(**kwargs)
                        
                    if result and isinstance(result, EventActions):
                        # Merge actions if returned directly (advanced usage)
                        # But typically modifications happen on cb_ctx
                        pass 
                except Exception as e:
                    print(f"Error in callback '{name}': {e}")
                    
        return actions

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        """Execute the tool and yield the result as an event."""
        # Get current state
        state = dict(ctx.session.state) if ctx.session else {}
        
        # 1. Run on_tool_start Callbacks
        start_actions = EventActions()
        if self.callbacks and self.callbacks.on_tool_start:
            start_actions = await self._run_callbacks(self.callbacks.on_tool_start, ctx, tool_name=self.name)
            # If start callbacks modified state, we should ideally emit an event or merge it.
            # We'll merge it into the final event for simplicity (batching state updates),
            # OR emit a separate event if we want distinct history entries. 
            # For ADK compliance, usually 1 invocation = 1 main event.
        
        # Resolve arguments with state values (potentially updated by callbacks?)
        # If callbacks updated state, ctx.session.state might be updated in memory by CallbackContext?
        # CallbackContext updates 'event_actions.state_delta' AND 'invocation_context.session.state' if implemented recursively?
        # Check CallbackContext impl: `self._state = State(..., delta=...)`. It doesn't write back to session immediately.
        # But we want arguments to reflect callback updates? 
        # For now, simplistic approach: arguments resolved from original state.
        
        resolved_args = self._resolve_arguments(state)
        
        # Execute the tool
        try:
            import asyncio
            if asyncio.iscoroutinefunction(self.tool_func):
                result = await self.tool_func(**resolved_args)
            else:
                result = self.tool_func(**resolved_args)
            result_str = str(result) if result is not None else ""
        except Exception as e:
            result_str = f"Tool execution error: {str(e)}"
        
        # 2. Run on_tool_finish Callbacks
        finish_actions = EventActions()
        if self.callbacks and self.callbacks.on_tool_finish:
            finish_actions = await self._run_callbacks(
                self.callbacks.on_tool_finish, 
                ctx, 
                tool_name=self.name, 
                result=result_str
            )
        
        # Prepare event content
        content = types.Content(
            role="model",
            parts=[types.Part(text=result_str)],
        )
        
        # Prepare final actions: output_key delta + callback deltas
        final_actions = EventActions()
        
        # Merge callback deltas
        if start_actions.state_delta:
            if final_actions.state_delta is None: final_actions.state_delta = {}
            final_actions.state_delta.update(start_actions.state_delta)
            
        if finish_actions.state_delta:
            if final_actions.state_delta is None: final_actions.state_delta = {}
            final_actions.state_delta.update(finish_actions.state_delta)

        # Merge output_key delta
        if self.output_key:
            if ctx.session:
                ctx.session.state[self.output_key] = result_str
            
            if final_actions.state_delta is None: final_actions.state_delta = {}
            final_actions.state_delta[self.output_key] = result_str
        
        # Yield the result as an event
        yield Event(
            author=self.name,
            content=content,
            actions=final_actions
        )

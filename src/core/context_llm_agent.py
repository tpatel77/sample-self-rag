"""
Context-aware LlmAgent that supports hooks and callbacks.
"""

from typing import AsyncGenerator, Any
from pydantic import Field

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.events.event_actions import EventActions as AdkEventActions
from google.adk.agents.callback_context import CallbackContext

from src.config.schema import AgentContextConfig
from src.core.callbacks.registry import CallbackRegistry

class ContextAwareLlmAgent(LlmAgent):
    """
    Subclass of LlmAgent that adds support for context hooks and callbacks.
    Inheritance is required to pass ADK's strict type checks.
    """
    
    agent_context_config: AgentContextConfig | None = Field(None, description="Context configuration")
    
    def __init__(
        self,
        *args,
        context_config: AgentContextConfig = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.agent_context_config = context_config
        
    def _sync_state_to_session(self, ctx: InvocationContext):
        """Sync relevant state from Config to Session."""
        if not ctx.session or not self.agent_context_config:
            return
            
        # Push initial configuration to session state
        if self.agent_context_config.initial:
             for k, v in self.agent_context_config.initial.items():
                 if k not in ctx.session.state:
                     ctx.session.state[k] = v
                 
    def _execute_hook(self, hook, ctx: InvocationContext):
        """Execute a context hook."""
        if not hook or not hook.set:
            return
        
        for key, value in hook.set.items():
            if ctx.session:
                 ctx.session.state[key] = value

    async def _execute_callbacks(self, callback_names: list[str], ctx: InvocationContext, event_type: str) -> AdkEventActions:
        """Execute callbacks and return actions."""
        actions = AdkEventActions()
        cb_ctx = CallbackContext(ctx, event_actions=actions)
        
        for name in callback_names:
            func = CallbackRegistry.get(name)
            if func:
                try:
                    if 'context' in func.__code__.co_varnames or 'kwargs' in func.__code__.co_varnames:
                        func(context=cb_ctx, event_type=event_type, agent_name=self.name)
                    else:
                        func(event_type=event_type, data=(self.name,))
                except Exception as e:
                    print(f"Error in callback '{name}': {e}")
        return actions

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        
        if not self.agent_context_config:
            async for event in super()._run_async_impl(ctx):
                yield event
            return
        
        # Sync Initial State
        self._sync_state_to_session(ctx)
        
        # Pre-execution Hook
        if self.agent_context_config.pre_hook:
            self._execute_hook(self.agent_context_config.pre_hook, ctx)
            
        # Agent Start Callback
        if self.agent_context_config.callbacks and self.agent_context_config.callbacks.on_agent_start:
            from google.adk.events import Event
            from google.genai import types
            
            actions = await self._execute_callbacks(self.agent_context_config.callbacks.on_agent_start, ctx, "agent_start")
            
            if actions.state_delta or actions.artifact_delta:
                 yield Event(
                     author=self.name,
                     content=types.Content(role="model", parts=[types.Part(text="")]),
                     actions=actions
                 )
            
        # Run inner logic (Standard LlmAgent execution)
        try:
            async for event in super()._run_async_impl(ctx):
                yield event
        finally:
             # Agent Finish Callback
             if self.agent_context_config.callbacks and self.agent_context_config.callbacks.on_agent_finish:
                from google.adk.events import Event
                from google.genai import types
                
                actions = await self._execute_callbacks(self.agent_context_config.callbacks.on_agent_finish, ctx, "agent_finish")
                
                if actions.state_delta or actions.artifact_delta:
                     yield Event(
                         author=self.name,
                         content=types.Content(role="model", parts=[types.Part(text="")]),
                         actions=actions
                     )

        # Post-execution Hook
        if self.agent_context_config.post_hook:
            self._execute_hook(self.agent_context_config.post_hook, ctx)

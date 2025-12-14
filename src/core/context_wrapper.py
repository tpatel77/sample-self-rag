"""
Wrapper agent for applying context hooks.
"""

from typing import AsyncGenerator, Any
from pydantic import Field

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from src.config.schema import AgentContextConfig
from src.core.callbacks.registry import CallbackRegistry

class ContextWrapperAgent(BaseAgent):
    """
    Wraps an internal agent to provide Pre/Post hooks and State Management.
    """
    
    inner_agent: BaseAgent = Field(..., description="The wrapped inner agent")
    config: AgentContextConfig = Field(..., description="Context configuration")
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(
        self, 
        inner_agent: BaseAgent, 
        context_config: AgentContextConfig
    ):
        super().__init__(
            name=inner_agent.name, 
            description=inner_agent.description,
            inner_agent=inner_agent,
            config=context_config
        )
        
        # Initialize initial state if defined
        # Note: We cannot easily set session state here as we don't have the session yet.
        # We rely on _sync_state_to_session called at runtime.
    
    def _sync_state_to_session(self, ctx: InvocationContext):
        """Sync relevant state from Config to Session."""
        if not ctx.session:
            return
            
        # Push initial configuration to session state
        if self.config.initial:
             for k, v in self.config.initial.items():
                 # Only set if not already present? Or overwrite? 
                 # Usually initial state implies defaults.
                 if k not in ctx.session.state:
                     ctx.session.state[k] = v
                 
    def _execute_hook(self, hook, ctx: InvocationContext):
        """Execute a context hook."""
        if not hook or not hook.set:
            return
        
        for key, value in hook.set.items():
            # Sync to ADK Session State (Runtime visibility & Persistence)
            if ctx.session:
                 ctx.session.state[key] = value

    async def _execute_callbacks(self, callback_names: list[str], ctx: InvocationContext, event_type: str) -> EventActions:
        """Execute callbacks and return actions."""
        # Similar logic to ToolAgent's _run_callbacks but specific to Agent scope
        from google.adk.agents.callback_context import CallbackContext
        from google.adk.events.event_actions import EventActions
        
        actions = EventActions()
        cb_ctx = CallbackContext(ctx, event_actions=actions)
        
        for name in callback_names:
            func = CallbackRegistry.get(name)
            if func:
                try:
                    if 'context' in func.__code__.co_varnames or 'kwargs' in func.__code__.co_varnames:
                        func(context=cb_ctx, event_type=event_type, agent_name=self.name)
                    else:
                        func(event_type=event_type, agent_name=self.name)
                except Exception as e:
                    print(f"Error in callback '{name}': {e}")
        return actions

    async def _run_async_impl(
        self,
        ctx: InvocationContext,
    ) -> AsyncGenerator[Event, None]:
        
        # Sync Initial State
        self._sync_state_to_session(ctx)
        
        # Pre-execution Hook
        if self.config.pre_hook:
            self._execute_hook(self.config.pre_hook, ctx)
            
        # Custom Callback: Agent Start
        if self.config.callbacks and self.config.callbacks.on_agent_start:
            from google.adk.events import Event
            from google.genai import types
            
            actions = await self._execute_callbacks(self.config.callbacks.on_agent_start, ctx, "agent_start")
            
            # If start callbacks produced persistence actions, emit an event
            if actions.state_delta or actions.artifact_delta:
                 yield Event(
                     author=self.name,
                     content=types.Content(role="model", parts=[types.Part(text="")]), # Empty content for control event
                     actions=actions
                 )
            
        # Run inner agent
        try:
            async for event in self.inner_agent._run_async_impl(ctx):
                yield event
        finally:
             # Custom Callback: Agent Finish
             if self.config.callbacks and self.config.callbacks.on_agent_finish:
                from google.adk.events import Event
                from google.genai import types
                
                actions = await self._execute_callbacks(self.config.callbacks.on_agent_finish, ctx, "agent_finish")
                
                if actions.state_delta or actions.artifact_delta:
                     yield Event(
                         author=self.name,
                         content=types.Content(role="model", parts=[types.Part(text="")]),
                         actions=actions
                     )

        # Post-execution Hook
        if self.config.post_hook:
            self._execute_hook(self.config.post_hook, ctx) 

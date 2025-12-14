"""Workflow orchestrator for executing ADK workflows."""

import asyncio
from pathlib import Path
from typing import Any

from google.adk.agents import BaseAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.core.workflow_builder import WorkflowBuilder
from src.config.schema import WorkflowConfig

# Import built-in tools to ensure they're registered
import src.tools.builtin  # noqa: F401


class WorkflowOrchestrator:
    """
    High-level orchestrator for loading and executing ADK workflows.
    
    Usage:
        orchestrator = WorkflowOrchestrator()
        orchestrator.load_workflow("workflows/my_workflow.yaml")
        result = orchestrator.run("Process this input")
        print(result)
    """
    
    def __init__(self, app_name: str = "adk_workflow"):
        """
        Initialize the orchestrator.
        
        Args:
            app_name: Application name for session management
        """
        self.app_name = app_name
        self.builder = WorkflowBuilder()
        self.root_agent: BaseAgent | None = None
        self.config: WorkflowConfig | None = None
        self._session_service = InMemorySessionService()
        self._runner: Runner | None = None
    
    def load_workflow(self, yaml_path: str | Path) -> "WorkflowOrchestrator":
        """
        Load a workflow from a YAML configuration file.
        
        Args:
            yaml_path: Path to the YAML configuration file
        
        Returns:
            Self for method chaining
        """
        self.root_agent = self.builder.build_from_yaml(yaml_path)
        self.config = self.builder.get_config()
        
        # Initialize Session Service based on Config
        session_backend = "memory"
        conn_str = None
        
        if self.config and self.config.context:
            session_backend = self.config.context.session_storage
            conn_str = self.config.context.connection_string
            
        if session_backend == "redis":
            if not conn_str:
                raise ValueError("connection_string required for Redis session storage")
            from src.services.redis_session import RedisSessionService
            # We assume connection_string is REDIS_URL. 
            # If user wants Write-Through, they might need a way to pass DB URL too.
            # keeping it simple: Redis Only for now unless connection string has separators.
            self._session_service = RedisSessionService(redis_url=conn_str, app_name=self.app_name)
            
        elif session_backend == "database":
            if not conn_str:
                raise ValueError("connection_string required for Database session storage")
            from google.adk.sessions.database_session_service import DatabaseSessionService
            self._session_service = DatabaseSessionService(db_url=conn_str)
            
        else:
            # Default to InMemory
            self._session_service = InMemorySessionService()
        
        # Create the runner
        self._runner = Runner(
            agent=self.root_agent,
            app_name=self.app_name,
            session_service=self._session_service,
        )
        
        return self
    
    async def run_async(
        self,
        user_input: str,
        user_id: str = "default_user",
        session_id: str | None = None,
        initial_state: dict[str, Any] | None = None,
    ) -> str:
        """
        Execute the workflow asynchronously with the given input.
        
        Args:
            user_input: The user's input to process
            user_id: User identifier for session management
            session_id: Optional session ID (creates new if not provided)
            initial_state: Optional dictionary of context variables to inject
        
        Returns:
            The final output from the workflow
        """
        if self._runner is None or self.config is None:
            raise ValueError("No workflow loaded. Call load_workflow() first.")
        
        # Create or get session
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
        
        session = await self._session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        
        if session is None:
            session = await self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            
        # Inject initial state if provided
        if initial_state and self.builder.state_manager:
            for k, v in initial_state.items():
                # We default to 'workflow' scope for run-time injection
                self.builder.state_manager.set(
                    scope="workflow",
                    key=k, 
                    value=v, 
                    session_id=session_id
                )
                # Sync to ADK Session
                if session:
                    session.state[k] = v
                    # Persist for InMemory
                    if hasattr(self._session_service, "sessions") and session.id in self._session_service.sessions:
                        self._session_service.sessions[session.id].state[k] = v
        
        # Create user message
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )
        
        # Run the workflow and collect responses
        final_response = ""
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            # Collect text from agent responses
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text  # Use the last response
        
        return final_response
    
        return final_response

    async def run_stream(
        self,
        user_input: str,
        user_id: str = "default_user",
        session_id: str | None = None,
        initial_state: dict[str, Any] | None = None,
    ):
        """
        Execute the workflow and yield events for streaming/tracing.
        
        Yields:
             ADK Events (start, output, end, etc.)
        """
        if self._runner is None:
             raise ValueError("No workflow loaded")
             
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
            
        session = await self._session_service.get_session(
            app_name=self.app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self._session_service.create_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            
        # Inject initial state if provided
        if initial_state and self.builder.state_manager:
            for k, v in initial_state.items():
                self.builder.state_manager.set(
                    scope="workflow",
                    key=k, 
                    value=v, 
                    session_id=session_id
                )
            
                if session:
                    session.state[k] = v
                    # Persist for InMemory
                    if hasattr(self._session_service, "sessions") and session_id in self._session_service.sessions:
                        self._session_service.sessions[session_id].state[k] = v
            
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=user_input)],
        )
        
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message,
        ):
            yield event

    def run(
        self,
        user_input: str,
        user_id: str = "default_user",
        session_id: str | None = None,
        initial_state: dict[str, Any] | None = None,
    ) -> str:
        """
        Execute the workflow synchronously with the given input.
        
        Args:
            user_input: The user's input to process
            user_id: User identifier for session management
            session_id: Optional session ID
            initial_state: Optional dictionary of context variables to inject
        
        Returns:
            The final output from the workflow
        """
        return asyncio.run(self.run_async(user_input, user_id, session_id, initial_state))
    
    def get_session_state(self, user_id: str = "default_user", session_id: str | None = None) -> dict[str, Any]:
        """
        Get the current session state.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        
        Returns:
            The session state dictionary
        """
        if self.config is None:
            return {}
        
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())
        
        async def _get_state() -> dict[str, Any]:
            session = await self._session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            return dict(session.state) if session else {}
        
        return asyncio.run(_get_state())
    
    def get_root_agent(self) -> BaseAgent | None:
        """Get the root agent for ADK tools compatibility."""
        return self.root_agent

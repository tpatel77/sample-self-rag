"""Agent factory for creating ADK agents from configuration."""

from typing import Any

from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent, ParallelAgent, BaseAgent

from src.config.schema import AgentConfig, WorkflowConfig
from src.config.schema import AgentConfig, WorkflowConfig
from src.core.tool_agent import ToolAgent
from src.core.router_agent import RouterAgent
from src.core.external_agent import ExternalAgent
from src.core.a2a_agent import A2AAgent


class AgentFactory:
    """Factory class for creating ADK agents from configuration."""
    
    def __init__(self, config: WorkflowConfig, tools: dict[str, Any] | None = None):
        """
        Initialize the agent factory.
        
        Args:
            config: The workflow configuration
            tools: Dictionary of available tools
        """
        self.config = config
        self.tools = tools or {}
        self._created_agents: dict[str, BaseAgent] = {}
    
    def create_agent(self, agent_config: AgentConfig) -> BaseAgent:
        """
        Create an agent based on its configuration.
        
        Args:
            agent_config: Configuration for the agent
        
        Returns:
            The created ADK agent
        """
        # Check if already created (for reuse in sub-agents)
        if agent_config.name in self._created_agents:
            return self._created_agents[agent_config.name]
        
        agent: BaseAgent
        
        if agent_config.type == "llm":
            agent = self._create_llm_agent(agent_config)
        elif agent_config.type == "sequential":
            agent = self._create_sequential_agent(agent_config)
        elif agent_config.type == "parallel":
            agent = self._create_parallel_agent(agent_config)
        elif agent_config.type == "loop":
            agent = self._create_loop_agent(agent_config)
        elif agent_config.type == "tool":
            agent = self._create_tool_agent(agent_config)
        elif agent_config.type == "router":
            agent = self._create_router_agent(agent_config)
        elif agent_config.type == "workflow":
            agent = self._create_sub_workflow_agent(agent_config)
        elif agent_config.type == "external":
            agent = self._create_external_agent(agent_config)
        elif agent_config.type == "a2a":
            agent = self._create_a2a_agent(agent_config)
        else:
            raise ValueError(f"Unknown agent type: {agent_config.type}")
            
        # Apply Callbacks (Tool and Model level)
        if agent_config.context and agent_config.context.callbacks:
            cbs = agent_config.context.callbacks
            
            # Wrap Tools (if any exist on the agent)
            # ADK agents (BaseAgent) store tools in different ways or not at all (e.g. Sequential).
            # LlmAgent stores them in self.tools.
            if hasattr(agent, "tools") and agent.tools and (cbs.on_tool_start or cbs.on_tool_finish):
                pass 
                
        # Apply context wrapper (Agent level)
        if agent_config.context:
            from src.core.context_wrapper import ContextWrapperAgent
            agent = ContextWrapperAgent(agent, agent_config.context)
            
        self._created_agents[agent_config.name] = agent
        return agent
    
    def _create_llm_agent(self, agent_config: AgentConfig) -> LlmAgent:
        """Create an LLM agent."""
        # Get model from agent config or use default
        model_name = agent_config.model or self.config.defaults.model
        
        # Wrap Model if callbacks present
        # Note: 'model' arg in LlmAgent can be a string (name) or Model object.
        # If we want to wrap, we must instantiate the Model object first.
        # ADK usually handles string->Model resolution internally.
        # We need to access the ModelRegistry or similar if we want to wrap it.
        # Or, LlmAgent takes model_client?
        
        # Simpler approach: LlmAgent takes `model` which is usually a string.
        # If we pass a string, ADK creates the model. We can't wrap it easily unless we subclass LlmAgent.
        # Limitations of ADK wrapping?
        
        # BUT, standard Model object from google.adk.model can be passed.
        # Let's assume we can create it.
        from google.adk.models import Gemini
        model_obj = Gemini(model=model_name)
        
        if agent_config.context and agent_config.context.callbacks:
            cbs = agent_config.context.callbacks
            if cbs.on_model_start or cbs.on_model_finish:
                model_obj = CallbackModelWrapper(model_obj, cbs.on_model_start, cbs.on_model_finish)

        # Collect tools for this agent
        agent_tools = []
        for tool_name in agent_config.tools:
            if tool_name in self.tools:
                tool_func = self.tools[tool_name]
                
                # Wrap Tool if callbacks present
                if agent_config.context and agent_config.context.callbacks:
                    cbs = agent_config.context.callbacks
                    if cbs.on_tool_start or cbs.on_tool_finish:
                        # We wrap the function before strict ADK Tool conversion
                        # Note: self.tools contains raw functions or ADK Tools?
                        # Usually raw functions in this factory layout.
                        tool_func = CallbackToolWrapper(
                            tool_func, tool_name, cbs.on_tool_start, cbs.on_tool_finish
                        )
                
                agent_tools.append(tool_func)
        
        return LlmAgent(
            name=agent_config.name,
            model=model_obj, # Pass wrapped object or string
            instruction=agent_config.instruction or "",
            description=agent_config.description or "",
            output_key=agent_config.output_key,
            tools=agent_tools,  
        )
    
    def _create_sequential_agent(self, agent_config: AgentConfig) -> SequentialAgent:
        """Create a sequential workflow agent."""
        sub_agents = self._create_sub_agents(agent_config.sub_agents)
        
        return SequentialAgent(
            name=agent_config.name,
            sub_agents=sub_agents,
            description=agent_config.description or "",
        )
    
    def _create_parallel_agent(self, agent_config: AgentConfig) -> ParallelAgent:
        """Create a parallel workflow agent."""
        sub_agents = self._create_sub_agents(agent_config.sub_agents)
        
        return ParallelAgent(
            name=agent_config.name,
            sub_agents=sub_agents,
            description=agent_config.description or "",
        )
    
    def _create_loop_agent(self, agent_config: AgentConfig) -> LoopAgent:
        """Create a loop workflow agent."""
        sub_agents = self._create_sub_agents(agent_config.sub_agents)
        
        return LoopAgent(
            name=agent_config.name,
            sub_agents=sub_agents,
            description=agent_config.description or "",
            max_iterations=agent_config.max_iterations or 10,
        )
    
        return ToolAgent(
            name=agent_config.name,
            tool_func=tool_func, # We should wrap this too if callbacks exist
            arguments=agent_config.arguments or {},
            output_key=agent_config.output_key,
            description=agent_config.description or "",
        )
        
    def _create_tool_agent(self, agent_config: AgentConfig) -> ToolAgent:
        """Create a tool agent for direct tool execution."""
        if not agent_config.tool_name:
            raise ValueError(f"Tool agent '{agent_config.name}' requires 'tool_name' to be specified")
        
        # Get the tool function
        tool_func = self.tools.get(agent_config.tool_name)
        if tool_func is None:
            raise ValueError(f"Tool not found: {agent_config.tool_name}")
            
        callbacks = None
        if agent_config.context:
            callbacks = agent_config.context.callbacks
        
        return ToolAgent(
            name=agent_config.name,
            tool_func=tool_func,
            arguments=agent_config.arguments or {},
            output_key=agent_config.output_key,
            callbacks=callbacks,
            description=agent_config.description or "",
        )

    def _create_router_agent(self, agent_config: AgentConfig) -> RouterAgent:
        """Create a router agent."""
        if not agent_config.condition:
            raise ValueError(f"Router agent '{agent_config.name}' requires 'condition'")
        if not agent_config.routes:
            raise ValueError(f"Router agent '{agent_config.name}' requires 'routes'")
        
        # We need to resolve the target agents.
        # But wait - if target agents are LATER in the list or not yet created, we have a problem.
        # ADK agents usually wrap instantiated agents.
        # So we must ensure all potential targets are created.
        
        # Strategy:
        # 1. Check if potential targets are already created.
        # 2. If not, create them now.
        
        resolved_routes = {}
        for result_key, agent_name in agent_config.routes.items():
            # Check created
            if agent_name in self._created_agents:
                resolved_routes[result_key] = self._created_agents[agent_name]
            else:
                # Find config and create
                target_config = self.config.get_agent_by_name(agent_name)
                if not target_config:
                    raise ValueError(f"Router target agent not found: {agent_name}")
                
                # Recursive creation (handles if it's already created inside create_agent)
                resolved_routes[result_key] = self.create_agent(target_config)
                
        return RouterAgent(
            name=agent_config.name,
            condition=agent_config.condition,
            routes=resolved_routes,
            description=agent_config.description or "",
        )

    def _create_sub_workflow_agent(self, agent_config: AgentConfig) -> BaseAgent:
        """Create a sub-workflow as an agent."""
        if not agent_config.path:
            raise ValueError(f"Workflow agent '{agent_config.name}' requires 'path'")
            
        # Avoid circular import by importing here
        from src.core.workflow_builder import WorkflowBuilder
        
        # Create a new builder for the sub-workflow
        # We pass the same tool registry to share tools
        # We might want to handle paths relative to the current workflow file?
        # For now, assume relative to cwd or absolute
        
        builder = WorkflowBuilder(tool_registry=None) # Uses global registry by default
        
        # Build the sub-workflow
        try:
            sub_agent = builder.build_from_yaml(agent_config.path)
            # We wrap it or just return it? 
            # The sub_agent is already a BaseAgent (Sequential/Process etc) using the name from YAML.
            # We might want to override the name with the one in this config?
            # ADK agents have names. If we return it as is, it has the sub-workflow's name.
            # But the parent workflow expects 'agent_config.name'.
            # ADK doesn't easily support renaming agents after creation if they are complex.
            # However, for orchestration, the name matters for ID.
            # Let's trust the sub-workflow's internal structure but maybe wrap it?
            # Actually, `sub_agents` lists refer to names. 
            # If I have `- name: sub_flow`, I expect `sub_flow` to be the agent.
            
            # ADK BaseAgent name is readable.
            # We can try to set the name, but internal sub-agents might have refs? 
            # Usually safe to rename the root of a workflow.
            sub_agent.name = agent_config.name 
            
            if agent_config.description:
                sub_agent.description = agent_config.description
                
            return sub_agent
            
        except Exception as e:
            raise RuntimeError(f"Failed to load sub-workflow '{agent_config.path}': {e}")
    
    def _create_external_agent(self, agent_config: AgentConfig) -> ExternalAgent:
        """Create an external agent."""
        if not agent_config.url:
            raise ValueError(f"External agent '{agent_config.name}' requires 'url'")
            
        return ExternalAgent(
            name=agent_config.name,
            url=agent_config.url,
            method=agent_config.method or "POST",
            headers=agent_config.headers or {},
            output_key=agent_config.output_key,
            description=agent_config.description or "",
        )
    
    def _create_a2a_agent(self, agent_config: AgentConfig) -> A2AAgent:
        """Create an A2A agent."""
        if not agent_config.url:
            raise ValueError(f"A2A agent '{agent_config.name}' requires 'url'")
        if not agent_config.target_agent_id:
            raise ValueError(f"A2A agent '{agent_config.name}' requires 'target_agent_id'")
            
        return A2AAgent(
            name=agent_config.name,
            url=agent_config.url,
            target_agent_id=agent_config.target_agent_id,
            output_key=agent_config.output_key,
            description=agent_config.description or "",
        )

    def _create_sub_agents(self, sub_agent_names: list[str]) -> list[BaseAgent]:
        """Create sub-agents from their names."""
        sub_agents = []
        for agent_name in sub_agent_names:
            agent_config = self.config.get_agent_by_name(agent_name)
            if agent_config is None:
                raise ValueError(f"Sub-agent not found: {agent_name}")
            sub_agents.append(self.create_agent(agent_config))
        return sub_agents
    
    def get_created_agents(self) -> dict[str, BaseAgent]:
        """Get all created agents."""
        return self._created_agents.copy()

import logging
from typing import Any

from domain.models.state_model import AgentConfig
from domain.orchestrator.constants.system_prompts import (
    PROMPT_MAP,
    SYSTEM_PROMPT_PLANNER,
    SYSTEM_PROMPT_SUPERVISOR,
)
from domain.orchestrator.nodes.base_node import BaseNode
from domain.orchestrator.nodes.planner_node import PlannerNode
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from domain.orchestrator.nodes.worker_factory import WorkerFactory
from domain.orchestrator.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Inventory of initialized nodes."""
    def __init__(self):
        self._nodes: dict[str, BaseNode] = {}

    def register(self, agent_id: str, node: BaseNode):
        self._nodes[agent_id] = node

    def get_node(self, agent_id: str) -> BaseNode:
        if agent_id not in self._nodes:
            raise ValueError(f"Agent '{agent_id}' is not in the registry.")
        return self._nodes[agent_id]

    def has_node(self, agent_id: str) -> bool:
        return agent_id in self._nodes


def setup_orchestrator(llm_provider: Any, file_system: Any) -> tuple[SupervisorNode, AgentRegistry]:
    # 1. Setup Registry & Tools
    registry = AgentRegistry()
    tools = ToolRegistry()
    
    # 2. Register Tools
    from infrastructure.tools.list_files_tool import ListFilesTool
    from infrastructure.tools.read_file_tool import ReadFileTool
    from infrastructure.tools.write_file_tool import WriteFileTool
    from infrastructure.tools.delete_file_tool import DeleteFileTool
    
    tools.register(ListFilesTool(fs=file_system))
    tools.register(ReadFileTool(fs=file_system))
    tools.register(WriteFileTool(fs=file_system))
    tools.register(DeleteFileTool(fs=file_system))
    
    # 3. Initialize Factory
    factory = WorkerFactory(tool_registry=tools, max_iterations=5)
    
    # 4. Register Supervisor
    super_config = AgentConfig(
        agent_id="supervisor",
        system_prompt=SYSTEM_PROMPT_SUPERVISOR,
        llm_provider=llm_provider,
    )
    supervisor = SupervisorNode(config=super_config, max_iterations=5, tool_registry=tools)
    registry.register("supervisor", supervisor)
    
    # 5. Register Planner
    planner_config = AgentConfig(
        agent_id="planner_agent",
        system_prompt=SYSTEM_PROMPT_PLANNER,
        llm_provider=llm_provider,
    )
    registry.register("planner_agent", factory.create_planner(planner_config))
    # 6. Register Specialists from PROMPT_MAP
    logger.info(f"🚀 Initializing agents: {list(PROMPT_MAP.keys())}")
    for agent_id, system_prompt in PROMPT_MAP.items():
        if agent_id not in registry._nodes:
            config = AgentConfig(
                agent_id=agent_id,
                system_prompt=system_prompt,
                llm_provider=llm_provider,
            )
            # Use factory to build the worker instance
            registry.register(agent_id, factory.create_worker(config))
    logger.info(f"✅ Agents registered: {list(registry._nodes.keys())}")


    return supervisor, registry

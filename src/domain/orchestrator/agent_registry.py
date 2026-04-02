import logging
from typing import Any

from domain.models.state_model import AgentConfig
from domain.orchestrator.constants.system_prompts import (
    PROMPT_MAP,
    SYSTEM_PROMPT_PLANNER,
    SYSTEM_PROMPT_SUPERVISOR,
)
from domain.orchestrator.nodes.base_node import BaseNode
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from domain.orchestrator.nodes.worker_factory import WorkerFactory
from domain.orchestrator.tool_registry import ToolRegistry
from infrastructure.tools.delete_file_tool import DeleteFileTool
from infrastructure.tools.list_files_tool import ListFilesTool
from infrastructure.tools.read_file_tool import ReadFileTool
from infrastructure.tools.write_file_tool import WriteFileTool


class AgentRegistry:
    """
    Inventory of initialized worker nodes.
    Acts as a bridge between the Supervisor's decision and the actual instance.
    """

    def __init__(self):
        self._nodes: dict[str, BaseNode] = {}

    def register(self, name: str, node: BaseNode) -> None:
        """Registers a node instance (e.g., 'planner', 'coder_python')."""
        self._nodes[name.lower()] = node

    def get_node(self, name: str) -> BaseNode:
        """Retrieves a node by its ID for the Orchestrator loop."""
        node = self._nodes.get(name.lower())
        if not node:
            raise ValueError(f"Agent '{name}' is not in the registry.")
        return node


def setup_orchestrator(
    llm_provider: Any, fs_adapter: Any, max_iterations: int = 10
) -> tuple[SupervisorNode, AgentRegistry]:
    """
    Surgically bootstraps the full orchestration system.
    Returns the entry-point Supervisor and the hydrated AgentRegistry.
    """
    # 1. Tooling
    tools = ToolRegistry()
    tools.register(ListFilesTool(fs_adapter))
    tools.register(ReadFileTool(fs_adapter))
    tools.register(WriteFileTool(fs_adapter))
    tools.register(DeleteFileTool(fs_adapter))

    # 2. Factories
    factory = WorkerFactory(tool_registry=tools, max_iterations=max_iterations)
    registry = AgentRegistry()

    # 3. Register Supervisor
    super_config = AgentConfig(
        agent_id="supervisor",
        system_prompt=SYSTEM_PROMPT_SUPERVISOR,
        llm_provider=llm_provider,
    )
    supervisor = SupervisorNode(config=super_config, max_iterations=max_iterations)
    registry.register("supervisor", supervisor)

    # 4. Register Planner
    planner_config = AgentConfig(
        agent_id="planner_agent",
        system_prompt=SYSTEM_PROMPT_PLANNER,
        llm_provider=llm_provider,
        output_format="txt"  # El planner genera Markdown, no JSON
    )
    registry.register("planner_agent", factory.create_planner(planner_config))


    # 5. Register Specialists from PROMPT_MAP
    for agent_id, system_prompt in PROMPT_MAP.items():
        config = AgentConfig(
            agent_id=agent_id,
            system_prompt=system_prompt,
            llm_provider=llm_provider,
        )
        registry.register(agent_id, factory.create_worker(config))

    return supervisor, registry

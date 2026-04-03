from typing import Any

from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.orchestrator.nodes.planner_node import PlannerNode
from domain.orchestrator.tool_registry import ToolRegistry


from domain.orchestrator.nodes.specialist_agents import (
    ClassifierAgent, NamingAgent, AtomicityAgent, SummarizerAgent, TagAgent
)

class WorkerFactory:
    def __init__(self, tool_registry: ToolRegistry | None = None, max_iterations: int = 5) -> None:
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    def create_worker(self, config: Any) -> BaseWorkerNode:
        # Map agent_id to class
        mapping = {
            "classifier_agent": ClassifierAgent,
            "naming_agent": NamingAgent,
            "atomicity_agent": AtomicityAgent,
            "summarizer_agent": SummarizerAgent,
            "tag_agent": TagAgent
        }
        agent_cls = mapping.get(config.agent_id, BaseWorkerNode)
        return agent_cls(
            config=config,
            max_iterations=self.max_iterations,
            tool_registry=self.tool_registry,
        )

    def create_planner(self, config: Any) -> PlannerNode:
        """
        Creates a specialized Planner instance.
        """
        return PlannerNode(
            config=config,
            max_iterations=self.max_iterations,
            tool_registry=self.tool_registry,
        )

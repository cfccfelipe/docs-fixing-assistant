from typing import Any

from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.orchestrator.tool_registry import ToolRegistry


class WorkerFactory:
    """
    Surgical assembly of Specialized Worker Nodes.
    Ensures consistent dependency injection across all specialists.
    """

    def __init__(self, tool_registry: ToolRegistry, max_iterations: int):
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    def create_worker(self, config: Any) -> BaseWorkerNode:
        """
        Creates a new worker instance.
        The specialization comes from the provided config (system prompt).
        """
        return BaseWorkerNode(
            config=config,
            max_iterations=self.max_iterations,
            tool_registry=self.tool_registry,
        )

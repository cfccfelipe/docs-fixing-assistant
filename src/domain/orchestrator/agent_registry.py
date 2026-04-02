import logging

from domain.orchestrator.nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


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
        logger.debug(f"Node registered in registry: {name}")

    def get_node(self, name: str) -> BaseNode:
        """Retrieves a node by its ID for the Orchestrator loop."""
        node = self._nodes.get(name.lower())
        if not node:
            logger.error(f"Routing error: Agent '{name}' not found.")
            raise ValueError(f"Agent '{name}' is not in the registry.")
        return node

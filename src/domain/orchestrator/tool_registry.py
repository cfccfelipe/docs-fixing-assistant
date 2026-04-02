import logging
from typing import Any

from domain.models.tool_model import ToolDefinition
from domain.ports.tool_port import ITool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry of available tools for agents.
    Acts as a bridge between the LLM's intent and actual implementation.
    """

    def __init__(self):
        self._tools: dict[str, ITool] = {}

    def register(self, tool: ITool) -> None:
        """Adds a tool to the registry using its metadata name."""
        self._tools[tool.metadata.name] = tool
        logger.debug(f"Tool '{tool.metadata.name}' registered successfully.")

    def get_all_metadata(self) -> list[ToolDefinition]:
        """Returns the list of all tool definitions for the LLM Provider."""
        return [tool.metadata for tool in self._tools.values()]

    def execute(self, name: str, **kwargs) -> Any:
        """
        Surgically executes a tool by name.
        Uses the __call__ pattern we defined in ITool.
        """
        tool = self._tools.get(name)
        if not tool:
            logger.error(f"Tool execution failed: '{name}' not found.")
            raise ValueError(f"Tool '{name}' is not registered.")

        return tool(**kwargs)

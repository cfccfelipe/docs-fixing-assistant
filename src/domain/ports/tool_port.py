from typing import Any, Protocol, runtime_checkable

from domain.models.tool_model import ToolDefinition


@runtime_checkable
class ITool(Protocol):
    """
    Protocol for any tool the LLM can invoke.
    Standardizes the bridge between Agent intent and Infrastructure execution.
    """

    @property
    def metadata(self) -> ToolDefinition:
        """
        Returns the formal ToolDefinition model.
        The source of truth for the LLM Provider.
        """
        ...

    def __call__(self, **kwargs) -> Any:
        """
        Logic execution for the tool.
        Allows the tool instance to be treated as a function.
        """
        ...

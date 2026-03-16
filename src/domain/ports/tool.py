from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ITool(Protocol):
    """
    Protocol for any tool the LLM can invoke.
    """

    name: str
    description: str
    parameters: dict[str, Any]

    def execute(self, **kwargs) -> Any:
        """Logic to be executed when the LLM calls the tool."""
        ...

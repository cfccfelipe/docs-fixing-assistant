from dataclasses import asdict, dataclass, field
from typing import Any

from domain.models.enums import ToolType


@dataclass(frozen=True)
class ToolDefinition:
    """
    Universal representation of a tool (Local or MCP).
    'arguments' defines the JSON Schema for the expected parameters.
    """

    name: str
    description: str
    type: ToolType
    server_name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Returns an agnostic dictionary representation of the tool definition."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass(frozen=True)
class ToolCall:
    """
    Surgical representation of a tool invocation.
    The 'id' is required to map the response back to the LLM's request.
    """

    id: str
    name: str
    arguments: dict[str, Any]

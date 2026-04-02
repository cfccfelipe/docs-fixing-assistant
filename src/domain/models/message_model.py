from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID

from domain.models.enums import MessageRole


@dataclass(frozen=True)
class MessageDefinition:
    """
    Formal representation of a conversation message.
    """

    id: UUID
    role: MessageRole
    content_history: str
    tool_history_ids: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Returns an agnostic dictionary representation for state serialization.
        Filters out None values to maintain a clean context window.
        """
        return {k: v for k, v in asdict(self).items() if v is not None}

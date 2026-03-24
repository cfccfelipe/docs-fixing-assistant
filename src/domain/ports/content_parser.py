from typing import Any, Protocol, runtime_checkable

from domain.models.state import AgentState


@runtime_checkable
class ContentParserPort(Protocol):
    """
    Interface for content transformation and normalization nodes.
    Used by infrastructure parsers (e.g., Flashcards, XML, Markdown).
    """

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """
        Processes the state and returns a partial update dictionary.

        Args:
            state: The current source of truth (AgentState).

        Returns:
            A dictionary containing the keys to be updated in the graph
            (e.g., {'content': '...', 'metadata': ...}).
        """
        ...

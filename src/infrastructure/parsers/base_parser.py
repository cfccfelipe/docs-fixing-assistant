import logging
from dataclasses import replace

from domain.models.state import AgentState, StateMetadata
from domain.ports.content_parser import ContentParserPort

logger = logging.getLogger(__name__)


class BaseParser(ContentParserPort):
    """
    Abstract-like Parser.
    Provides normalization tools for specialized parsers.
    """

    def __init__(self, agent_key: str = "base_parser"):
        self.agent_key = agent_key

    def _normalize(self, text: str) -> tuple[str, list[str]]:
        """Logic-only: Trims and validates content."""
        cleaned = (text or "").strip()
        errors = []
        if not cleaned:
            errors.append(f"Critical: Content for {self.agent_key} is empty.")
        return cleaned, errors

    def _build_metadata(self, state: AgentState, detail: str) -> StateMetadata:
        """Helper to create consistent metadata across all parsers."""
        return replace(
            state.metadata,
            agent_key=self.agent_key,
            content_modified=detail,
            model_name="Rule-Based-Parser",
        )

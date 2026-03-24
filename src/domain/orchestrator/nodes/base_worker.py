import logging
from dataclasses import replace
from typing import Any

from domain.models.state import AgentState, StateMetadata
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import OrchestrationException

logger = logging.getLogger(__name__)


class BaseWorker:
    """
    Base class for all graph nodes (Workers, Supervisors, Parsers).
    Provides standardized metadata management and error handling.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def _create_metadata(
        self, state: AgentState, content_info: str = None, additional_tokens: int = 0
    ) -> StateMetadata:
        """
        Standardized metadata factory.
        Ensures immutability, preserves trace_id, and accumulates tokens.
        Matches the StateMetadata dataclass fields exactly.
        """

        # Ensure we always have a base metadata object to work with
        current_md = state.metadata or StateMetadata()

        # CRITICAL: We only use fields that exist in your StateMetadata:
        # last_agent_key, token_usage, trace_id, model_name
        return replace(
            current_md,
            last_agent_key=self.name,  # Corrected from 'agent_key'
            token_usage=(current_md.token_usage or 0) + additional_tokens,
            # If you want to log the 'content_info', we do it via logger
            # unless you add 'content_modified' back to the StateMetadata dataclass.
        )

    @handle_errors(exception_cls=OrchestrationException, layer="Domain")
    async def __call__(self, state: AgentState) -> dict[str, Any]:
        """
        Generic execution method.
        Returns a partial state update (Dict) compatible with LangGraph.
        """
        logger.info(f"Worker [{self.name}] invoked.")

        # Note: We removed 'content_info' argument here to match the
        # StateMetadata dataclass you shared previously.
        return {"metadata": self._create_metadata(state, additional_tokens=0)}

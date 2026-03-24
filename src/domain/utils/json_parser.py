import json
import logging
import re
from typing import Any

from domain.models.state import StopReason
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError

logger = logging.getLogger(__name__)


class JsonParser:
    """
    Universal Utility for robust JSON extraction.
    Designed to work across Domain, Infrastructure, and Nodes.
    """

    @staticmethod
    @handle_errors(exception_cls=ParserError, layer="JsonParserUtility")
    def parse(raw_text: str | Any, fallback: Any = None) -> Any:
        """
        The "All-Purpose" Parser.
        - Removes Markdown fences (```json ... ```).
        - Extracts JSON objects {...} or lists [...] from prose.
        - Returns 'fallback' if extraction is impossible.
        """
        if not raw_text or not isinstance(raw_text, str):
            return fallback

        # 1. Pre-cleaning: Remove whitespace and markdown blocks
        # This handles cases where the LLM wraps the JSON in code fences
        content = raw_text.strip()
        content = re.sub(
            r"^```json\s*|```$", "", content, flags=re.MULTILINE | re.IGNORECASE
        ).strip()

        # 2. Try direct parsing
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 3. Fallback: Search for the JSON block within the text
        match = re.search(r"(\{.*\}|\[.*\])", content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.debug("Regex found a potential JSON block, but it's malformed.")

        return fallback

    @staticmethod
    def to_agent_error(reason: str) -> dict[str, Any]:
        """
        Bridge: Formats a generic parsing failure into the AgentState schema.
        Uses the StopReason Enum for consistency.
        """
        return {
            "stop_reason": StopReason.ERROR,
            "next_agent": None,
            "next_task": None,
            "error_message": reason,
        }

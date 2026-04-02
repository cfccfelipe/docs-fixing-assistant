from enum import Enum


class LLMResponseFormat(Enum):
    """
    Structured output formats supported by LLM providers.
    """

    JSON = "json"
    XML = "xml"
    MARKDOWN = "markdown"
    TEXT = "text"


class MessageRole(Enum):
    """
    Standard roles in an LLM conversation.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolType(Enum):
    """
    Supported tool types, including standard functions and MCP protocols.
    """

    FUNCTION = "function"
    MCP = "mcp"


class StopReason(Enum):
    """
    Standardized exit codes for Orchestrator nodes.
    Using str mixin for JSON serializability.
    """

    CALL = "CALL"
    ERROR = "ERROR"
    END = "END"

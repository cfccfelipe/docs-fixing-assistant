from dataclasses import dataclass, field
from functools import cached_property
from typing import Any

from domain.models.message_model import MessageDefinition
from domain.models.tool_model import ToolCall, ToolDefinition


@dataclass(frozen=True)
class LLMInferenceConfig:
    """
    Pure Domain Model for inference parameters.
    Agnostic of the underlying provider (Ollama, OpenAI, etc.).
    """

    temperature: float = 0.0
    stop: list[str] = field(default_factory=list)
    max_tokens: int = 4096
    top_p: float = 0.9
    presence_penalty: float = 0.0
    seed: int = 42

    @cached_property
    def to_dict(self) -> dict[str, Any]:
        """
        Memoized dictionary representation O(1).
        Filters out None values to keep the provider payload lean.
        """
        data: dict[str, Any] = {k: v for k, v in vars(self).items() if v is not None}
        data.pop("to_dict", None)
        return data


@dataclass(frozen=True)
class LLMRequest:
    """
    Unified execution payload for LLM providers.

    Architecture Note for Recruiters:
    We distinguish between Registry (Available) and History (Executed):
    1. 'tools_registry': The active toolkit containing function schemas.
    2. 'messages': The conversation history containing 'tool_history' logs.
    """

    messages: list[MessageDefinition]
    inference: LLMInferenceConfig | None = None

    tools_registry: list[ToolDefinition] | None = field(
        default=None,
        metadata={"help": "Available function schemas for the current turn"},
    )


@dataclass(frozen=True)
class LLMResponse:
    """
    Standardized DTO for LLM outputs.
    Optimized for state serialization and performance tracking.
    """

    content: str

    tool_calls: list[ToolCall] = field(default_factory=list)

    # Token Metadata
    token_usage: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    # Performance Metadata (in milliseconds)
    total_duration_ms: float | None = None
    load_duration_ms: float | None = None
    prompt_eval_duration_ms: float | None = None
    eval_duration_ms: float | None = None

    model: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        """
        Converts the response to a dictionary for state updates or logging.
        Uses a filtering comprehension O(N) to ensure clean context windows.
        """
        data: dict[str, Any] = {k: v for k, v in vars(self).items() if v is not None}

        return data


@dataclass(frozen=True)
class BaseLLMConfig:
    """Base configuration for any LLM connection."""

    model_id: str
    inference: LLMInferenceConfig = field(default_factory=LLMInferenceConfig)


@dataclass(frozen=True)
class OllamaConfig(BaseLLMConfig):
    """Specific configuration for local Ollama infrastructure."""

    host: str = "http://localhost:11434"
    timeout: int = 60

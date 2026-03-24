from dataclasses import dataclass, field
from typing import Any, Literal

from domain.ports.llm_provider import LLMProviderPort


@dataclass(frozen=True)
class AgentConfig:
    """
    Configuration DTO for specific agents.
    Encapsulates prompts, LLM settings, and tool definitions (MCP).
    """

    agent_id: str
    system_prompt: str
    llm_provider: LLMProviderPort

    examples: list[dict[str, str]] = field(default_factory=list)

    temperature: float = 0.0
    max_tokens: int = 2500
    stop_sequences: list[str] = field(default_factory=lambda: ["</document>", "###"])

    content_threshold: int = 30000
    output_format: Literal["xml", "json", "text"] = "xml"
    max_retries: int = 2

    metadata: dict[str, Any] = field(default_factory=dict)

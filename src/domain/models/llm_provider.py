from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMInferenceConfig:
    """Pure inference parameters used by the model engine."""

    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9

    def to_dict(self) -> dict[str, Any]:
        """Utility to pass directly to providers like ollama.chat(options=...)"""
        return {
            "temperature": self.temperature,
            "num_predict": self.max_tokens,
            "top_p": self.top_p,
        }


@dataclass(frozen=True)
class BaseLLMConfig:
    """Base settings for any LLM connection."""

    model_id: str
    inference: LLMInferenceConfig = field(default_factory=LLMInferenceConfig)


@dataclass(frozen=True)
class OllamaConfig(BaseLLMConfig):
    """Specific connection settings for local Ollama."""

    host: str = "http://localhost:11434"
    timeout: int = 60


@dataclass(frozen=True)
class OpenAIConfig(BaseLLMConfig):
    """Specific connection settings for Cloud OpenAI."""

    api_key: str = ""  # Should be loaded from .env
    organization_id: str | None = None

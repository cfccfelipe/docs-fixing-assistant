from pydantic import AnyHttpUrl, Field, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

from domain.models.llm_provider import LLMInferenceConfig


class OllamaConfig(BaseSettings):
    """Specific settings for Ollama infrastructure."""

    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_", env_file=".env", extra="ignore"
    )

    base_url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:11434")
    )
    model_name: str = Field(default="llama3.1:latest")
    timeout: int = Field(default=120)

    # Defaults para el .env
    temperature: float = Field(default=0.0)
    top_p: float = Field(default=0.7)
    num_predict: int = Field(default=15000)

    @property
    def host(self) -> str:
        return str(self.base_url)

    @property
    def inference(self) -> LLMInferenceConfig:
        """Bridge to Domain Model."""
        return LLMInferenceConfig(
            temperature=self.temperature, max_tokens=self.num_predict, top_p=self.top_p
        )

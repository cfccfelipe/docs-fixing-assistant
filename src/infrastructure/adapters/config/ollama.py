from pydantic import AnyHttpUrl, Field, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaConfig(BaseSettings):
    """
    Configuration for the Ollama adapter using Pydantic v2.
    Loads values from environment variables prefixed with OLLAMA_.
    """

    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_", env_file=".env", extra="ignore"
    )

    base_url: AnyHttpUrl = Field(
        default=TypeAdapter(AnyHttpUrl).validate_python("http://localhost:11434")
    )
    model_name: str = Field(default="llama3.1:latest")
    timeout: int = Field(default=120)

    temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    top_p: float = Field(default=0.7, ge=0.0, le=1.0)
    num_predict: int = Field(default=15000, ge=1, le=15000)

    @property
    def host(self) -> str:
        return str(self.base_url)

    @property
    def options(self) -> dict:  # 🚨 Cambiado de inference_options a options
        """
        Returns a dictionary of inference parameters compatible
        with the Ollama Python SDK options.
        """
        return {
            "temperature": self.temperature,
            "num_predict": self.num_predict,
            "top_p": self.top_p,
        }

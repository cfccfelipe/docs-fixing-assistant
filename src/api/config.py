"""
Centralized configuration settings.
Uses Composition to group infrastructure-specific configs.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from infrastructure.adapters.config.ollama import OllamaConfig


class Settings(BaseSettings):
    """
    Application settings and environment variables.
    The single source of truth for the entire system.
    """

    # Server Configuration
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Project Metadata
    PROJECT_NAME: str = "Docs Fixing Assistant"
    VERSION: str = "1.0.0"

    ollama: OllamaConfig = OllamaConfig()

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

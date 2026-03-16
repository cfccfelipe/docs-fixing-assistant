"""
Error Schemas: Pydantic models for standardized API error responses.
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Standardized error response for the entire API.
    Ensures consistency between Domain, Infrastructure, and API layers.
    """

    error_code: str = Field(
        ...,
        description="Unique internal application error code",
        examples=["LLM_CONNECTION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable error description",
        examples=["No se pudo conectar con el servicio de Ollama"],
    )
    details: list[dict[str, Any]] | dict[str, Any] | None = Field(
        default=None,
        description="Additional context, validation errors, or technical metadata",
    )

    class Config:
        """Config to ensure compatibility and clean serialization."""

        populate_by_name = True
        extra = "ignore"

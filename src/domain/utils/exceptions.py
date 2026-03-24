# domain/utils/exceptions.py
from typing import Any

from domain.constants.errors import (
    ERR_CODE_AGENT_FAILURE,
    ERR_CODE_FILE_SYSTEM,
    ERR_CODE_LLM_CONNECTION,
    ERR_CODE_ORCHESTRATION_ERROR,
    ERR_CODE_PARSER_FAILURE,
    ERR_CODE_VALIDATION,
    MSG_AGENT_ERROR,
    MSG_FILE_SYSTEM,
    MSG_LLM_CONNECTION,
    MSG_ORCHESTRATION_ERROR,
    MSG_PARSER_FAILURE,
    MSG_VALIDATION_ERROR,
)
from domain.models.error import Error


class BaseException(Exception):
    def __init__(self, error: Error, overrides: dict | list | None = None):
        self.error_code: str = error.error_code
        self.status_code: int = error.status_code
        self.message: str = error.message
        self.details: dict | list | Any = overrides if overrides is not None else {}
        super().__init__(self.message)

    def __str__(self):
        """
        Returns a formatted error message including technical details if present.
        """
        base_msg = self.message

        if isinstance(self.details, dict) and "message" in self.details:
            return f"{base_msg} | Details: {self.details['message']}"

        if isinstance(self.details, list) and self.details:
            return f"{base_msg} | Details: {str(self.details)}"

        return base_msg


class ValidationException(BaseException):
    """Raised when the input data fails domain validation rules."""

    def __init__(self, overrides: list | dict | None = None):
        super().__init__(
            error=Error(
                status_code=422,
                error_code=ERR_CODE_VALIDATION,
                message=MSG_VALIDATION_ERROR,
            ),
            overrides=overrides,
        )


class FileSystemException(BaseException):
    """Raised when a file operation fails in infrastructure."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=400,
                error_code=ERR_CODE_FILE_SYSTEM,
                message=MSG_FILE_SYSTEM,
            ),
            overrides=overrides,
        )


class LLMConnectionException(BaseException):
    """Raised when the LLM provider (e.g., Ollama/AWS) is unreachable."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=503,
                error_code=ERR_CODE_LLM_CONNECTION,
                message=MSG_LLM_CONNECTION,
            ),
            overrides=overrides,
        )


class AgentException(BaseException):
    """Base exception for errors occurring within any AgentPort implementation."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=500,
                error_code=ERR_CODE_AGENT_FAILURE,
                message=MSG_AGENT_ERROR,
            ),
            overrides=overrides,
        )


class OrchestrationException(BaseException):
    """Specifically for failures in the OrchestratorAgent logic or flow."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=500,
                error_code=ERR_CODE_ORCHESTRATION_ERROR,
                message=MSG_ORCHESTRATION_ERROR,
            ),
            overrides=overrides,
        )


class InfrastructureException(BaseException):
    """Specifically for failures in external providers like Ollama or File System."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=503,
                error_code=ERR_CODE_LLM_CONNECTION,
                message=MSG_LLM_CONNECTION,
            ),
            overrides=overrides,
        )


class ParserError(BaseException):
    """Excepción de dominio para errores en parsers de contenido."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=500,
                error_code=ERR_CODE_PARSER_FAILURE,
                message=MSG_PARSER_FAILURE,
            ),
            overrides=overrides,
        )

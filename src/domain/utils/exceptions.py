from domain.constants.errors import (
    ERR_CODE_FILE_SYSTEM,
    ERR_CODE_LLM_CONNECTION,
    ERR_CODE_VALIDATION,
    MSG_FILE_SYSTEM,
    MSG_LLM_CONNECTION,
    MSG_VALIDATION_ERROR,
)
from domain.models.error import Error


class BaseException(Exception):
    def __init__(self, error: Error, overrides: dict | list | None = None):
        self.error_code: str = error.error_code
        self.status_code: int = error.status_code
        self.message: str = error.message
        self.details: dict | list | None = overrides if overrides is not None else {}
        super().__init__(self.message)

    def __str__(self):
        """
        Error message + override
        """
        base_msg = self.message

        if isinstance(self.details, dict) and "message" in self.details:
            return f"{base_msg} | Details: {self.details['message']}"

        if isinstance(self.details, list) and self.details:
            return f"{base_msg} | Details: {str(self.details)}"

        return base_msg


class ValidationException(BaseException):
    """Raised when the LLM provider is unreachable."""

    def __init__(self, overrides: list | None = None):
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
    """Raised when the LLM provider is unreachable."""

    def __init__(self, overrides: dict | None = None):
        super().__init__(
            error=Error(
                status_code=503,
                error_code=ERR_CODE_LLM_CONNECTION,
                message=MSG_LLM_CONNECTION,
            ),
            overrides=overrides,
        )

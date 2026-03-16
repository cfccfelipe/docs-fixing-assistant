"""
Error Handlers: Centralized exception management and HTTP response normalization.
"""

import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.schemas.error_schemas import ErrorResponse
from domain.utils.exceptions import BaseException, ValidationException

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Registers exception handlers to the FastAPI application instance."""

    @app.exception_handler(BaseException)
    async def app_exception_handler(request: Request, exc: BaseException):
        """Generic mapper for any AppException."""

        content = ErrorResponse(
            error_code=exc.error_code, message=exc.message, details=exc.details
        )

        return JSONResponse(
            status_code=exc.status_code, content=content.model_dump(exclude_none=True)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Normalizes Pydantic errors and mimics decorator logging behavior."""
        sanitized_details = [
            {
                **error,
                "ctx": {
                    k: (str(v) if isinstance(v, Exception) else v)
                    for k, v in error.get("ctx", {}).items()
                },
            }
            if "ctx" in error
            else error
            for error in exc.errors()
        ]

        logger.error(
            f"Validation Error at {request.url.path}",
            extra={
                "extra": {
                    "function": "fastapi_validation",
                    "details": sanitized_details,
                }
            },
        )

        return await app_exception_handler(
            request, ValidationException(overrides=sanitized_details)
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handles standard FastAPI/Starlette HTTPExceptions."""
        content = (
            exc.detail
            if isinstance(exc.detail, dict) and "error_code" in exc.detail
            else ErrorResponse(
                error_code="HTTP_ERROR", message=str(exc.detail)
            ).model_dump(exclude_none=True)
        )

        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Final safety net for unhandled errors to prevent leaking stack traces."""
        logger.critical(f"Unhandled Exception: {str(exc)}\n{traceback.format_exc()}")

        content = ErrorResponse(
            error_code="INTERNAL_ERROR", message="An unexpected error occurred."
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content.model_dump(exclude_none=True),
        )

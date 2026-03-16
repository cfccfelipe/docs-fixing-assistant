import asyncio
import functools
import logging
from typing import Any, Protocol

from domain.utils.exceptions import BaseException


class ExceptionClass(Protocol):
    def __call__(self, overrides: dict[str, str] | None = None) -> BaseException: ...


def handle_errors(exception_cls: Any, **extra_context: str):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except (exception_cls, asyncio.CancelledError):
                    # Re-lanzamos sin envolver para permitir la cancelación limpia
                    raise
                except Exception as e:
                    _log_and_raise(func, e, exception_cls, extra_context)

            return wrapper
        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except exception_cls:
                    raise
                except Exception as e:
                    _log_and_raise(func, e, exception_cls, extra_context)

            return wrapper

    return decorator


def _log_and_raise(func, e, exception_cls, extra_context):
    logger = logging.getLogger(func.__module__)
    log_data = {
        "function": func.__name__,
        "error_type": type(e).__name__,
        "technical_details": str(e),
        **extra_context,
    }
    logger.error(
        f"Domain Error in {func.__name__}: {str(e)}", extra={"extra": log_data}
    )
    merged_context = {**extra_context, "message": str(e)}
    raise exception_cls(overrides=merged_context) from e

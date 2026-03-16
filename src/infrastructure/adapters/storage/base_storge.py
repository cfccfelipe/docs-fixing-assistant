"""
Base storage utilities for safe resource management.
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import IO, Any, Literal

logger = logging.getLogger(__name__)


class StorageContextMixin:
    """
    Provides a universal context manager for local and remote file operations.
    Intended to be inherited by infrastructure tools (read/write/storage).
    """

    def _validate_path(self, path: str) -> None:
        """Internal path validation logic to prevent traversal attacks."""
        if ".." in path:
            raise PermissionError("Path traversal attempt detected.")

    @contextmanager
    def safe_access(
        self,
        path: str,
        mode: str,
        storage_type: Literal["local", "remote"] = "local",
    ) -> Generator[IO[Any], None, None]:
        """
        Manages file resources safely based on storage type.
        Ensures path validation, error logging, and proper closing.
        """
        self._validate_path(path)

        resource: IO[Any] | None = None
        try:
            if storage_type == "local":
                # Only apply encoding for text modes
                if "b" in mode:
                    resource = open(path, mode)  # returns IO[bytes]
                else:
                    resource = open(path, mode, encoding="utf-8")  # returns IO[str]
                logger.debug(f"Opened local resource at {path} with mode={mode}")
                yield resource
            elif storage_type == "remote":
                raise NotImplementedError("Remote storage (S3) integration pending.")
        except Exception as e:
            logger.error(
                f"Storage error at {path} ({storage_type}, mode={mode}): {str(e)}"
            )
            raise
        finally:
            if resource and hasattr(resource, "close"):
                resource.close()
                logger.debug(f"Closed resource at {path}")

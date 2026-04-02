import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any

logger = logging.getLogger(__name__)


class StorageContextMixin:
    """Security layer: Prevents path traversal and manages file handles."""

    def _validate_path(self, path: str | Path) -> Path:
        """Enforces path safety."""
        str_path = str(path)
        if ".." in str_path:
            logger.warning(f"Traversal attempt blocked: {str_path}")
            raise PermissionError("Path traversal attempt detected.")
        return Path(path)

    @contextmanager
    def safe_access(self, path: Path, mode: str) -> Generator[IO[Any], None, None]:
        """Context manager for leak-proof file operations."""
        resource: IO[Any] | None = None
        try:
            if "w" in mode or "a" in mode:
                path.parent.mkdir(parents=True, exist_ok=True)

            encoding = None if "b" in mode else "utf-8"
            resource = open(path, mode, encoding=encoding)
            yield resource
        finally:
            if resource and not resource.closed:
                resource.close()

    def _safe_delete(self, path: Path) -> bool:
        if path.exists() and path.is_file():
            os.remove(path)
            return True
        return False

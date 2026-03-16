"""
Infrastructure implementation of file system tools with decorated error handling.
Supports streaming for high-volume data consolidation and generic file listing.
"""

import logging
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from domain.ports.file_system import FileSystemPort
from domain.ports.tool import ITool
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import FileSystemException
from infrastructure.adapters.storage.base_storge import StorageContextMixin

logger = logging.getLogger(__name__)


class LocalFileSystemAdapter(StorageContextMixin, ITool, FileSystemPort):
    """
    Unified adapter for file system operations.
    Implements FileSystemPort for domain services and ITool for agent usage.
    """

    name = "local_fs_adapter"
    description = "Handles local disk I/O operations including streaming and generic directory listing."

    def __init__(self, base_dir: str = "./output"):
        # Directorio seguro de salida por defecto
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe_path(self, path: str) -> Path:
        """
        Normaliza y valida que la ruta esté dentro del directorio seguro.
        Se usa solo para listados, no para lectura/escritura flexible.
        """
        candidate = Path(path).resolve()
        if not str(candidate).startswith(str(self.base_dir)):
            raise PermissionError("Path traversal attempt detected.")
        return candidate

    # --- Métodos del Puerto (Domain Usage) ---

    @handle_errors(
        exception_cls=FileSystemException,
        layer="Infrastructure",
        component="LocalFileSystemAdapter",
        operation="read_file",
    )
    def read_file(self, path: str) -> str:
        """
        Lectura flexible: permite rutas absolutas en cualquier parte del sistema.
        """
        safe_path = Path(path).resolve()
        with self.safe_access(str(safe_path), "r", storage_type="local") as f:
            return f.read()

    @handle_errors(
        exception_cls=FileSystemException,
        layer="Infrastructure",
        component="LocalFileSystemAdapter",
        operation="write_file",
    )
    def write_file(self, path: str, content: str | Iterable[str]) -> str:
        """
        Escritura flexible: permite rutas absolutas en cualquier parte del sistema.
        Supports Iterable[str] to enable memory-efficient streaming for large files.
        """
        safe_path = Path(path).resolve()
        safe_path.parent.mkdir(parents=True, exist_ok=True)

        with self.safe_access(str(safe_path), "w", storage_type="local") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                for chunk in content:
                    f.write(chunk)

        return str(safe_path)

    @handle_errors(
        exception_cls=FileSystemException,
        layer="Infrastructure",
        component="LocalFileSystemAdapter",
        operation="list_files",
    )
    def list_files(self, folder_path: str, extension: str = "*") -> list[Path]:
        """
        Generic file listing. Automatically handles extension formatting
        and filters out empty files and previous consolidated results.
        Solo permite listar dentro de base_dir.
        """
        safe_dir = self._resolve_safe_path(folder_path)
        if not safe_dir.exists():
            raise FileSystemException(
                overrides={"message": f"Directory not found: {folder_path}"}
            )

        ext = f".{extension.lstrip('.')}" if extension != "*" else "*"
        pattern = f"*{ext}"

        return [
            f
            for f in safe_dir.rglob(pattern)
            if f.is_file() and f.name != "consolidated.xml" and f.stat().st_size > 0
        ]

    # --- Método Execute (Legacy/Tool Usage) ---

    def execute(self, **kwargs: Any) -> Any:
        """
        ITool compatibility layer.
        Dispatches to the correct method based on parameters.
        """
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path")

        if operation == "read":
            return self.read_file(path)
        elif operation == "write":
            return self.write_file(path, kwargs.get("content", ""))

        raise ValueError(f"Unsupported operation: {operation}")


# Mantener estas clases como alias para compatibilidad si otros servicios las inyectan por separado
class FileReadTool(LocalFileSystemAdapter):
    name = "file_read"


class FileWriteTool(LocalFileSystemAdapter):
    name = "file_write"

from collections.abc import Iterable
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class FileSystemPort(Protocol):
    """
    General purpose File System Port.
    Standardizes I/O operations and directory listing for the entire domain.
    """

    def read_file(self, path: str) -> str:
        """Reads the full content of a file as a string."""
        ...

    def write_file(self, path: str, content: str | Iterable[str]) -> str:
        """
        Writes content to a file. Supports strings for small files
        and Iterables for memory-efficient streaming.
        """
        ...

    def list_files(self, folder_path: str, extension: str = "*") -> list[Path]:
        """
        Lists files in a directory filtering by extension.
        Defaults to all files (*).
        """
        ...

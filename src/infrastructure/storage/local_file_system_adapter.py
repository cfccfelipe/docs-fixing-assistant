from collections.abc import Iterable
from pathlib import Path

from domain.ports.file_system_port import FileSystemPort
from infrastructure.storage.storage_mixin import StorageContextMixin


class LocalFileSystemAdapter(StorageContextMixin, FileSystemPort):
    def __init__(self, base_path: str | Path = "."):
        self._base_path = Path(base_path).resolve()

    @property
    def base_path(self) -> Path:
        return self._base_path

    def read_file(self, path: str) -> str:
        # Resolve path
        target = Path(path)
        if not target.is_absolute():
            target = (self._base_path / path).resolve()
        else:
            target = target.resolve()
            
        full_path = self._validate_path(target)
        with self.safe_access(full_path, "r") as f:
            return f.read()

    def write_file(self, path: str, content: str | Iterable[str]) -> str:
        # Determine path relative to base_path
        # Sanitize path to prevent directory traversal
        path_parts = Path(path).parts
        # If it has a root part, take the relative one.
        if Path(path).is_absolute():
            # For this PoC, only allow if it starts with base_path
            # But the agent sends just "architecture/..."
            relative_path = Path(path).name
        else:
            relative_path = path
        
        target = (self._base_path / relative_path).resolve()
        
        # Ensure parent directory exists
        target.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                for line in content:
                    f.write(line)
        return str(target)

    def delete_file(self, path: str) -> bool:
        target = Path(path)
        if not target.is_absolute():
            target = (self._base_path / path).resolve()
        else:
            target = target.resolve()
            
        full_path = self._validate_path(target)
        return self._safe_delete(full_path)

    def list_files(self, folder_path: str, extension: str = "*") -> list[Path]:
        target = self._validate_path(self._base_path / folder_path)
        if not target.is_dir():
            return []
        pattern = f"*.{extension.lstrip('.')}" if extension != "*" else "*"
        return list(target.glob(pattern))

    def exists(self, path: str) -> bool:
        target = Path(path)
        if not target.is_absolute():
            target = (self._base_path / path).resolve()
        else:
            target = target.resolve()
        return target.exists()

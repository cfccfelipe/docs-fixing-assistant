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
        full_path = self._validate_path(self._base_path / path)
        with self.safe_access(full_path, "r") as f:
            return f.read()

    def write_file(self, path: str, content: str | Iterable[str]) -> str:
        full_path = self._validate_path(self._base_path / path)
        with self.safe_access(full_path, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                for line in content:
                    f.write(line)
        return str(full_path)

    def delete_file(self, path: str) -> bool:
        full_path = self._validate_path(self._base_path / path)
        return self._safe_delete(full_path)

    def list_files(self, folder_path: str, extension: str = "*") -> list[Path]:
        target = self._validate_path(self._base_path / folder_path)
        if not target.is_dir():
            return []
        pattern = f"*.{extension.lstrip('.')}" if extension != "*" else "*"
        return list(target.glob(pattern))

    def exists(self, path: str) -> bool:
        return (self._base_path / path).exists()

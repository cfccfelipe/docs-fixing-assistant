from pathlib import Path

import pytest

from infrastructure.storage.local_file_system_adapter import LocalFileSystemAdapter
from infrastructure.storage.storage_mixin import StorageContextMixin


class MockStorage(StorageContextMixin):
    """Mock class to test mixin logic."""

    pass


def test_validate_path_blocks_traversal():
    storage = MockStorage()

    # Intentar salir de la carpeta permitida
    with pytest.raises(PermissionError, match="Path traversal attempt"):
        storage._validate_path("../../etc/passwd")


def test_validate_path_allows_valid_subpath():
    storage = MockStorage()
    path = "src/main.py"
    validated = storage._validate_path(path)
    assert isinstance(validated, Path)
    assert str(validated) == "src/main.py"


def test_write_and_read_file(tmp_path):
    # tmp_path actúa como nuestro base_path seguro
    adapter = LocalFileSystemAdapter(base_path=tmp_path)
    test_file = "hello.txt"
    content = "AI is working"

    # Escribir
    adapter.write_file(test_file, content)

    # Verificar que el archivo existe físicamente en la carpeta temporal
    assert (tmp_path / test_file).exists()
    assert (tmp_path / test_file).read_text() == content

    # Leer a través del adaptador
    read_content = adapter.read_file(test_file)
    assert read_content == content


def test_list_files_filtering(tmp_path):
    adapter = LocalFileSystemAdapter(base_path=tmp_path)
    (tmp_path / "script.py").write_text("print(1)")
    (tmp_path / "readme.md").write_text("# Hello")

    files = adapter.list_files(".", extension="py")
    assert len(files) == 1
    assert files[0].name == "script.py"

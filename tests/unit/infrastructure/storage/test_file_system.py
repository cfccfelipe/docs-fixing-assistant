from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from domain.utils.exceptions import FileSystemException
from infrastructure.adapters.storage.local_file_system import (
    FileReadTool,
    FileWriteTool,
    LocalFileSystemAdapter,
)


# Mock del context manager para safe_access (reutilizable)
@contextmanager
def mock_safe_access_logic(path, mode, storage_type="local"):
    mock_file = MagicMock()
    if "r" in mode:
        mock_file.read.return_value = "dummy content"
    yield mock_file


class TestFileSystemTools:
    # --- FileReadTool (ahora parte de LocalFileSystemAdapter) ---

    def test_file_read_success(self):
        """Valida que la lectura use el puerto unificado correctamente."""
        tool = FileReadTool()
        with patch.object(
            LocalFileSystemAdapter, "safe_access", side_effect=mock_safe_access_logic
        ):
            result = tool.read_file(path="test.md")
            assert result == "dummy content"

    def test_file_read_exception_handling(self):
        """Verifica que @handle_errors atrape fallos de disco."""
        tool = FileReadTool()

        @contextmanager
        def error_access(*args, **kwargs):
            raise OSError("Disk failure")
            yield

        with patch.object(
            LocalFileSystemAdapter, "safe_access", side_effect=error_access
        ):
            with pytest.raises(FileSystemException, match="Disk failure"):
                tool.read_file(path="crash.md")

    # --- FileWriteTool (Soporte para Strings e Iterables) ---

    def test_file_write_string_success(self):
        """Valida la escritura estándar de strings."""
        tool = FileWriteTool()
        mock_file = MagicMock()

        @contextmanager
        def capture_write(*args, **kwargs):
            yield mock_file

        with patch.object(
            LocalFileSystemAdapter, "safe_access", side_effect=capture_write
        ):
            tool.write_file(path="output.md", content="hello")
            mock_file.write.assert_called_once_with("hello")

    def test_file_write_streaming_success(self):
        """
        CRITICAL: Valida que el adaptador soporte streaming (iterables).
        Este es el corazón de la eficiencia de memoria en Manizales.
        """
        tool = FileWriteTool()
        mock_file = MagicMock()
        chunks = ["chunk1", "chunk2", "chunk3"]

        @contextmanager
        def capture_write(*args, **kwargs):
            yield mock_file

        with patch.object(
            LocalFileSystemAdapter, "safe_access", side_effect=capture_write
        ):
            tool.write_file(path="large_file.xml", content=iter(chunks))

            # Verificamos que se llamó a write por cada fragmento
            assert mock_file.write.call_count == 3
            mock_file.write.assert_any_call("chunk1")
            mock_file.write.assert_any_call("chunk3")

    # --- LocalFileSystemAdapter: list_files ---

    def test_list_files_filtering(self, tmp_path):
        """Verifica que el listado sea genérico y filtre basura."""
        # Inicializamos el adapter con base_dir=tmp_path
        adapter = LocalFileSystemAdapter(base_dir=str(tmp_path))

        # Creamos archivos de prueba
        (tmp_path / "valid.xml").write_text("<root/>")
        (tmp_path / "another.xml").write_text("<root/>")
        (tmp_path / "ignore.txt").write_text("text")
        (tmp_path / "consolidated.xml").write_text("<root/>")  # Debe ignorarse
        (tmp_path / "empty.xml").write_text("")  # Debe ignorarse

        files = adapter.list_files(str(tmp_path), extension="xml")

        filenames = [f.name for f in files]
        assert "valid.xml" in filenames
        assert "another.xml" in filenames
        assert "ignore.txt" not in filenames
        assert "consolidated.xml" not in filenames
        assert "empty.xml" not in filenames
        assert len(files) == 2

    # --- Compatibility Layer (ITool) ---

    def test_adapter_execute_compatibility(self):
        """Asegura que el método execute (ITool) despache a los métodos correctos."""
        adapter = LocalFileSystemAdapter()

        with patch.object(adapter, "read_file") as mock_read:
            adapter.execute(operation="read", path="test.md")
            mock_read.assert_called_once_with("test.md")

        with patch.object(adapter, "write_file") as mock_write:
            adapter.execute(operation="write", path="test.md", content="data")
            mock_write.assert_called_once_with("test.md", "data")

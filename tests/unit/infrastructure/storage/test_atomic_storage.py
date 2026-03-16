from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import defusedxml.ElementTree as dET
import pytest
from defusedxml import defuse_stdlib

# Importamos la excepción de dominio necesaria
from domain.utils.exceptions import FileSystemException
from infrastructure.adapters.storage.atomic_storage import (
    AtomicSourceStorageTool,
)

ET = dET
defuse_stdlib()


class TestAtomicSourceStorageTool:
    @pytest.fixture
    def tool(self):
        return AtomicSourceStorageTool()

    @pytest.fixture
    def mock_storage(self, tool):
        """Mocks the safe_access context manager from StorageContextMixin."""
        mock_file = MagicMock()

        @contextmanager
        def mock_safe_access(*args, **kwargs):
            yield mock_file

        with patch.object(
            AtomicSourceStorageTool, "safe_access", side_effect=mock_safe_access
        ):
            yield mock_file

    ## --- Tests for New File Creation ---

    def test_execute_creates_new_xml_structure(self, tool, mock_storage, tmp_path):
        """Verifies initial XML assembly with metadata and segmenting."""
        # Estructura: /tmp/project/xml/file.xml
        # PARENT_DIRECTORY debería ser "project"
        project_dir = tmp_path / "project"
        storage_dir = project_dir / "xml"

        file_name = "test-document"
        raw_content = "# Hello World\nThis is content."

        # Act
        result_path = tool.execute(
            raw_content=raw_content, file_name=file_name, storage_path=str(storage_dir)
        )

        # Assert
        assert "test-document.xml" in result_path

        written_content = mock_storage.write.call_args[0][0]
        root = ET.fromstring(written_content)

        # Check Metadata
        assert root.find("metadata/ORIGINAL_FILE_NAME").text == "test-document"
        assert root.find("metadata/PARENT_DIRECTORY").text == "project"

        # Check Segment
        segment = root.find("segment[@id='1']")
        assert "Hello World" in segment.text
        assert "[LEVEL_1]" in segment.text

    ## --- Tests for Updating Existing Files ---

    def test_execute_updates_existing_xml_preserves_metadata(
        self, tool, mock_storage, tmp_path
    ):
        """Ensures that when a file exists, we merge content but keep original metadata tags."""
        storage_dir = tmp_path / "project" / "xml"
        storage_dir.mkdir(parents=True)

        existing_xml = (
            "<root>"
            "  <metadata><ORIGINAL_FILE_NAME>old_name</ORIGINAL_FILE_NAME><PARENT_DIRECTORY>project</PARENT_DIRECTORY></metadata>"
            '  <segment id="1">Old Content</segment>'
            "</root>"
        )

        with patch("pathlib.Path.exists", return_value=True):
            with patch("defusedxml.ElementTree.parse") as mock_parse:
                mock_tree = MagicMock()
                mock_tree.getroot.return_value = ET.fromstring(existing_xml)
                mock_parse.return_value = mock_tree

                # Act
                tool.execute(
                    raw_content="<new_tag>Updated Content</new_tag>",
                    file_name="existing",
                    storage_path=str(storage_dir),
                )

        written_content = mock_storage.write.call_args[0][0]
        root = ET.fromstring(written_content)

        segment = root.find("segment[@id='1']")
        assert segment.find("new_tag").text == "Updated Content"
        assert root.find("metadata/ORIGINAL_FILE_NAME").text == "old_name"

    ## --- Tests for Security and Sanitization ---

    def test_file_name_sanitization(self, tool, mock_storage, tmp_path):
        """Verifies that malicious or weird file names are sanitized."""
        # Act
        result_path = tool.execute(
            raw_content="content",
            file_name="malicious/../file!@#",
            storage_path=str(tmp_path / "project" / "xml"),
        )

        assert "maliciousfile.xml" in result_path

    def test_missing_parameters_raises_error(self, tool):
        """Verifies Domain Exception when required fields are missing."""
        # CAMBIO: Esperamos FileSystemException, no ValueError
        with pytest.raises(FileSystemException, match="Faltan parámetros requeridos"):
            tool.execute(raw_content="only content")

    ## --- Markdown Cleaning Logic ---

    def test_clean_markdown_strips_obsidian_syntax(self, tool):
        """Tests internal _clean_markdown helper for specific patterns."""
        dirty_md = (
            "---frontmatter---\n# Title\n[[Link]] and ![[Image.png]]\n%%Comment%%"
        )
        cleaned = tool._clean_markdown(dirty_md)

        assert "frontmatter" not in cleaned
        assert "Link" in cleaned
        assert "Image.png" not in cleaned
        assert "Comment" not in cleaned
        assert "[LEVEL_1] Title" in cleaned

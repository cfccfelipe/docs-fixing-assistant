from unittest.mock import MagicMock

from domain.orchestrator.tool_registry import ToolRegistry
from infrastructure.tools.read_file_tool import ReadFileTool


def test_tool_metadata_is_correct():
    mock_fs = MagicMock()
    tool = ReadFileTool(fs=mock_fs)

    assert tool.metadata.name == "read_file"
    assert "path" in tool.metadata.arguments["required"]


def test_tool_execution_calls_adapter():
    mock_fs = MagicMock()
    mock_fs.read_file.return_value = "file content"
    tool = ReadFileTool(fs=mock_fs)

    # El LLM enviaría los argumentos así:
    result = tool(path="test.py")

    # Verificar que la Tool extrajo 'path' y se lo pasó al adaptador
    mock_fs.read_file.assert_called_once_with("test.py")
    assert result == "file content"


def test_registry_execution_flow():
    registry = ToolRegistry()
    mock_tool = MagicMock()
    mock_tool.metadata.name = "get_weather"
    mock_tool.return_value = "Sunny"

    registry.register(mock_tool)

    # El orquestador llama al registry por nombre
    result = registry.execute("get_weather", location="Manizales")

    assert result == "Sunny"
    mock_tool.assert_called_once_with(location="Manizales")

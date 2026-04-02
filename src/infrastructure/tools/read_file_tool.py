from domain.models.enums import ToolType
from domain.models.tool_model import ToolDefinition
from domain.ports.file_system_port import FileSystemPort
from domain.ports.tool_port import ITool


class ReadFileTool(ITool):
    """
    Surgical tool for reading file contents.
    Encapsulates the FileSystemPort.read_file logic.
    """

    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    @property
    def metadata(self) -> ToolDefinition:
        """Defines the schema for reading operations."""
        return ToolDefinition(
            name="read_file",
            description="Reads the full content of a file. Use this to analyze existing code or documentation.",
            type=ToolType.FUNCTION,
            arguments={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file (e.g., 'src/main.py')",
                    }
                },
                "required": ["path"],
            },
        )

    def __call__(self, **kwargs) -> str:
        """Executes the read operation with surgical argument extraction."""
        path = kwargs.get("path")
        if not path:
            raise ValueError("The 'path' argument is required for read_file.")
        return self.fs.read_file(path)

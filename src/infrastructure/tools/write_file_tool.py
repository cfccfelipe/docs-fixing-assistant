from domain.models.enums import ToolType
from domain.models.tool_model import ToolDefinition
from domain.ports.file_system_port import FileSystemPort
from domain.ports.tool_port import ITool


class WriteFileTool(ITool):
    """
    Surgical tool for writing or updating files.
    Encapsulates the FileSystemPort.write_file logic.
    """

    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    @property
    def metadata(self) -> ToolDefinition:
        """Defines the schema for writing operations."""
        return ToolDefinition(
            name="write_file",
            description="Creates or updates a file with the provided content. Overwrites if it exists.",
            type=ToolType.FUNCTION,
            arguments={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file.",
                    },
                },
                "required": ["path", "content"],
            },
        )

    def __call__(self, **kwargs) -> str:
        """Executes the write operation with surgical argument extraction."""
        path = kwargs.get("path")
        content = kwargs.get("content")
        if not path or content is None:
            raise ValueError("Both 'path' and 'content' are required for write_file.")
        return self.fs.write_file(path, content)

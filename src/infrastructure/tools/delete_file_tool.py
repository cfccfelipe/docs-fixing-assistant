from domain.models.enums import ToolType
from domain.models.tool_model import ToolDefinition
from domain.ports.file_system_port import FileSystemPort
from domain.ports.tool_port import ITool


class DeleteFileTool(ITool):
    """
    Surgical tool for removing files.
    Encapsulates the FileSystemPort.delete_file logic.
    """

    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    @property
    def metadata(self) -> ToolDefinition:
        """Defines the schema for deletion operations."""
        return ToolDefinition(
            name="delete_file",
            description="Deletes a file permanently from the workspace. Use with caution.",
            type=ToolType.FUNCTION,
            arguments={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file to be deleted.",
                    }
                },
                "required": ["path"],
            },
        )

    def __call__(self, **kwargs) -> str:
        """Executes the delete operation with surgical argument extraction."""
        path = kwargs.get("path")
        if not path:
            raise ValueError("The 'path' argument is required for delete_file.")

        success = self.fs.delete_file(path)
        return (
            f"File '{path}' deleted successfully."
            if success
            else f"File '{path}' not found."
        )

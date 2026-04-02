from domain.models.enums import ToolType
from domain.models.tool_model import ToolDefinition
from domain.ports.file_system_port import FileSystemPort
from domain.ports.tool_port import ITool


class ListFilesTool(ITool):
    """
    Surgical tool for exploring directory structures.
    Encapsulates the FileSystemPort.list_files logic.
    """

    def __init__(self, fs: FileSystemPort):
        self.fs = fs

    @property
    def metadata(self) -> ToolDefinition:
        """Defines the schema for directory listing."""
        return ToolDefinition(
            name="list_files",
            description="Lists files in a directory to understand the project structure and find relevant files.",
            type=ToolType.FUNCTION,
            arguments={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Relative path to the folder (use '.' for root).",
                    },
                    "extension": {
                        "type": "string",
                        "description": "Optional filter (e.g., 'py', 'md'). Use '*' for all.",
                        "default": "*",
                    },
                },
                "required": ["folder_path"],
            },
        )

    def __call__(self, **kwargs) -> str:
        """Executes the listing operation and returns a formatted string for the LLM."""
        folder_path = kwargs.get("folder_path", ".")
        extension = kwargs.get("extension", "*")

        files = self.fs.list_files(folder_path, extension)

        if not files:
            return f"No files found in '{folder_path}' with extension '{extension}'."

        # Convertimos Path objects a strings legibles para el LLM
        return "\n".join([str(f.relative_to(self.fs.base_path)) for f in files])

import re
from datetime import datetime

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError


class MermaidDiagramParser(BaseParser):
    """
    Parser for Mermaid diagrams.
    Inherits from BaseParser to apply normalization and logging first.
    """

    @staticmethod
    def sanitize_mermaid(text: str) -> str:
        """
        Sanitizes Mermaid syntax to prevent common errors.
        """
        text = re.sub(r"\|.*?\|", "", text)
        if not text.strip().startswith(("graph", "flowchart", "sequenceDiagram")):
            text = "graph LR\n" + text
        return text.strip()

    @handle_errors(ParserError, parser="MermaidDiagramParser")
    async def __call__(self, state: AgentState) -> NodeResponse:
        # 1. Ejecuta normalización base
        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        # 2. Sanitiza Mermaid antes de validar
        sanitized = self.sanitize_mermaid(cleaned)

        # 3. Inicializa errores de forma segura
        errors: list[str] = []
        if base_response.metadata and base_response.metadata.validation_errors:
            errors.extend(base_response.metadata.validation_errors)

        # 4. Validación específica de Mermaid
        if not (
            sanitized.strip().startswith("graph") or "sequenceDiagram" in sanitized
        ):
            errors.append("Invalid Mermaid diagram syntax.")

        # 5. Mensaje de salida
        dispatch_msg = (
            "Mermaid diagram is valid."
            if not errors
            else "Mermaid diagram errors found."
        )

        return NodeResponse(
            content=sanitized,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="mermaid_diagram_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

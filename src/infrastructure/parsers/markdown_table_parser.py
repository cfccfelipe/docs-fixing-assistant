import re
from datetime import datetime

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError


class MarkdownTableParser(BaseParser):
    """
    Parser for Markdown tables.
    Inherits from BaseParser to apply normalization and logging first.
    """

    @handle_errors(ParserError, parser="MarkdownTableParser")
    async def __call__(self, state: AgentState) -> NodeResponse:
        # 1. Ejecuta normalización base
        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        # 2. Inicializa errores de forma segura
        errors: list[str] = []
        if base_response.metadata and base_response.metadata.validation_errors:
            errors.extend(base_response.metadata.validation_errors)

        # 3. Validación específica de tablas Markdown
        if "|" not in cleaned or re.search(r"---", cleaned) is None:
            errors.append("Invalid Markdown table format.")

        # 4. Mensaje de salida
        dispatch_msg = (
            "Markdown table is valid." if not errors else "Markdown table errors found."
        )

        return NodeResponse(
            content=cleaned,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="markdown_table_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

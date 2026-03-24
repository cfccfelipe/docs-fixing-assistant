from datetime import datetime

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError


class TextParser(BaseParser):
    """
    Parser for plain text.
    Inherits from BaseParser to apply normalization and logging first.
    """

    @handle_errors(ParserError, parser="TextParser")
    async def __call__(self, state: AgentState) -> NodeResponse:
        # 1. Ejecuta normalización base
        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        # 2. Inicializa errores de forma segura
        errors: list[str] = []
        if base_response.metadata and base_response.metadata.validation_errors:
            errors.extend(base_response.metadata.validation_errors)

        # 3. Validación específica de texto plano
        if not cleaned.strip():
            errors.append("Text content is empty.")

        # 4. Mensaje de salida
        dispatch_msg = "Text is valid." if not errors else "Text parsing issues found."

        return NodeResponse(
            content=cleaned,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="text_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

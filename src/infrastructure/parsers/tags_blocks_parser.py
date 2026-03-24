import re
from datetime import datetime

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError


class TagsBlocksParser(BaseParser):
    """
    Parser especializado en extraer bloques balanceados por etiquetas.
    Ejemplo: <tag>contenido</tag>
    """

    @handle_errors(ParserError, parser="TagsBlocksParser")
    async def __call__(self, state: AgentState) -> NodeResponse:
        # 1. Normalización base
        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        # 2. Inicializa errores
        errors: list[str] = []
        if base_response.metadata and base_response.metadata.validation_errors:
            errors.extend(base_response.metadata.validation_errors)

        # 3. Extracción de bloques balanceados
        pattern = r"(<(?P<tag>[a-zA-Z0-9_:-]+).*?>[\s\S]*?</(?P=tag)>)"
        match = re.search(pattern, cleaned)
        extracted = match.group(1).strip() if match else ""

        if not extracted:
            errors.append("No balanced tag block found.")

        # 4. Mensaje de salida
        dispatch_msg = (
            "Tag block parsed successfully."
            if not errors
            else "Tag block parsing issues found."
        )

        return NodeResponse(
            content=extracted if extracted else cleaned,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="tags_blocks_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

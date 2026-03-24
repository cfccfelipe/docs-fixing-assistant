import re
from datetime import datetime

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError


class FlashcardsParser(BaseParser):
    """
    Parser especializado en flashcards con formato [[Pregunta]]::Respuesta.
    """

    @handle_errors(ParserError, parser="FlashcardsParser")
    async def __call__(self, state: AgentState) -> NodeResponse:
        # 1. Normalización base
        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        # 2. Inicializa errores
        errors: list[str] = []
        if base_response.metadata and base_response.metadata.validation_errors:
            errors.extend(base_response.metadata.validation_errors)

        # 3. Validación de flashcards
        card_pattern = r"\[\[.*?\]\]*?::.*"
        matches = [
            line.strip()
            for line in cleaned.splitlines()
            if re.search(card_pattern, line)
        ]
        if not matches:
            errors.append("No valid flashcards found.")

        # 4. Mensaje de salida
        dispatch_msg = (
            "Flashcards parsed successfully."
            if not errors
            else "Flashcards parsing issues found."
        )

        return NodeResponse(
            content="\n".join(matches) if matches else cleaned,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="flashcards_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

import logging
import re
from datetime import datetime

from lxml import etree as ET  # nosec B410

from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError

logger = logging.getLogger(__name__)


class XMLContentParser(BaseParser):
    """Parser especializado en XML."""

    # --- Helpers internos ---
    @staticmethod
    def _extract_xml_root(text: str, root_tag: str = "atomic_structure") -> str:
        """
        Extrae un bloque XML con la etiqueta raíz especificada.
        """
        pattern = rf"<{root_tag}>[\s\S]*?</{root_tag}>"
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
        if "<topic" in text or "<pattern" in text:
            return f"<{root_tag}>\n{text}\n</{root_tag}>"
        return ""

    @staticmethod
    def _get_safe_parser() -> ET.XMLParser:
        """
        Devuelve un parser XML seguro con restricciones de red y entidades.
        """
        return ET.XMLParser(
            resolve_entities=False,
            no_network=True,
            dtd_validation=False,
            load_dtd=False,
            huge_tree=False,
        )

    @staticmethod
    def _get_syntax_errors(content: str) -> list[str]:
        """
        Valida sintaxis XML y devuelve lista de errores.
        """
        if not content.strip():
            return ["Content is empty"]

        try:
            parser = XMLContentParser._get_safe_parser()
            ET.fromstring(content.encode("utf-8"), parser=parser)  # nosec B320
            return []
        except ET.XMLSyntaxError as e:
            return [f"XML Error: Line {e.position[0]}, Col {e.position[1]}: {e.msg}"]
        except Exception as e:
            return [f"Fatal Parse Error: {str(e)}"]

    # --- Parser principal ---
    @handle_errors(ParserError, parser="XMLContentParser")
    async def __call__(self, state: AgentState) -> NodeResponse:

        base_response = await super().__call__(state)
        cleaned = base_response.content or ""

        errors = self._get_syntax_errors(cleaned)

        dispatch_msg = "XML is valid." if not errors else f"XML errors: {len(errors)}"
        logger.info(dispatch_msg)

        return NodeResponse(
            content=cleaned,
            results=[dispatch_msg],
            iterations=0,
            metadata=StateMetadata(
                last_agent="xml_content_parser",
                validation_errors=errors,
                timestamp=datetime.now().timestamp(),
            ),
        )

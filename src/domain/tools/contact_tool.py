import logging
import re
from typing import Any

from domain.ports.tool_port import ITool

logger = logging.getLogger(__name__)


class ConcatTool(ITool):
    """
    Tool that finalizes the XML structure efficiently.
    Enforces the 2-metadata contract: ORIGINAL_FILE_NAME and PARENT_DIRECTORY.
    """

    name = "concat_tool"
    description = "Concatenates XML segments, injects dynamic metadata, and ensures root structure."
    parameters = {
        "type": "object",
        "properties": {
            "raw_content": {
                "type": "string",
                "description": "XML content (usually atomic_structure blocks)",
            },
            "original_file_name": {
                "type": "string",
                "description": "Names of source files (e.g., 'auth.xml, db.xml')",
            },
            "parent_directory": {
                "type": "string",
                "description": "Source folder name",
            },
        },
        "required": ["raw_content"],
    }

    def execute(self, **kwargs: Any) -> str:
        raw_content = kwargs.get("raw_content")
        original_file_name = kwargs.get("original_file_name", "unknown_source")
        parent_directory = kwargs.get("parent_directory", "unknown_folder")

        if not raw_content:
            logger.error("ConcatTool: raw_content is missing")
            raise ValueError("Missing required parameter: raw_content")

        # 1. Limpieza de caracteres invisibles y espacios (Operación in-place)
        raw_content = raw_content.lstrip("\ufeff").strip()

        # 2. Unificación eficiente de bloques atómicos
        # Si el LLM devolvió múltiples tags, los consolidamos en un solo bloque coherente.
        if "<atomic_structure" in raw_content:
            logger.info("ConcatTool: extracting and merging atomic segments")

            # Usamos finditer para procesar el string sin crear listas gigantes intermedias
            matches = re.findall(
                r"<atomic_structure.*?>(.*?)</atomic_structure>", raw_content, re.DOTALL
            )

            if matches:
                # Unificamos el contenido interior de los bloques
                inner_content = (
                    "<atomic_structure>\n"
                    + "\n".join(m.strip() for m in matches if m.strip())
                    + "\n</atomic_structure>"
                )
            else:
                inner_content = raw_content
        else:
            # Fallback por si el LLM no devolvió los tags esperados
            inner_content = (
                "<atomic_structure>\n" + raw_content + "\n</atomic_structure>"
            )

        # 3. ENVOLTURA FINAL (Contrato estricto de 2 metadatos)
        # Optimizamos con f-strings para evitar concatenaciones múltiples (+)
        logger.info(f"ConcatTool: finalizing XML for {parent_directory}")

        return (
            f"<root>\n"
            f"  <metadata>\n"
            f"    <ORIGINAL_FILE_NAME>{original_file_name}</ORIGINAL_FILE_NAME>\n"
            f"    <PARENT_DIRECTORY>{parent_directory}</PARENT_DIRECTORY>\n"
            f"  </metadata>\n"
            f"  <segment id='1'>\n"
            f"    {inner_content}\n"
            f"  </segment>\n"
            f"</root>"
        )

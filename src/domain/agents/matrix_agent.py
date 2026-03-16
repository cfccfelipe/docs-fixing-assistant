import asyncio
import logging
import re

from domain.constants.system_prompts import SYSTEM_PROMPT_MATRIX
from domain.constants.users_prompts import USER_PROMPT_MATRIX
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class MatrixAgent(AgentPort):
    """
    Agente responsable de generar matrices estratégicas (Eisenhower, SWOT, etc.)
    a partir de contenido XML. Simplificado para mayor claridad y robustez.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_MATRIX

    async def run(self, content: str) -> str:
        logger.info("Running MatrixAgent...")

        user_prompt = USER_PROMPT_MATRIX.format(xml_content=content)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            # Limpieza de fences y notas explicativas
            clean_content = (
                raw_content.replace("```markdown", "").replace("```", "").strip()
            )
            clean_content = re.sub(r"(?im)^note:.*$", "", clean_content)
            clean_content = re.sub(r"(?im)^(this|the)\s+table.*$", "", clean_content)

            # Asegurar que empieza con la cabecera de tabla
            if not clean_content.startswith("|"):
                for line in clean_content.splitlines():
                    if line.strip().startswith("|"):
                        clean_content = "\n".join(
                            clean_content.splitlines()[
                                clean_content.splitlines().index(line) :
                            ]
                        )
                        break

            return clean_content or "[Empty Matrix]"

        except asyncio.CancelledError:
            logger.warning("MatrixAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en MatrixAgent: {e}")
            return "[Error en MatrixAgent]"

    def _to_string(self, response) -> str:
        """Convierte la respuesta en string."""
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

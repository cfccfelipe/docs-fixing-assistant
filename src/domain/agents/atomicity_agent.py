import asyncio
import logging
import re

from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_ATOMICITY
from domain.orchestrator.constants.user_prompts import USER_PROMPT_ATOMICITY
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class AtomicityAgent(AgentPort):
    """
    Agente responsable de transformar segmentos [LEVEL_N] en una
    estructura XML limpia y anidada. Simplificado para mayor claridad.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider

    async def run(self, content: str) -> str:
        logger.info("Running AtomicityAgent...")

        messages = [
            {"role": "system", "content": system_prompts.SYSTEM_PROMPT_ATOMICITY},
            {
                "role": "user",
                "content": users_prompts.USER_PROMPT_ATOMICITY.format(
                    xml_content=content
                ),
            },
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_output = self._to_string(response)

            # Limpieza de fences y comillas
            cleaned = re.sub(
                r"^```xml\s*|\s*```$", "", raw_output.strip(), flags=re.MULTILINE
            )
            if cleaned.startswith('"') and cleaned.endswith('"'):
                cleaned = cleaned[1:-1].strip()

            return cleaned or "[Empty Atomicity Output]"

        except asyncio.CancelledError:
            logger.warning("AtomicityAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en AtomicityAgent: {e}")
            return "[Error en AtomicityAgent]"

    def _to_string(self, response) -> str:
        """Convierte la respuesta en string."""
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

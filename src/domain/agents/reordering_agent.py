import asyncio
import logging
import re

from domain.orchestrator.constants import system_prompts, user_prompts
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class ReorderingAgent(AgentPort):
    """
    Agente responsable de concatenar, reordenar y validar segmentos XML.
    Optimizado para ejecución asíncrona y limpieza mínima de artefactos.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider

    async def run(self, content: str) -> str:
        logger.info("Running ReorderingAgent...")

        messages = [
            {"role": "system", "content": system_prompts.SYSTEM_PROMPT_REORDER},
            {"role": "user", "content": user_prompts.USER_PROMPT_REORDER},
            {"role": "user", "content": content},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_output = self._to_string(response)

            # Limpieza básica de artefactos
            cleaned = re.sub(
                r"^```xml\s*|\s*```$", "", raw_output.strip(), flags=re.MULTILINE
            )
            if cleaned.startswith('"') and cleaned.endswith('"'):
                cleaned = cleaned[1:-1].strip()

            return cleaned or "[Empty Reordering Output]"

        except asyncio.CancelledError:
            logger.warning("ReorderingAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en ReorderingAgent: {e}")
            return "[Error en ReorderingAgent]"

    def _to_string(self, response) -> str:
        """Convierte la respuesta en string."""
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

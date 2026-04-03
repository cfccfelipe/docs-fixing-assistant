import asyncio
import hashlib
import logging

from domain.orchestrator.constants import user_prompts
from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_NAMING
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class NamingAgent(AgentPort):
    """
    Agente encargado de generar un nombre de archivo semánticamente preciso.
    Simplificado para mayor claridad y robustez.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_NAMING

    async def run(self, content: str) -> str:
        logger.info("Ejecutando NamingAgent...")

        user_prompt = (
            users_prompts.USER_PROMPT_NAMING.format(xml_content=content)
            + "\n\nDevuelve SOLO un nombre de archivo en snake_case terminado en _Strategic."
        )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            clean_name = self._sanitize_filename(raw_content)
            if clean_name:
                logger.info(f"✅ Nombre estratégico definido: {clean_name}")
                return clean_name

            return self._fallback(content)

        except asyncio.CancelledError:
            logger.warning("NamingAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en NamingAgent: {e}")
            return self._fallback(content)

    def _to_string(self, response) -> str:
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

    def _sanitize_filename(self, text: str) -> str:
        """Limpia y valida el nombre."""
        text = text.strip().replace("`", "").replace('"', "").replace("'", "")
        # Tomar la primera línea no vacía
        candidate = text.splitlines()[-1].strip() if text else ""

        # Filtrar metadatos
        if any(
            token in candidate.lower() for token in ["model=", "created_at=", "done="]
        ):
            return ""

        # Normalizar
        candidate = (
            candidate.replace(" ", "_").replace("-", "_").replace(".", "_").strip("_")
        )

        # Validación mínima
        if not candidate or len(candidate) > 40:
            return ""

        if not candidate.lower().endswith("strategic"):
            candidate = f"{candidate}_Strategic"

        return candidate

    def _fallback(self, content: str) -> str:
        """Genera nombre de emergencia basado en hash."""
        content_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[
            :8
        ]
        return f"Resource_{content_hash}_Strategic"

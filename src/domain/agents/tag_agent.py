import asyncio
import logging

from domain.constants.system_prompts import SYSTEM_PROMPT_TAGS
from domain.constants.users_prompts import USER_PROMPT_TAGS
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class TagAgent(AgentPort):
    """
    Agente responsable de generar metadatos YAML (tags) a partir de contenido XML.
    Optimizado para claridad y menor complejidad.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_TAGS

    async def run(self, content: str) -> str:
        logger.info("Running TagAgent for Metadata...")
        user_prompt = USER_PROMPT_TAGS.format(xml_content=content)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            yaml_block = self._extract_yaml(raw_content)
            return self._enforce_wikilinks(yaml_block) or "[Empty YAML]"

        except asyncio.CancelledError:
            logger.warning("TagAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en TagAgent: {e}")
            return "[Error en TagAgent]"

    def _to_string(self, response) -> str:
        """Convierte la respuesta en string."""
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

    def _extract_yaml(self, text: str) -> str:
        """Extrae bloque YAML delimitado por --- si existe."""
        text = text.replace("```yaml", "").replace("```", "").strip()
        if text.count("---") >= 2:
            first, last = text.find("---"), text.rfind("---")
            return text[first : last + 3].strip()
        return text

    def _enforce_wikilinks(self, yaml_text: str) -> str:
        """Asegura que ciertos campos tengan formato [[...]]."""
        target_keys = ("category:", "moc:", "trade_off:")
        lines = []
        for line in yaml_text.splitlines():
            if any(key in line for key in target_keys):
                val = line.split(":", 1)[-1].strip().strip('"')
                if val and not val.startswith("[["):
                    val = f"[[{val.strip('[]')}]]"
                line = f'{line.split(":")[0]}: "{val}"'
            lines.append(line)
        return "\n".join(lines).strip()

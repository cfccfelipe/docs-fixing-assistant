import asyncio
import logging
import re

from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_CASE_STUDY
from domain.orchestrator.constants.user_prompts import USER_PROMPT_CASE_STUDY
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class CaseStudyAgent(AgentPort):
    """
    Agente responsable de generar estudios de caso estratégicos
    a partir de contenido XML. Simplificado para mayor claridad y robustez.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_CASE_STUDY

    async def run(self, content: str) -> str:
        logger.info("Running CaseStudyAgent...")

        user_prompt = USER_PROMPT_CASE_STUDY.format(xml_content=content)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            # Limpieza básica de fences, notas y formato prohibido
            clean_content = (
                raw_content.replace("```markdown", "")
                .replace("```", "")
                .replace("**", "")
                .strip()
            )
            clean_content = re.sub(r"(?im)^note:.*$", "", clean_content)

            # Ajuste: unir clave y contenido en un solo párrafo
            for key in ("case_of_use::", "correct_solution::", "incorrect_solution::"):
                clean_content = re.sub(rf"({key})\s*\n+", r"\1 ", clean_content)

            # Asegurar que empieza con case_of_use::
            if not clean_content.startswith("case_of_use::"):
                for line in clean_content.splitlines():
                    if line.strip().startswith("case_of_use::"):
                        idx = clean_content.splitlines().index(line)
                        clean_content = "\n".join(clean_content.splitlines()[idx:])
                        break

            return clean_content or "[Empty Case Study]"

        except asyncio.CancelledError:
            logger.warning("CaseStudyAgent cancelado.")
            raise
        except Exception as e:
            logger.error(f"❌ Error en CaseStudyAgent: {e}")
            return "[Error en CaseStudyAgent]"

    def _to_string(self, response) -> str:
        """Convierte la respuesta en string."""
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

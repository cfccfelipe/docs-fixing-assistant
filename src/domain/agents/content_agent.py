import logging
import re

from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_CONTENT
from domain.orchestrator.constants.user_prompts import USER_PROMPT_CONTENT
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class ContentAgent(AgentPort):
    """
    Agent optimized to transform XML into exhaustive strategic architecture.
    Ensures 0% data loss and clean Obsidian H2-H4 hierarchy.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_CONTENT

    async def run(self, content: str) -> str:
        logger.info("Running ContentAgent: Exhaustive Strategic Synthesis...")

        user_prompt = USER_PROMPT_CONTENT.format(xml_content=content)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)

            # Safe content extraction
            if isinstance(response, dict):
                raw_content = response.get("content", "").strip()
            else:
                raw_content = str(response).strip()

            if not raw_content:
                return "> [!error] Failed to generate technical content."

            # Perform deep cleaning to ensure professional output
            return self._clean_output(raw_content)

        except Exception as e:
            logger.error(f"❌ Error in ContentAgent: {str(e)}")
            return f"> [!caution] Synthesis Error: {type(e).__name__}"

    def _clean_output(self, text: str) -> str:
        """
        Removes markdown fences, conversational noise, and enforces
        start at the first Pillar (##).
        """
        # 1. Remove markdown code fences
        text = re.sub(r"```markdown|```", "", text).strip()

        # 2. Force start at the first H2 (Pillar) to remove "Here is the document..."
        if "##" in text:
            text = text[text.find("##") :]

        # 3. Remove common LLM concluding fluff (Case insensitive)
        noise_patterns = [
            r"(?i)^This concludes.*",
            r"(?i)^The output above.*",
            r"(?i)^In summary.*",
            r"(?i)^I have reformatted.*",
            r"(?i)^I hope this.*",
        ]
        for pattern in noise_patterns:
            text = re.sub(pattern, "", text, flags=re.MULTILINE)

        return text.strip()

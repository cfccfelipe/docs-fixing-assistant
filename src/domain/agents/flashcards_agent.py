import asyncio
import logging
import re

from domain.constants.system_prompts import SYSTEM_PROMPT_FLASHCARDS
from domain.constants.users_prompts import USER_PROMPT_FLASHCARDS
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class FlashcardsAgent(AgentPort):
    """
    Agent responsible for generating high-precision technical flashcards.
    Optimized for Obsidian Spaced Repetition (Concept :: Action).
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_FLASHCARDS

    async def run(self, content: str) -> str:
        logger.info("Running FlashcardsAgent: Action-Oriented Recall...")

        user_prompt = USER_PROMPT_FLASHCARDS.format(xml_content=content)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            # Clean and validate the output
            clean_content = self._sanitize_output(raw_content)

            return clean_content if clean_content else "[Empty Flashcards]"

        except asyncio.CancelledError:
            logger.warning("FlashcardsAgent cancelled.")
            raise
        except Exception as e:
            logger.error(f"❌ Error in FlashcardsAgent: {e}")
            return f"> [!error] Flashcard Generation Error: {type(e).__name__}"

    def _to_string(self, response) -> str:
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

    def _sanitize_output(self, text: str) -> str:
        """
        Aggressively removes LLM noise, numbering, and empty front-sides.
        Ensures valid [[WikiLink]] :: Action format.
        """
        # 1. Strip markdown fences and intro/outro noise
        text = re.sub(r"```[a-z]*\n|```", "", text).strip()

        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:
            # 2. Extract only the portion starting from the first '[[' to catch 'Flashcard 1: [[X]]'
            match = re.search(r"(\[\[.*?\]\].*?::.*)", line)

            if match:
                clean_line = match.group(1).strip()

                # 3. Validation: Split and check if Front Side has real content
                parts = clean_line.split("::")
                if len(parts) >= 2:
                    front = parts[0].strip()
                    back = parts[1].strip()

                    # Ensure front is at least '[[A]]' (5 chars) and back isn't empty
                    if len(front) >= 5 and back:
                        cleaned_lines.append(f"{front} :: {back}")

        return "\n".join(cleaned_lines).strip()

import logging
import re

from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_DIAGRAM
from domain.orchestrator.constants.user_prompts import USER_PROMPT_DIAGRAM
from domain.ports.agent import AgentPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class DiagramAgent(AgentPort):
    """
    Agent optimized for generating valid, noise-free Mermaid.js diagrams.
    Aggressively strips prose and sanitizes syntax to prevent Obsidian parse errors.
    """

    def __init__(self, llm_provider: LLMProviderPort):
        self.llm_provider = llm_provider
        self.system_prompt = SYSTEM_PROMPT_DIAGRAM

    async def run(self, content: str) -> str:
        logger.info("Running DiagramAgent: Visual Architecture Mapping...")

        user_prompt = USER_PROMPT_DIAGRAM.format(xml_content=content)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm_provider.generate(messages=messages)
            raw_content = self._to_string(response)

            # 1. Strict Extraction: Get ONLY the content inside ```mermaid blocks
            mermaid_match = re.search(r"```mermaid\s*([\s\S]*?)\s*```", raw_content)

            if not mermaid_match:
                # Fallback: check if the model forgot the fences but provided the graph
                graph_match = re.search(
                    r"(graph\s+(?:LR|TD|BT|RL)[\s\S]*)", raw_content
                )
                if graph_match:
                    clean_mermaid = graph_match.group(1).strip()
                else:
                    logger.warning("No Mermaid graph found in LLM response.")
                    return "> [!error] Mermaid Generation Failed: No graph detected."
            else:
                clean_mermaid = mermaid_match.group(1).strip()

            # 2. Hard-Sanitize the extracted Mermaid code
            final_mermaid = self._sanitize_mermaid(clean_mermaid)

            # 3. Return only the wrapped block
            return f"```mermaid\n{final_mermaid}\n```"

        except Exception as e:
            logger.error(f"❌ Error in DiagramAgent: {e}")
            return f"> [!caution] Diagram Generation Error: {type(e).__name__}"

    def _to_string(self, response) -> str:
        if isinstance(response, dict):
            return response.get("content", "").strip()
        return str(response).strip()

    def _sanitize_mermaid(self, text: str) -> str:
        """
        Deep-cleans Mermaid syntax to prevent the common 'TAGEND' or 'NODE_STRING' errors.
        """
        # A. Remove all labels between pipes |label| (Main cause of syntax failure)
        # We replace them with simple arrows to guarantee a valid graph
        text = re.sub(r"\|.*?\|", "", text)

        # B. Sanitize Node text [brackets]: Keep only Alphanumeric and spaces
        text = re.sub(
            r"\[(.*?)\]",
            lambda m: "[" + re.sub(r"[^a-zA-Z0-9 ]", "", m.group(1)) + "]",
            text,
        )

        # C. Sanitize Subgraph titles: No special chars, underscores allowed
        text = re.sub(
            r"subgraph (.*)",
            lambda m: "subgraph " + re.sub(r"[^a-zA-Z0-9_ ]", "", m.group(1)),
            text,
        )

        # D. Generic cleanup of double-arrows or malformed link remnants
        text = text.replace("-->-", "-->").replace("--->", "-->").replace("->", "-->")

        # E. Final safety: Remove any lines that don't belong to Mermaid syntax
        valid_keywords = ("graph", "subgraph", "end", "style", "click", "-->")
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip().startswith(valid_keywords) or "-->" in line
        ]

        return "\n".join(lines).strip()

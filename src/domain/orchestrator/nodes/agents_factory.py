import logging

from domain.models.agent import AgentConfig
from domain.orchestrator.constants.system_prompts import PROMPT_MAP
from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.orchestrator.registry import VALID_ROUTING_KEYS
from domain.orchestrator.utils.parsers.base_parser import BaseParser
from domain.orchestrator.utils.parsers.markdown_table_parser import MarkdownTableParser
from domain.orchestrator.utils.parsers.mermeid_diagram_parser import (
    MermaidDiagramParser,
)
from domain.orchestrator.utils.parsers.text_parser import TextParser
from domain.orchestrator.utils.parsers.xml_parser import XMLContentParser
from domain.ports.file_system import FileSystemPort
from domain.ports.llm_provider import LLMProviderPort

logger = logging.getLogger(__name__)


class WorkerNodeFactory:
    """
    Factory responsible for instantiating specialized WorkerNodes.
    Maps agent IDs to system prompts, parsers, and file system access.
    """

    def __init__(
        self, llm_provider: LLMProviderPort, fs: FileSystemPort | None = None
    ) -> None:
        self.llm_provider = llm_provider

        self.fs: FileSystemPort | None = fs

    def create(self, agent_id: str) -> BaseWorkerNode:
        if agent_id not in VALID_ROUTING_KEYS:
            logger.error(f"❌ Attempted to create unknown agent: {agent_id}")
            raise ValueError(
                f"Agent ID '{agent_id}' is not registered in VALID_ROUTING_KEYS."
            )

        system_prompt = PROMPT_MAP.get(
            agent_id,
            "You are a technical assistant specializing in XML document refinement.",
        )

        logger.info(f"🏗️ Factory: Creating worker instance for '{agent_id}'")

        parser_map = {
            "atomicity_agent": XMLContentParser(),
            "reorder_agent": XMLContentParser(),
            "tag_agent": XMLContentParser(),
            "matrix_agent": MarkdownTableParser(),
            "diagram_agent": MermaidDiagramParser(),
            "flashcards_agent": MarkdownTableParser(),
            "case_study_agent": TextParser(),
            "content_agent": TextParser(),
            "naming_agent": TextParser(),
        }

        parser = parser_map.get(agent_id, BaseParser())

        config = AgentConfig(
            agent_id=agent_id,
            system_prompt=system_prompt,
            llm_provider=self.llm_provider,
            examples=[],
            temperature=0.0,
            max_tokens=500,
            stop_sequences=[],
            content_threshold=2000,
            metadata={},
        )

        return BaseWorkerNode(
            config=config,
            parser=parser,
            fs=self.fs,
        )

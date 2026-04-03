import logging
import uuid
import re
from pathlib import Path
from typing import Any

from domain.models.enums import MessageRole, StopReason
from domain.models.llm_provider_model import LLMInferenceConfig, LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.orchestrator.tool_registry import ToolRegistry
from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_PLANNER
from domain.utils.text_utils import split_markdown_by_headers

logger = logging.getLogger(__name__)


class PlannerNode(BaseWorkerNode):
    """
    PlannerNode plans the lifecycle for all files found in folder_path.
    Implements semantic chunking ONLY for content-heavy agents (Atomicity, Summarizer).
    Naming and Classification happen once per file.
    """

    def __init__(
        self,
        config: Any,
        max_iterations: int,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(config, max_iterations, tool_registry)

    async def __call__(self, state: AgentState) -> StateUpdate:
        folder_path = Path(state.folder_path).resolve()
        logger.info(f"📝 Planning for workspace: {folder_path}")
        
        # 1. Explorar archivos
        exclude = ["xml", "summaries", "PLAN.md", "fixed_files"]
        files = [f for f in folder_path.glob("*.md") if f.name not in exclude]
        
        if not files:
            logger.warning(f"⚠️ No markdown files found in {folder_path}")
            return StateUpdate(stop_reason=StopReason.END, final_response="No files found.")

        # 2. Generar lista de tareas manual para control total del flujo
        # Eliminamos la dependencia del LLM para la estructura del plan para garantizar PERSISTENCIA y DETERMINISMO.
        plan_lines = []
        for f in files:
            content = f.read_text()
            # Naming and Classification happen ONCE
            plan_lines.append(f"- [ ] {f.name} -> naming_agent -> rename_file")
            plan_lines.append(f"- [ ] {f.name} -> classifier_agent -> classify_domain")
            
            # Atomicity and Summarizer support chunking
            if len(content) > 5000:
                chunks = split_markdown_by_headers(content, max_chars=5000)
                for i, _ in enumerate(chunks, 1):
                    plan_lines.append(f"- [ ] {f.name} (Part {i}) -> atomicity_agent -> xml_conversion")
                    plan_lines.append(f"- [ ] {f.name} (Part {i}) -> summarizer_agent -> hierarchical_summary")
            else:
                plan_lines.append(f"- [ ] {f.name} -> atomicity_agent -> xml_conversion")
                plan_lines.append(f"- [ ] {f.name} -> summarizer_agent -> hierarchical_summary")
            
            # Tagging happens ONCE
            plan_lines.append(f"- [ ] {f.name} -> tag_agent -> generate_metadata")

        cleaned_content = "\n".join(plan_lines)

        # Save to PLAN.md (PERSISTENCE)
        if self.tool_registry:
            self.tool_registry.execute("write_file", path="PLAN.md", content=cleaned_content)
        
        logger.info(f"✅ PLAN.md written with {len(plan_lines)} deterministic tasks.")

        return StateUpdate(
            content=cleaned_content,
            next_agent="supervisor",
            stop_reason=StopReason.CALL,
            metadata=self._create_metadata(state),
            iteration=state.iteration + 1,
        )

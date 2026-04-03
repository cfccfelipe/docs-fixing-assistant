import logging
import uuid
import re
from pathlib import Path
from typing import Any

from domain.models.enums import MessageRole, StopReason
from domain.models.llm_provider_model import LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_node import BaseNode
from domain.orchestrator.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class SupervisorNode(BaseNode):
    """
    Lead Architect: Orchestrates tasks deterministically by syncing PLAN.md.
    Maintains persistence and ensures sequential progress.
    """

    def __init__(self, config: Any, max_iterations: int, tool_registry: ToolRegistry | None = None) -> None:
        super().__init__(config, max_iterations)
        self.tool_registry = tool_registry

    async def __call__(self, state: AgentState) -> StateUpdate:
        # 1. Sync state with PLAN.md
        content = ""
        if self.tool_registry:
            try:
                content = self.tool_registry.execute("read_file", path="PLAN.md")
            except Exception:
                content = state.content

        if not content:
            logger.info("ℹ️ No plan found. Routing to planner.")
            return StateUpdate(next_agent="planner_agent", stop_reason=StopReason.CALL)

        lines = content.splitlines()
        
        # 2. Find first incomplete task
        next_idx = -1
        for i, line in enumerate(lines):
            if "- [ ]" in line:
                next_idx = i
                break
        
        if next_idx != -1:
            task_line = lines[next_idx].strip()
            
            # Robust extraction of filename and agent ID
            match = re.search(r'-\s*\[\s?\]\s*(.*?\.md(?:\s*\(Part\s*\d+\))?)\s*->\s*(\w+)', task_line)
            
            if match:
                raw_file_name = match.group(1).strip()
                next_agent = match.group(2).strip()
                
                # 🎯 PROGRESSION: Mark as DONE immediately before routing to ensure no loops.
                # In a deterministic flow, we assume the agent will try its best.
                lines[next_idx] = task_line.replace("- [ ]", "- [x]")
                new_content = "\n".join(lines)
                if self.tool_registry:
                    self.tool_registry.execute("write_file", path="PLAN.md", content=new_content)
                
                # Strip "(Part X)" for actual file access
                actual_file_name = re.sub(r'\s*\(Part\s*\d+\)', '', raw_file_name).strip()
                
                logger.info(f"🎯 [Deterministic] Routing {next_agent} for {actual_file_name} (Task {next_idx + 1})")
                
                return StateUpdate(
                    content=new_content,
                    current_file=actual_file_name,
                    next_agent=next_agent,
                    next_task=task_line,
                    stop_reason=StopReason.CALL,
                    iteration=state.iteration + 1
                )

        # 3. Completion
        logger.info("🏁 All tasks complete.")
        return StateUpdate(stop_reason=StopReason.END, final_response="Execution complete.")

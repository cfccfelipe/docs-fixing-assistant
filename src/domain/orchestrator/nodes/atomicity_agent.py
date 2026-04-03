import logging
from typing import Any
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode

logger = logging.getLogger(__name__)

class AtomicityAgent(BaseWorkerNode):
    """
    Agent responsible for converting Markdown to XML structures.
    """
    async def __call__(self, state: AgentState) -> StateUpdate:
        logger.info(f"⚛️ AtomicityAgent: Structuring {state.current_file}")
        
        # 1. Read the file content
        content = self.tool_registry.execute("read_file", path=state.current_file)
        
        # 2. Convert to XML (simplified representation for now)
        xml_content = f"<document><title>{state.current_file}</title><content>{content}</content></document>"
        
        # 3. Save to xml/ directory
        # Ensure xml/ exists
        import os
        if not os.path.exists("xml"):
            os.makedirs("xml")
            
        xml_path = f"xml/{state.current_file.replace('.md', '.xml')}"
        self.tool_registry.execute("write_file", path=xml_path, content=xml_content)
        
        return StateUpdate(
            task_result=f"XML created at {xml_path}",
            next_agent="supervisor",
            stop_reason=None,
            metadata=self._create_metadata(state)
        )

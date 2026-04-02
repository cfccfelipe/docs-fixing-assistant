import logging
import uuid
from typing import Any

from domain.models.enums import MessageRole
from domain.models.llm_provider_model import LLMInferenceConfig, LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_worker_node import BaseWorkerNode
from domain.orchestrator.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class PlannerNode(BaseWorkerNode):
    """
    Specialized node for planning.
    It lists files before generating the prompt to ensure the LLM has context.
    """

    def __init__(
        self,
        config: Any,
        max_iterations: int,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(config, max_iterations, tool_registry)

    async def __call__(self, state: AgentState) -> StateUpdate:
        # 1. Explorar archivos antes de llamar al LLM
        files = []
        if self.tool_registry:
            try:
                # Usamos la tool directamente
                files_data = self.tool_registry.execute("list_files", folder_path=state.folder_path)
                
                # Manejar tanto lista de Paths como string (según la tool)
                if isinstance(files_data, list):
                    files = [getattr(f, "name", str(f)) for f in files_data]
                else:
                    files = [f.strip() for f in str(files_data).split("\n") if f.strip()]
            except Exception as e:
                logger.error(f"Error listing files for planner: {e}")

        # 2. Formatear el prompt con la información real
        sys_prompt = self.config.system_prompt.format(
            path=state.folder_path,
            files=", ".join(files) if files else "No markdown files found."
        )

        request = LLMRequest(
            messages=[
                MessageDefinition(
                    id=uuid.uuid4(),
                    role=MessageRole.SYSTEM,
                    content_history=sys_prompt,
                ),
                MessageDefinition(
                    id=uuid.uuid4(),
                    role=MessageRole.USER,
                    content_history=f"Context: {state.content or 'Empty plan'}",
                ),
            ],
            tools_registry=self._get_tools_definitions(),
            inference=LLMInferenceConfig(
                temperature=getattr(self.config, "temperature", 0.0),
                max_tokens=getattr(self.config, "max_tokens", 1024),
            ),
        )

        response: LLMResponse = await self._execute_inference(request)
        logger.info(f"Planner LLM Output: {response.content}")
        from domain.models.enums import StopReason

        # 3. El planner no suele llamar a tools, solo escribe el plan en content
        return StateUpdate(
            content=response.content,
            next_agent="supervisor",
            stop_reason=StopReason.CALL,
            metadata=self._create_metadata(state, response),
            iteration=state.iteration + 1,
        )

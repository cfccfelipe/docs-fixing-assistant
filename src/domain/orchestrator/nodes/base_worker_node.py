import logging
import uuid
from typing import Any

from domain.models.enums import MessageRole, StopReason
from domain.models.llm_provider_model import LLMInferenceConfig, LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.nodes.base_node import BaseNode
from domain.orchestrator.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class BaseWorkerNode(BaseNode):
    def __init__(
        self,
        config: Any,
        max_iterations: int,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        super().__init__(config, max_iterations)
        self.tool_registry = tool_registry

    async def __call__(self, state: AgentState) -> StateUpdate:
        delta = self._get_execution_delta(state)
        if "stop_reason" in delta:
            return StateUpdate(metadata=self._create_metadata(state), **delta)

        request = LLMRequest(
            messages=[
                MessageDefinition(
                    id=uuid.uuid4(),
                    role=MessageRole.SYSTEM,
                    content_history=self.config.system_prompt,
                ),
                MessageDefinition(
                    id=uuid.uuid4(),
                    role=MessageRole.USER,
                    content_history=f"Task: {state.next_task}\nContext: {state.content}",
                ),
            ],
            tools_registry=self._get_tools_definitions(),
            inference=LLMInferenceConfig(
                temperature=getattr(self.config, "temperature", 0.0),
                max_tokens=getattr(self.config, "max_tokens", 1024),
            ),
        )

        response: LLMResponse = await self._execute_inference(request)

        # FIX 1: Validación de ToolRegistry y acceso a tool_calls (no solo IDs)
        if response.tool_calls and self.tool_registry:
            return await self._handle_infrastructure_calls(state, response)

        return StateUpdate(
            content=response.content,
            next_agent="supervisor",
            stop_reason=StopReason.CALL,
            metadata=self._create_metadata(state, response),
            iteration=state.iteration + 1,
        )

    async def _handle_infrastructure_calls(
        self, state: AgentState, response: LLMResponse
    ) -> StateUpdate:
        results = []
        errors = []

        # FIX 2: Type Guard para asegurar que tool_registry existe antes de execute
        if not self.tool_registry:
            return StateUpdate(
                error_message="ToolRegistry missing during tool call attempt.",
                stop_reason=StopReason.ERROR,
                metadata=self._create_metadata(state, response),
            )

        for call in response.tool_calls:
            try:
                # Ahora 'call' es un objeto ToolCall con .name y .arguments
                result = self.tool_registry.execute(call.name, **call.arguments)
                results.append(f"Tool {call.name} output: {result}")
            except Exception as e:
                error_msg = f"Error in {call.name}: {str(e)}"
                logger.error(f"🚨 {error_msg}")
                errors.append(error_msg)

        return StateUpdate(
            content="\n".join(results),
            error_message="; ".join(errors) if errors else None,
            next_agent="supervisor",
            stop_reason=StopReason.ERROR if errors else StopReason.CALL,
            metadata=self._create_metadata(state, response),
            iteration=state.iteration + 1,
        )

    def _get_tools_definitions(self) -> list[Any]:
        if not self.tool_registry:
            return []
        return self.tool_registry.get_all_metadata()

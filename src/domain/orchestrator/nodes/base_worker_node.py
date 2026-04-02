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

        messages = [
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
        ]

        task_results = []
        node_iterations = 0
        max_node_iters = 5 # Prevent infinite internal loops

        while node_iterations < max_node_iters:
            node_iterations += 1
            request = LLMRequest(
                messages=messages,
                tools_registry=self._get_tools_definitions(),
                inference=LLMInferenceConfig(
                    temperature=getattr(self.config, "temperature", 0.0),
                    max_tokens=getattr(self.config, "max_tokens", 1024),
                ),
            )

            response: LLMResponse = await self._execute_inference(request)
            
            # Si no hay tool calls, terminamos el bucle interno
            if not response.tool_calls or not self.tool_registry:
                return StateUpdate(
                    task_result="\n".join(task_results) if task_results else response.content,
                    next_agent="supervisor",
                    stop_reason=StopReason.CALL,
                    metadata=self._create_metadata(state, response),
                    iteration=state.iteration + 1,
                )

            # Ejecutar herramientas
            results, errors = await self._execute_tools(response.tool_calls)
            task_results.extend(results)
            
            # Actualizar historial para la siguiente vuelta
            # 1. Agregar la respuesta del asistente (con las tool_calls)
            messages.append(MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.ASSISTANT,
                content_history=response.content,
                tool_calls=response.tool_calls
            ))
            # 2. Agregar los resultados de las herramientas
            for i, res in enumerate(results):
                messages.append(MessageDefinition(
                    id=uuid.uuid4(),
                    role=MessageRole.TOOL,
                    content_history=res,
                    # Relacionar con el ID de la llamada si es posible
                ))

            if errors:
                return StateUpdate(
                    task_result="\n".join(task_results),
                    error_message="; ".join(errors),
                    next_agent="supervisor",
                    stop_reason=StopReason.ERROR,
                    metadata=self._create_metadata(state, response),
                    iteration=state.iteration + 1,
                )

        return StateUpdate(
            task_result="\n".join(task_results),
            error_message="Internal node iteration limit reached.",
            next_agent="supervisor",
            stop_reason=StopReason.ERROR,
            metadata=self._create_metadata(state),
            iteration=state.iteration + 1,
        )

    async def _execute_tools(self, tool_calls: list[ToolCall]) -> tuple[list[str], list[str]]:
        results = []
        errors = []
        if not self.tool_registry:
            return [], ["ToolRegistry missing"]

        for call in tool_calls:
            try:
                result = self.tool_registry.execute(call.name, **call.arguments)
                results.append(f"Tool {call.name} output: {result}")
            except Exception as e:
                error_msg = f"Error in {call.name}: {str(e)}"
                logger.error(f"🚨 {error_msg}")
                errors.append(error_msg)
        return results, errors

    def _get_tools_definitions(self) -> list[Any]:
        if not self.tool_registry:
            return []
        return self.tool_registry.get_all_metadata()

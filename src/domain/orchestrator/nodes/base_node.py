import logging
import re
import uuid
from dataclasses import replace
from typing import Any

from domain.models.enums import MessageRole, StopReason
from domain.models.llm_provider_model import LLMInferenceConfig, LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateMetadata, StateUpdate
from domain.orchestrator.constants import messages as msg
from domain.ports.llm_provider import LLMProviderPort
from domain.ports.node_port import NodePort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import OrchestrationException
from domain.utils.response_parser import ResponseParser

logger = logging.getLogger(__name__)


class BaseNode(NodePort):
    """
    Core execution engine for agents.
    Handles context filtering, JSON auto-healing, and hallucination cleaning.
    """

    def __init__(self, config: Any, max_iterations: int) -> None:
        self.config: Any = config
        self.name: str = config.agent_id
        self.llm_provider: LLMProviderPort = config.llm_provider
        self.max_iterations: int = max_iterations

    @handle_errors(exception_cls=OrchestrationException, layer="Domain")
    async def __call__(self, state: AgentState) -> StateUpdate:
        """Standardized execution flow with context filtering."""
        delta = self._get_execution_delta(state)

        if delta.get("stop_reason") == StopReason.END:
            return StateUpdate(
                folder_path=state.folder_path,
                iteration=state.iteration,
                metadata=self._create_metadata(state),
                **delta,
            )

        # Filter metadata out of state dict to avoid tempting the model
        state_dict = {k: v for k, v in vars(state).items() if k != "metadata"}

        plan_display = (
            state.content.strip()
            if state.content and state.content.strip()
            else "EMPTY - Project initialization phase."
        )

        format_kwargs = {
            "state": state_dict,
            "current_state": state_dict,
            "plan_content": plan_display,
        }

        messages = [
            MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.SYSTEM,
                content_history=getattr(
                    self.config, "system_prompt", "You are a precise assistant."
                ).format(**format_kwargs),
            ),
            MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.USER,
                content_history=state.user_prompt,
            ),
        ]

        request = LLMRequest(messages=messages)
        response = await self._execute_inference(request)
        parsed_content = self._parse_response(response, state)

        return StateUpdate(
            folder_path=state.folder_path,
            metadata=self._create_metadata(state, response),
            **(delta | parsed_content),
        )

    async def _execute_inference(self, request: LLMRequest) -> LLMResponse:
        """Executes inference with 'Assistant Prefilling' and Surgical Cleaning."""
        fmt = getattr(self.config, "output_format", "json").lower()
        prefill = "{" if fmt == "json" else ""

        updated_messages = list(request.messages)
        if prefill:
            updated_messages.append(
                MessageDefinition(
                    id=uuid.uuid4(), role=MessageRole.ASSISTANT, content_history=prefill
                )
            )

        new_inference = LLMInferenceConfig(
            temperature=getattr(self.config, "temperature", 0.0),
            max_tokens=getattr(self.config, "max_tokens", 512),
            stop=["}\n", "###", "User:"],
        )

        final_request = replace(
            request, messages=updated_messages, inference=new_inference
        )
        response: LLMResponse = await self.llm_provider(final_request)

        if prefill and response.content:
            content = response.content.strip()

            # 1. Resolve duplicated braces
            if not content.startswith(prefill):
                content = prefill + content
            content = content.replace('{" {', "{").replace("{{", "{")

            # 2. Remove hallucinated metadata
            if '"metadata"' in content:
                content = re.sub(
                    r'"metadata"\s*:\s*\{.*?\}', "", content, flags=re.DOTALL
                )
                content = content.replace(", ,", ",").replace(",,", ",")
                content = re.sub(r",\s*}", "}", content)
                content = re.sub(r"{\s*,", "{", content)

            # 3. Ensure structural integrity
            content = content.strip()
            if not content.endswith("}"):
                content += "}"

            response = replace(response, content=content)

        return response

    def _parse_response(
        self, response: LLMResponse, state: AgentState
    ) -> dict[str, Any]:
        """Standardized JSON/TXT parsing via ResponseParser."""
        if response.tool_calls:
            return {
                "tool_calls": response.tool_calls,
                "stop_reason": StopReason.CALL,
                "content": response.content,
            }

        fmt = getattr(self.config, "output_format", "json").lower()
        if fmt == "json":
            parsed = ResponseParser.parse_json(response.content)

            if parsed and isinstance(parsed, dict):
                raw_reason = parsed.get("stop_reason")
                if raw_reason:
                    try:
                        parsed["stop_reason"] = StopReason(str(raw_reason).upper())
                    except (ValueError, AttributeError):
                        parsed["stop_reason"] = StopReason.ERROR
                else:
                    # Si no hay stop_reason explícito
                    if not state.content or not state.content.strip():
                        parsed["stop_reason"] = StopReason.CALL
                        parsed["next_agent"] = "planner_agent"
                    else:
                        parsed["stop_reason"] = StopReason.CALL
                return parsed

            return {
                "error_message": f"JSON Failure. Raw: {response.content[:100]}",
                "parsing_failed": True,
                "stop_reason": StopReason.ERROR,
            }

        return {
            "content": ResponseParser.parse_txt(response.content),
            "stop_reason": StopReason.CALL,
        }

    def _create_metadata(
        self, state: AgentState, response: LLMResponse | None = None
    ) -> StateMetadata:
        """Telemetry accumulation logic."""
        current_md = getattr(state, "metadata", None) or StateMetadata()
        if not response:
            return replace(current_md, last_agent_key=self.name)

        return replace(
            current_md,
            last_agent_key=self.name,
            model_name=response.model,
            input_tokens=current_md.input_tokens + (response.input_tokens or 0),
            output_tokens=current_md.output_tokens + (response.output_tokens or 0),
            token_usage=current_md.token_usage + (response.token_usage or 0),
            total_duration_ms=current_md.total_duration_ms
            + (response.total_duration_ms or 0),
        )

    def _get_execution_delta(self, state: AgentState) -> dict[str, Any]:
        """Circuit breaker and completion logic."""
        current_iter = state.iteration if isinstance(state.iteration, int) else 0

        # End if max iterations reached
        if current_iter >= self.max_iterations:
            return {
                "stop_reason": StopReason.END,
                "error_message": f"Circuit Breaker: {self.max_iterations} iters reached.",
                "final_response": msg.MSG_CIRCUIT_BREAKER_USER_FEEDBACK.format(
                    user_prompt=state.user_prompt, max_iters=self.max_iterations
                ),
            }

        # Inicialización si plan vacío
        if not state.content or not state.content.strip():
            return {
                "stop_reason": StopReason.CALL,
                "next_agent": "planner_agent",
                "final_response": "Supervisor: Routing to planner for initialization.",
            }

        return {"iteration": current_iter + 1}

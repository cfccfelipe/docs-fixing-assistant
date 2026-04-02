import logging
import uuid

from domain.models.enums import MessageRole, StopReason
from domain.models.llm_provider_model import LLMRequest, LLMResponse
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateUpdate
from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_SUPERVISOR
from domain.orchestrator.constants.user_prompts import USER_PROMPT_SUPERVISOR
from domain.orchestrator.nodes.base_node import BaseNode

logger = logging.getLogger(__name__)


class SupervisorNode(BaseNode):
    """
    Lead Architect & Intent Router.
    Orchestrates the workflow by analyzing the Project Plan (content).
    """

    async def __call__(self, state: AgentState) -> StateUpdate:
        """Standardized execution flow with redundant key mapping."""
        delta = self._get_execution_delta(state)

        if delta.get("stop_reason") == StopReason.END:
            return StateUpdate(
                folder_path=state.folder_path,
                metadata=self._create_metadata(state),
                **delta,
            )

        # Prepare context for prompts
        plan_display = (
            state.content.strip()
            if state.content and state.content.strip()
            else "EMPTY - Initializing..."
        )

        format_kwargs = {
            "current_state": state,
            "state": state,
            "plan_content": plan_display,
        }

        try:
            sys_prompt = SYSTEM_PROMPT_SUPERVISOR.format(**format_kwargs)
            usr_prompt = USER_PROMPT_SUPERVISOR.format(**format_kwargs)
        except (KeyError, AttributeError) as e:
            logger.error(f"❌ Prompt Format Error: {e}")
            return self._handle_parsing_failure(
                state, LLMResponse(content=f"FormatError: {e}", model="system")
            )

        request = LLMRequest(
            messages=[
                MessageDefinition(
                    id=uuid.uuid4(), role=MessageRole.SYSTEM, content_history=sys_prompt
                ),
                MessageDefinition(
                    id=uuid.uuid4(), role=MessageRole.USER, content_history=usr_prompt
                ),
            ]
        )

        response = await self._execute_inference(request)
        parsed_data = self._parse_response(response, state)

        return self._build_routing_update(state, parsed_data, response, delta)

    def _build_routing_update(self, state, parsed, response, delta) -> StateUpdate:
        if parsed.get("parsing_failed"):
            return self._handle_parsing_failure(state, response)

        raw_reason = parsed.get("stop_reason", StopReason.CALL)
        next_agent = parsed.get("next_agent")
        next_task = parsed.get("next_task")

        # Caso especial: plan vacío -> planner_agent
        if not state.content or not state.content.strip():
            next_agent = "planner_agent"
            stop_reason = StopReason.CALL
        # Caso especial: tareas pendientes -> coder_agent
        elif "- [ ]" in state.content:
            next_agent = "coder_agent"
            stop_reason = StopReason.CALL
            # Extraer la primera tarea pendiente literal
            pending_lines = [
                line
                for line in state.content.splitlines()
                if line.strip().startswith("- [ ]")
            ]
            if pending_lines:
                next_task = pending_lines[0].replace("- [ ]", "").strip()
        # Caso especial: todas las tareas completadas -> END
        elif "- [x]" in state.content and "- [ ]" not in state.content:
            next_agent = None
            stop_reason = StopReason.END
        elif next_agent is None and raw_reason != StopReason.ERROR:
            stop_reason = StopReason.END
        else:
            stop_reason = (
                raw_reason if isinstance(raw_reason, StopReason) else StopReason.CALL
            )

        final_resp = parsed.get("final_response")
        if stop_reason == StopReason.END and not final_resp:
            final_resp = "Project plan execution finalized."
        elif (
            stop_reason == StopReason.CALL
            and next_agent == "planner_agent"
            and not final_resp
        ):
            final_resp = "Supervisor: Routing to planner for initialization."

        return StateUpdate(
            folder_path=state.folder_path,
            iteration=delta.get("iteration", state.iteration + 1),
            next_agent=next_agent,
            next_task=next_task,
            stop_reason=stop_reason,
            error_message=parsed.get("error_message") or state.error_message,
            metadata=self._create_metadata(state, response),
            final_response=final_resp,
        )

    def _handle_parsing_failure(self, state, response) -> StateUpdate:
        clean_content = response.content.strip() if response.content else "None"
        logger.error("🚨 Supervisor Parsing Failure: %s", clean_content)

        # Fallback: si el plan está vacío, siempre ir al planner
        if not state.content or not state.content.strip():
            return StateUpdate(
                folder_path=state.folder_path,
                stop_reason=StopReason.CALL,
                next_agent="planner_agent",
                final_response="Supervisor: Routing to planner for initialization.",
                metadata=self._create_metadata(state, response),
            )

        return StateUpdate(
            folder_path=state.folder_path,
            stop_reason=StopReason.ERROR,
            error_message=f"JSON Failure. Raw: {clean_content[:50]}...",
            metadata=self._create_metadata(state, response),
        )

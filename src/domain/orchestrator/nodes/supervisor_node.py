import logging
from typing import Any

# Models & Ports
from domain.models.llm_provider import LLMInferenceConfig
from domain.models.state import AgentState, StopReason
from domain.orchestrator.constants import messages as msg

# Assuming SYSTEM_PROMPT_SUPERVISOR_8B is updated to expect the new state
from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_SUPERVISOR_8B
from domain.orchestrator.nodes.base_worker import BaseWorker
from domain.ports.llm_provider import LLMProviderPort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import OrchestrationException

# Utils
from domain.utils.json_parser import JsonParser

logger = logging.getLogger(__name__)


class SupervisorNode(BaseWorker):
    """
    Advanced Orchestrator for LangGraph.
    Uses 'plan.md' as the source of truth to coordinate atomic tasks.
    """

    def __init__(self, llm_provider: LLMProviderPort) -> None:
        super().__init__(name="supervisor")
        self.llm_provider = llm_provider
        self.config = LLMInferenceConfig(temperature=0.0, max_tokens=4096)
        self.max_iterations = 6

    @handle_errors(exception_cls=OrchestrationException, layer="Domain")
    async def __call__(self, state: AgentState) -> dict[str, Any]:
        # 1. Circuit Breaker
        current_iter = state.iteration or 0
        if current_iter >= self.max_iterations:
            logger.error(msg.MSG_MAX_ITERATIONS)
            return {
                "stop_reason": StopReason.ERROR,
                "error_message": msg.MSG_MAX_ITERATIONS,
                "metadata": self._create_metadata(
                    state, content_info="Max iterations reached"
                ),
            }

        # 2. LLM Inference
        # Formatting the prompt with the complete AgentState
        prompt = SYSTEM_PROMPT_SUPERVISOR_8B.format(current_state=state)
        response = await self.llm_provider.generate(
            messages=[{"role": "user", "content": prompt}],
            inference=self.config,
        )

        # 3. Robust Parsing
        raw_content = str(response.get("content", ""))
        parsed = JsonParser.parse(raw_content)

        if not parsed:
            error_data = JsonParser.to_agent_error(
                "Invalid JSON structure in Supervisor response."
            )
            error_data["metadata"] = self._create_metadata(
                state, content_info="Parsing failed"
            )
            return error_data

        # 4. Decision Extraction & Enum Normalization
        # We ensure stop_reason is a valid StopReason Enum
        try:
            raw_reason = str(parsed.get("stop_reason", "ERROR")).upper()
            stop_reason = StopReason(raw_reason)
        except ValueError:
            stop_reason = StopReason.ERROR

        next_agent = parsed.get("next_agent")
        next_task = parsed.get("next_task")
        error_msg = parsed.get("error_message")

        # 5. Metadata Update
        new_metadata = self._create_metadata(
            state,
            content_info=f"Decision: {stop_reason} -> {next_agent}",
            additional_tokens=response.get("token_usage", 0),
        )

        # 6. Output Branching

        # Case A: Finish
        if stop_reason == StopReason.END:
            logger.info("🏁 %s", msg.MSG_WORKFLOW_FINALIZED)
            return {
                "stop_reason": StopReason.END,
                "next_agent": None,
                "next_task": None,
                "metadata": new_metadata,
            }

        # Case B: Error
        if stop_reason == StopReason.ERROR:
            logger.error("🚨 Supervisor Error: %s", error_msg)
            return {
                "stop_reason": StopReason.ERROR,
                "error_message": error_msg,
                "metadata": new_metadata,
            }

        # Case C: Call
        logger.info(
            "Iter: %s | Next: %s | Task: %s", current_iter, next_agent, next_task
        )

        return {
            "next_agent": next_agent,
            "next_task": next_task,
            "iteration": current_iter + 1,
            "stop_reason": StopReason.CALL,
            "metadata": new_metadata,
        }

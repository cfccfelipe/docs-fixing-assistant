import logging
import os

from domain.models.agent import AgentConfig
from domain.models.llm_provider import LLMInferenceConfig
from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.nodes.base_worker import BaseWorker
from domain.ports.content_parser import ContentParserPort
from domain.ports.file_system import FileSystemPort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import OrchestrationException

logger = logging.getLogger(__name__)


class BaseWorkerNode(BaseWorker):
    """
    Specialized worker node for technical editing and MCP tool integration.
    Extends BaseWorker with LLM prompt construction, error-driven correction,
    confidence scoring, and optional validation via a parser.
    """

    def __init__(
        self,
        config: AgentConfig,
        parser: ContentParserPort | None = None,
        fs: FileSystemPort | None = None,
    ) -> None:
        super().__init__(name=config.agent_id)
        self.config = config
        self.parser = parser
        self.fs: FileSystemPort | None = fs

    @handle_errors(exception_cls=OrchestrationException, layer="Domain")
    async def __call__(self, state: AgentState) -> NodeResponse:
        current_content: str = (state.content or "").strip()
        if state.path and self.fs:
            if os.path.isdir(state.path):
                files = self.fs.list_files(state.path)
                loaded_contents = []
                for f in files:
                    loaded_contents.append(self.fs.read_file(f))
                current_content = "\n\n".join(loaded_contents)
            else:
                current_content = self.fs.read_file(state.path)

        user_feedback: str = state.user_feedback or ""
        metadata: StateMetadata = state.metadata or StateMetadata()

        effective_examples = self.config.examples[:4]

        prev_errors: list[str] = metadata.validation_errors or []
        error_context = (
            f"\n\n[FIX REQUIRED - PREVIOUS ERRORS]:\n{'; '.join(prev_errors)}"
            if prev_errors
            else ""
        )

        requires_summary: bool = len(current_content) > self.config.content_threshold
        system_prompt: str = self.config.system_prompt
        if requires_summary:
            system_prompt += (
                "\n\n[WARNING]: Content exceeds threshold. Provide a summary of "
                "technical changes instead of the full content."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            *effective_examples,
            {
                "role": "user",
                "content": f"### SOURCE:\n{current_content}{error_context}\n\n### TASK:\n{user_feedback}",
            },
        ]

        inference_params = LLMInferenceConfig(
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stop=self.config.stop_sequences,
            presence_penalty=0.1,
            seed=42,
        )

        logger.info(
            f"Agent [{self.config.agent_id}] invoked. Mode: {'Summary' if requires_summary else 'Edit'}"
        )

        response: dict = await self.config.llm_provider.generate(
            messages=messages,
            inference=inference_params,
            tools=self.config.metadata.get("tools") if self.config.metadata else None,
        )

        new_content: str = str(response.get("content") or current_content)
        stop_reason: str = response.get("stop_reason", "completed")
        tool_calls: list = response.get("tool_calls", [])
        usage: dict = response.get("usage", {})

        confidence: float = (
            0.7
            if stop_reason == "length"
            else (0.3 if response.get("error_message") else 1.0)
        )

        validation_errors: list[str] = []
        if self.validator:
            state_for_validation = AgentState(
                user_feedback=state.user_feedback,
                content=new_content,
                evaluation_score=state.evaluation_score,
                active_agents=state.active_agents,
                results=state.results,
                iterations=state.iterations,
                metadata=state.metadata,
                path=state.path,  # ✅ mantener path en validación
            )
            validation_response: NodeResponse = await self.validator(
                state_for_validation
            )
            if validation_response.metadata:
                validation_errors = validation_response.metadata.validation_errors

        logger.info(
            f"Agent [{self.config.agent_id}] finished. Stop: {stop_reason}, "
            f"Tokens: {usage.get('total_tokens', 0)}, Confidence: {confidence}"
        )

        return NodeResponse(
            content=new_content,
            results=[
                f"Agent '{self.config.agent_id}' step finished (Stop: {stop_reason})."
            ],
            active_agents=["mcp_executor"] if tool_calls else [],
            iterations=1,
            evaluation_score=confidence,
            metadata=StateMetadata(
                last_agent=self.config.agent_id,
                token_usage=usage.get("total_tokens", 0),
                stop_reason=stop_reason,
                is_summary=requires_summary or (stop_reason == "length"),
                has_tool_calls=len(tool_calls) > 0,
                error_message=response.get("error_message", ""),
                validation_errors=validation_errors,
            ),
        )

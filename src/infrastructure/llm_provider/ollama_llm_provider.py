import logging
import uuid
from typing import Any

import ollama
from ollama._types import ChatResponse

from domain.models.llm_provider_model import (
    LLMInferenceConfig,
    LLMRequest,
    LLMResponse,
    OllamaConfig,
)
from domain.models.message_model import MessageDefinition
from domain.models.tool_model import ToolCall
from domain.ports.llm_provider import LLMProviderPort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import InfrastructureException

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMProviderPort):
    """
    Infrastructure adapter for the local Ollama service.
    Optimized for Llama 3.1 and JSON enforcement.
    """

    def __init__(self, config: OllamaConfig) -> None:
        self.config_llm: OllamaConfig = config

    @handle_errors(exception_cls=InfrastructureException, layer="Infrastructure")
    async def __call__(self, request: LLMRequest) -> LLMResponse:
        """Executes the inference request with native JSON support."""
        logger.debug(f"Executing Ollama request: {self.config_llm.model_id}")

        messages = self._map_messages(request.messages, request.tools_registry)
        tools = self._map_tools(request.tools_registry)
        options = self._prepare_options(request.inference)

        # Activar JSON Mode si corresponde
        output_format = ""
        is_json = "json" in str(getattr(self.config_llm, "output_format", "")).lower()
        if is_json or getattr(request.inference, "json_mode", False):
            output_format = "json"

        response: ChatResponse = ollama.chat(
            model=self.config_llm.model_id,
            messages=messages,
            tools=tools,
            options=options,
            format=output_format,
            stream=False,
        )

        return self._build_llm_response(response)

    def _prepare_options(self, inference: LLMInferenceConfig | None) -> dict[str, Any]:
        """Maps Domain config to Ollama's specific 'Options' schema."""
        target_config = inference or self.config_llm.inference
        raw_options = vars(target_config)

        if "max_tokens" in raw_options:
            raw_options["num_predict"] = raw_options.pop("max_tokens")

        allowed = {
            "num_predict",
            "top_k",
            "top_p",
            "temperature",
            "repeat_penalty",
            "seed",
            "stop",
            "num_ctx",
            "num_gpu",
            "mirostat",
            "tfs_z",
        }

        return {k: v for k, v in raw_options.items() if k in allowed}

    def _build_llm_response(self, response: ChatResponse) -> LLMResponse:
        resp = response.__dict__ if not isinstance(response, dict) else response
        message_obj = resp.get("message", {})

        if isinstance(message_obj, dict):
            content = message_obj.get("content", "")
            raw_calls = message_obj.get("tool_calls", [])
        else:
            content = getattr(message_obj, "content", "")
            raw_calls = getattr(message_obj, "tool_calls", [])

        in_t = resp.get("prompt_eval_count") or 0
        out_t = resp.get("eval_count") or 0

        # Asegurar que token_usage avance
        token_usage = in_t + out_t
        if token_usage == 0 and content:
            token_usage = 1

        return LLMResponse(
            model=resp.get("model", self.config_llm.model_id),
            content=(content or "").strip(),
            tool_calls=self._map_structured_calls(raw_calls),
            input_tokens=in_t,
            output_tokens=out_t,
            token_usage=token_usage,
            total_duration_ms=self._to_ms(resp.get("total_duration")),
            load_duration_ms=self._to_ms(resp.get("load_duration")),
            prompt_eval_duration_ms=self._to_ms(resp.get("prompt_eval_duration")),
            eval_duration_ms=self._to_ms(resp.get("eval_duration")),
        )

    def _map_structured_calls(self, raw_calls: list[Any] | None) -> list[ToolCall]:
        structured_calls: list[ToolCall] = []
        for t in raw_calls or []:
            if not t:
                continue
            t_dict = t if isinstance(t, dict) else dict(t)
            func = t_dict.get("function", t_dict)
            func_dict = func if isinstance(func, dict) else dict(func)
            name = func_dict.get("name", "")
            if name:
                structured_calls.append(
                    ToolCall(
                        id=str(t_dict.get("id", uuid.uuid4())),
                        name=str(name),
                        arguments=func_dict.get("arguments", {}),
                    )
                )
        return structured_calls

    def _to_ms(self, nanoseconds: Any) -> float:
        try:
            if nanoseconds is None:
                return 0.0
            return float(nanoseconds) / 1_000_000.0
        except (TypeError, ValueError):
            return 0.0

    def _map_messages(
        self, chat_messages: list[MessageDefinition], registry: Any
    ) -> list[dict[str, Any]]:
        return [
            {"role": m.role.value, "content": m.content_history} for m in chat_messages
        ]

    def _map_tools(self, tools: Any) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": f"{t.server_name}__{t.name}" if t.server_name else t.name,
                    "description": t.description,
                    "parameters": t.arguments,
                },
            }
            for t in tools
        ]

    async def check_health(self) -> bool:
        try:
            ollama.list()
            return True
        except Exception:
            return False

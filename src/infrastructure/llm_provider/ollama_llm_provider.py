import logging
import uuid
from typing import Any

import httpx
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
    Uses direct HTTP calls to bypass library inconsistencies.
    """

    def __init__(self, config: OllamaConfig) -> None:
        self.config_llm: OllamaConfig = config
        self.url = f"{config.host}/api/chat"

    @handle_errors(exception_cls=InfrastructureException, layer="Infrastructure")
    async def __call__(self, request: LLMRequest) -> LLMResponse:
        logger.debug(f"Executing Ollama request: {self.config_llm.model_id}")

        messages = self._map_messages(request.messages)
        options = self._prepare_options(request.inference)

        is_json = "json" in str(getattr(self.config_llm, "output_format", "")).lower()
        if getattr(request.inference, "json_mode", False):
            is_json = True

        payload = {
            "model": self.config_llm.model_id,
            "messages": messages,
            "options": options,
            "stream": False,
        }
        if is_json:
            payload["format"] = "json"

        logger.info(f"Ollama HTTP Payload: {payload}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        llm_resp = self._build_llm_response(data)
        logger.info(f"Ollama HTTP Response Content: '{llm_resp.content}'")
        return llm_resp

    def _prepare_options(self, inference: LLMInferenceConfig | None) -> dict[str, Any]:
        target_config = inference or self.config_llm.inference
        raw_options = vars(target_config)
        
        # Clonar para evitar mutar el original si se reusa
        opts = {k: v for k, v in raw_options.items() if v is not None}

        if "max_tokens" in opts:
            opts["num_predict"] = opts.pop("max_tokens")

        allowed = {
            "num_predict", "top_k", "top_p", "temperature",
            "repeat_penalty", "seed", "stop", "num_ctx"
        }
        return {k: v for k, v in opts.items() if k in allowed}

    def _build_llm_response(self, data: dict[str, Any]) -> LLMResponse:
        message = data.get("message", {})
        content = message.get("content", "")
        raw_calls = message.get("tool_calls", [])

        in_t = data.get("prompt_eval_count") or 0
        out_t = data.get("eval_count") or 0
        
        token_usage = in_t + out_t
        if token_usage == 0 and content:
            token_usage = 1

        return LLMResponse(
            model=data.get("model", self.config_llm.model_id),
            content=(content or "").strip(),
            tool_calls=self._map_structured_calls(raw_calls),
            input_tokens=in_t,
            output_tokens=out_t,
            token_usage=token_usage,
            total_duration_ms=self._to_ms(data.get("total_duration")),
        )

    def _map_structured_calls(self, raw_calls: list[Any] | None) -> list[ToolCall]:
        structured_calls: list[ToolCall] = []
        for t in raw_calls or []:
            func = t.get("function", {})
            name = func.get("name", "")
            if name:
                structured_calls.append(
                    ToolCall(
                        id=str(t.get("id", uuid.uuid4())),
                        name=str(name),
                        arguments=func.get("arguments", {}),
                    )
                )
        return structured_calls

    def _to_ms(self, nanoseconds: Any) -> float:
        try:
            return float(nanoseconds) / 1_000_000.0 if nanoseconds else 0.0
        except:
            return 0.0

    def _map_messages(self, chat_messages: list[MessageDefinition]) -> list[dict[str, Any]]:
        return [{"role": m.role.value, "content": m.content_history} for m in chat_messages]

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.config_llm.host}/api/tags")
                return resp.status_code == 200
        except:
            return False

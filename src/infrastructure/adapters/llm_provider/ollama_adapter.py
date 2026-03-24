# src/infrastructure/adapters/llm/ollama_adapter.py

import logging
from typing import Any

import ollama

from domain.models.llm_provider import LLMInferenceConfig
from domain.ports.llm_provider import LLMProviderPort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import InfrastructureException
from infrastructure.adapters.config.ollama import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMProviderPort):
    """
    Adapter for local Ollama service.
    Handles mapping between Domain inference configs and Ollama SDK options.

    Fixed: Instantiates AsyncClient inside async methods to prevent
    'Event loop is closed' errors during integration tests.
    """

    def __init__(self, config: OllamaConfig) -> None:
        self.config = config
        # We store the host string instead of a bound client to ensure
        # compatibility with different event loops in test environments.
        self._host = self.config.host

    @handle_errors(exception_cls=InfrastructureException, layer="Infrastructure")
    async def generate(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        inference: LLMInferenceConfig | None = None,
    ) -> dict[str, Any]:
        """
        Executes the chat request using Ollama.
        Forces JSON format to ensure 8B models respect the Supervisor's schema.
        """
        current_inference = inference or self.config.inference
        options = current_inference.to_dict()

        # Create client bound to the current running loop
        client = ollama.AsyncClient(host=self._host)

        response = await client.chat(
            model=self.config.model_name,
            messages=messages,
            tools=tools,
            options=options,
            format="json",  # Mandatory for SupervisorNode parsing reliability
        )

        # Metadata extraction for AgentState synchronization
        eval_count = response.get("eval_count", 0)
        prompt_eval = response.get("prompt_eval_count", 0)

        return {
            "content": response.get("message", {}).get("content", ""),
            "tool_calls": response.get("message", {}).get("tool_calls", []),
            "token_usage": eval_count + prompt_eval,
            "model_name": self.config.model_name,
            "raw": response,
        }

    @handle_errors(exception_cls=InfrastructureException, layer="Infrastructure")
    async def check_health(self) -> bool:
        """Verifies if the Ollama service is reachable using a fresh client."""
        client = ollama.AsyncClient(host=self._host)
        await client.list()
        return True

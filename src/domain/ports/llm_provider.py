from typing import Protocol, runtime_checkable

from domain.models.llm_provider_model import BaseLLMConfig, LLMRequest, LLMResponse


@runtime_checkable
class LLMProviderPort(Protocol):
    """
    Universal asynchronous contract for LLM providers.
    Uses the Request-Response DTO pattern to ensure architectural stability
    and decoupling from infrastructure-specific SDKs.

    This port is implemented as a 'callable' (__call__) to align with
    modern Python functional patterns in AI orchestration.
    """

    config: BaseLLMConfig

    async def __call__(self, request: LLMRequest) -> LLMResponse:
        """
        Executes the inference request and returns a standardized response.

        Args:
            request: A structured LLMRequest containing messages, tools,
                    inference config, and output format.

        Returns:
            A standardized LLMResponse DTO containing content, tool calls,
            and detailed telemetry (tokens and duration).
        """
        ...

    async def check_health(self) -> bool:
        """
        Verifies the availability of the LLM service.
        Used for circuit breaker initialization and health monitoring.
        """
        ...

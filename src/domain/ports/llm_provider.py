from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProviderPort(Protocol):
    """
    Contract for LLM providers.
    Standardized as asynchronous to enable non-blocking communication
    with local and cloud-based models.
    """

    async def generate(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """
        Main asynchronous contract for chat and tool-calling capabilities.
        Returns a dictionary containing the assistant's response or tool calls.
        """
        ...

    async def check_health(self) -> bool:
        """
        Verifies asynchronously if the connection to the LLM service is active.
        """
        ...

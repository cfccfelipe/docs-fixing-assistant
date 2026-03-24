from typing import Any

import pytest

from domain.models.llm_provider import LLMInferenceConfig
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from domain.ports.llm_provider import LLMProviderPort


class DummyLLMProvider(LLMProviderPort):
    """Fake LLM provider that mimics LLMProviderPort for unit testing."""

    def __init__(self, output: str = "end", fail: bool = False):
        self.output = output
        self.fail = fail

    async def generate(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        inference: LLMInferenceConfig | None = None,
    ) -> dict[str, Any]:
        if self.fail:
            raise RuntimeError("Simulated LLM failure")
        return {"content": self.output, "stop_reason": "completed"}


@pytest.fixture
def supervisor_factory():
    """Factory fixture to create SupervisorNode with different DummyLLMProvider configs."""

    def _factory(output: str = "end", fail: bool = False):
        return SupervisorNode(llm_provider=DummyLLMProvider(output=output, fail=fail))

    return _factory

from typing import Any

import pytest

from domain.models.llm_provider import LLMInferenceConfig
from domain.models.state import AgentState, NodeResponse, StateMetadata
from domain.orchestrator.constants import messages as msg
from domain.orchestrator.nodes.supervisor_node import SupervisorNode
from domain.orchestrator.registry import MANDATORY_AGENT_IDS
from domain.ports.llm_provider import LLMProviderPort
from domain.utils.exceptions import OrchestrationException


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


# -------------------
# Positive test cases
# -------------------


@pytest.mark.asyncio
async def test_max_iterations_triggers_end():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="anything"))
    state = AgentState(user_feedback="test", path="dummy/path", iterations=6)
    response: NodeResponse = await supervisor(state)

    assert response.active_agents == ["__end__"]
    assert msg.MSG_MAX_ITERATIONS in response.results[0]


@pytest.mark.asyncio
async def test_workflow_finalized_on_end_keyword():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="end"))
    state = AgentState(user_feedback="finish now", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    assert response.active_agents == ["__end__"]
    assert msg.MSG_WORKFLOW_FINALIZED in response.results[0]


@pytest.mark.asyncio
async def test_standard_routing_with_valid_keys():
    supervisor = SupervisorNode(
        llm_provider=DummyLLMProvider(output="atomicity_agent naming_agent")
    )
    state = AgentState(user_feedback="route me", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    for agent in MANDATORY_AGENT_IDS:
        assert agent in response.active_agents
    assert "naming_agent" in response.active_agents


@pytest.mark.asyncio
async def test_fallback_routing_when_no_keys_found():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="random text"))
    state = AgentState(user_feedback="no valid keys", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    assert msg.MSG_FALLBACK_ROUTING in response.results[0]


@pytest.mark.asyncio
async def test_summary_mode_triggers_chunking():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="end"))
    state = AgentState(
        user_feedback="summarize",
        path="dummy/path",
        iterations=0,
        metadata=StateMetadata(is_summary=True),
    )
    response: NodeResponse = await supervisor(state)

    assert response.active_agents == ["xml_chunker"]
    assert msg.MSG_CHUNK_REQUIRED in response.results[0]


# -------------------
# Negative test cases
# -------------------


@pytest.mark.asyncio
async def test_supervisor_handles_llm_failure():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(fail=True))
    state = AgentState(user_feedback="test", path="dummy/path", iterations=0)

    # El supervisor lanza OrchestrationException
    with pytest.raises(OrchestrationException) as excinfo:
        await supervisor(state)

    assert "Simulated LLM failure" in str(excinfo.value)


@pytest.mark.asyncio
async def test_supervisor_invalid_output_triggers_fallback():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="nonsense output"))
    state = AgentState(user_feedback="invalid", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    assert msg.MSG_FALLBACK_ROUTING in response.results[0]
    assert (
        response.metadata.error_message is None or response.metadata.error_message == ""
    )


@pytest.mark.asyncio
async def test_supervisor_exceeds_iterations_with_errors():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output="anything"))
    state = AgentState(
        user_feedback="keep looping",
        path="dummy/path",
        iterations=10,
        metadata=StateMetadata(validation_errors=["previous failure"]),
    )
    response: NodeResponse = await supervisor(state)

    assert response.active_agents == ["__end__"]
    assert msg.MSG_MAX_ITERATIONS in response.results[0]
    # El supervisor coloca el mensaje en error_message y no preserva validation_errors
    assert response.metadata.error_message == msg.MSG_MAX_ITERATIONS
    assert response.metadata.validation_errors == []


@pytest.mark.asyncio
async def test_supervisor_handles_non_completed_stop_reason():
    class DummyLLMProviderStop(LLMProviderPort):
        async def generate(self, messages, tools=None, inference=None):
            return {"content": "atomicity_agent", "stop_reason": "length"}

    supervisor = SupervisorNode(llm_provider=DummyLLMProviderStop())
    state = AgentState(user_feedback="test", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    assert "atomicity_agent" in response.active_agents
    assert response.metadata.stop_reason == "length"


@pytest.mark.asyncio
async def test_supervisor_empty_user_feedback_triggers_fallback():
    supervisor = SupervisorNode(llm_provider=DummyLLMProvider(output=""))
    state = AgentState(user_feedback="", path="dummy/path", iterations=0)
    response: NodeResponse = await supervisor(state)

    assert msg.MSG_FALLBACK_ROUTING in response.results[0]
    assert all(agent in response.active_agents for agent in MANDATORY_AGENT_IDS)

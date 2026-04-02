from unittest.mock import AsyncMock

import pytest

from domain.models.enums import StopReason
from domain.models.llm_provider_model import LLMResponse
from domain.models.state_model import AgentConfig, AgentState, StateMetadata
from domain.orchestrator.nodes.supervisor_node import SupervisorNode


@pytest.fixture
def mock_llm_provider():
    return AsyncMock()


@pytest.fixture
def supervisor_config(mock_llm_provider):
    return AgentConfig(
        agent_id="supervisor",
        system_prompt="Analyze state: {current_state}",
        llm_provider=mock_llm_provider,
        temperature=0.0,
        max_tokens=100,
        output_format="json",
    )


@pytest.fixture
def supervisor_node(supervisor_config):
    return SupervisorNode(config=supervisor_config, max_iterations=5)


@pytest.mark.asyncio
async def test_supervisor_routing_decision(supervisor_node, mock_llm_provider):
    """
    Test: Supervisor -> Planner.
    El BaseNode inyecta '{'. El mock completa el resto del JSON.
    """
    state = AgentState(
        folder_path="/test",
        user_prompt="start",
        iteration=0,
        metadata=StateMetadata(),
    )

    # IMPORTANTE: Sin la llave de apertura, para que al sumar '{' + content sea válido.
    mock_llm_provider.return_value = LLMResponse(
        model="test",
        content='"next_agent": "planner", "next_task": "plan", "stop_reason": "CALL"}',
        input_tokens=5,
        output_tokens=5,
        token_usage=10,
    )

    update = await supervisor_node(state)

    # Si esto falla con ERROR, revisa que ResponseParser no esté normalizando a minúsculas
    assert update["stop_reason"] == StopReason.CALL
    assert update["next_agent"] == "planner"


@pytest.mark.asyncio
async def test_supervisor_termination(supervisor_node, mock_llm_provider):
    """Test: Supervisor -> End."""
    state = AgentState(folder_path="/test", user_prompt="stop", iteration=1)

    mock_llm_provider.return_value = LLMResponse(
        model="test",
        content='"stop_reason": "END", "final_response": "done"}',
        token_usage=10,
    )

    update = await supervisor_node(state)

    assert update["stop_reason"] == StopReason.END
    assert update["final_response"] == "done"

from unittest.mock import AsyncMock

import pytest

from domain.models.llm_provider_model import LLMResponse
from domain.models.state_model import AgentConfig, AgentState, StateMetadata, StopReason
from domain.orchestrator.nodes.supervisor_node import SupervisorNode


@pytest.fixture
def mock_llm_provider():
    return AsyncMock()


@pytest.fixture
def supervisor_node(mock_llm_provider):
    from domain.orchestrator.constants.system_prompts import SYSTEM_PROMPT_SUPERVISOR

    config = AgentConfig(
        agent_id="supervisor",
        system_prompt=SYSTEM_PROMPT_SUPERVISOR,
        llm_provider=mock_llm_provider,
    )
    return SupervisorNode(config=config, max_iterations=5)


@pytest.mark.asyncio
async def test_supervisor_routing_decision(supervisor_node, mock_llm_provider):
    """
    Test: Supervisor -> Planner.
    """
    state = AgentState(
        folder_path="/test",
        user_prompt="start",
        iteration=0,
        metadata=StateMetadata(),
        content="", # Empty content should trigger planner_agent
    )

    mock_llm_provider.return_value = LLMResponse(
        model="test",
        content='"next_agent": "planner_agent", "next_task": "plan", "stop_reason": "CALL"}',
        token_usage=10,
    )

    update = await supervisor_node(state)

    assert update["stop_reason"] == StopReason.CALL
    assert update["next_agent"] == "planner_agent"


@pytest.mark.asyncio
async def test_supervisor_termination(supervisor_node, mock_llm_provider):
    """Test: Supervisor -> End."""
    # content with [x] and no [ ] should trigger END if configured in prompts/logic
    state = AgentState(
        folder_path="/test",
        user_prompt="stop",
        iteration=1,
        content="- [x] Task done"
    )

    mock_llm_provider.return_value = LLMResponse(
        model="test",
        content='"stop_reason": "END", "final_response": "done"}',
        token_usage=10,
    )

    update = await supervisor_node(state)

    assert update["stop_reason"] == StopReason.END

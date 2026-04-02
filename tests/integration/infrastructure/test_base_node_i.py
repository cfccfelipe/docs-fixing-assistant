import uuid

import httpx
import pytest

from domain.models.enums import MessageRole
from domain.models.llm_provider_model import (
    LLMInferenceConfig,
    LLMRequest,
    OllamaConfig,
)
from domain.models.message_model import MessageDefinition
from domain.models.state_model import AgentState, StateMetadata
from domain.orchestrator.nodes.base_node import BaseNode
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3.1:latest"


def is_ollama_running():
    """Check if the local Ollama service is reachable."""
    try:
        return httpx.get(OLLAMA_HOST).status_code == 200
    except Exception:
        return False


@pytest.fixture
def real_llm_provider():
    """Provides a real OllamaAdapter instance."""
    config = OllamaConfig(
        host=OLLAMA_HOST,
        model_id=MODEL_NAME,
        timeout=60,
        inference=LLMInferenceConfig(temperature=0.0, max_tokens=100),
    )
    return OllamaAdapter(config)


@pytest.fixture
def integration_node(real_llm_provider):
    """Provides a BaseNode configured for integration testing."""

    class Config:
        agent_id = "integration_agent"
        llm_provider = real_llm_provider
        temperature = 0.0
        max_tokens = 100
        output_format = "json"

    return BaseNode(config=Config(), max_iterations=5)


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama not running")
async def test_base_node_integration_full_flow(integration_node):
    """
    Validates that the node executes real inference and accumulates
    verifiable metrics in StateMetadata.
    """
    state = AgentState(
        folder_path="any",
        user_prompt='What is the capital of France? Respond strictly in this JSON format: {"capital": "Paris"}',
        metadata=StateMetadata(),
    )

    request = LLMRequest(
        messages=[
            MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.SYSTEM,
                content_history="You are an assistant that only responds in valid JSON format.",
            ),
            MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.USER,
                content_history=state.user_prompt,
            ),
        ],
        inference=None,
        tools_registry=[],
    )

    response = await integration_node._execute_inference(request)
    parsed_content = integration_node._parse_response(response, state)

    # Clearer debugging
    assert parsed_content is not None, f"Parser returned None. Raw: {response.content}"
    assert not parsed_content.get("parsing_failed", False), (
        f"JSON parsing failed. Raw content: {response.content}"
    )

    values_str = [str(v).lower() for v in parsed_content.values()]
    assert any("paris" in v for v in values_str), (
        f"Expected 'paris' in values, but got: {parsed_content}"
    )

    new_metadata = integration_node._create_metadata(state, response)

    assert response.input_tokens > 0, "Input tokens should be > 0"
    assert response.output_tokens > 0, "Output tokens should be > 0"
    assert new_metadata.token_usage >= (response.input_tokens + response.output_tokens)
    assert new_metadata.total_duration_ms > 0


@pytest.mark.asyncio
@pytest.mark.skipif(not is_ollama_running(), reason="Ollama not running")
async def test_base_node_cumulative_metadata(integration_node):
    """
    Validates that the node correctly sums metrics if the state already contained them.
    """
    previous_metadata = StateMetadata(
        token_usage=100, input_tokens=50, output_tokens=50, total_duration_ms=500.0
    )
    state = AgentState(
        folder_path="any",
        user_prompt="Respond only with the word 'Hello' in JSON: {'msg': 'Hello'}",
        metadata=previous_metadata,
    )

    request = LLMRequest(
        messages=[
            MessageDefinition(
                id=uuid.uuid4(),
                role=MessageRole.USER,
                content_history=state.user_prompt,
            )
        ],
        inference=None,
        tools_registry=[],
    )

    response = await integration_node._execute_inference(request)
    final_metadata = integration_node._create_metadata(state, response)

    assert final_metadata.token_usage > 100, "Token usage was not accumulated."
    assert final_metadata.input_tokens > 50, "Input tokens were not accumulated."
    assert final_metadata.total_duration_ms > 500.0, "Duration was not accumulated."
    assert final_metadata.last_agent_key == "integration_agent"

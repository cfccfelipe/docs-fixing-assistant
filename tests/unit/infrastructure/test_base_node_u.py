from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from domain.models.llm_provider_model import LLMResponse, ToolCall
from domain.models.state_model import AgentState, StateMetadata, StopReason
from domain.orchestrator.nodes.base_node import BaseNode

# --- Mocks de Configuración ---


@dataclass
class MockAgentConfig:
    agent_id: str = "test_agent"
    temperature: float = 0.0
    max_tokens: int = 100
    stop_sequences: list[str] = field(default_factory=lambda: ["}"])
    output_format: str = "json"
    llm_provider: Any = None


@pytest.fixture
def base_node():
    config = MockAgentConfig()
    config.llm_provider = AsyncMock()
    # BaseNode(config, max_iterations)
    return BaseNode(config=config, max_iterations=3)


@pytest.fixture
def initial_state():
    return AgentState(
        user_prompt="Hello",
        iteration=0,
        metadata=StateMetadata(token_usage=50, input_tokens=25, output_tokens=25),
        folder_path="test",
    )


# --- Tests de Lógica de Control ---


@pytest.mark.asyncio
async def test_circuit_breaker_triggers(base_node, initial_state):
    """
    Verifica que el bucle se detenga al alcanzar el max_iterations.
    Ajustado para acceder a los datos como diccionario/objeto de forma robusta.
    """
    initial_state.iteration = 3  # Coincide con max_iterations del fixture

    result = await base_node(initial_state)

    # 1. Si el resultado es un StateUpdate o Dict, accedemos por llave o get
    # para evitar el AttributeError
    stop_reason = getattr(result, "stop_reason", None) or result.get("stop_reason")
    error_message = getattr(result, "error_message", "") or result.get(
        "error_message", ""
    )

    assert stop_reason == StopReason.END
    assert "Circuit Breaker" in error_message


def test_iteration_increments(base_node, initial_state):
    """Verifica el incremento quirúrgico de la iteración."""
    result = base_node._get_execution_delta(initial_state)
    assert result["iteration"] == 1


# --- Tests de Telemetría y Metadata ---


def test_metadata_accumulation(base_node, initial_state):
    """Valida la suma correcta de tokens entre iteraciones."""
    mock_response = LLMResponse(
        model="llama3",
        content='{"status": "ok"}',
        input_tokens=10,
        output_tokens=20,
        token_usage=30,
        total_duration_ms=100.0,
    )

    new_metadata = base_node._create_metadata(initial_state, mock_response)

    assert new_metadata.token_usage == 80  # 50 previo + 30 nuevo
    assert new_metadata.input_tokens == 35  # 25 previo + 10 nuevo
    assert new_metadata.last_agent_key == "test_agent"


# --- Tests de Inferencia y Parsing (Ajustados a ToolCalls) ---


def test_parse_response_with_tool_objects(base_node):
    """
    CORRECCIÓN: Valida que tool_calls (objetos) disparen StopReason.CALL
    en lugar de usar los antiguos IDs planos.
    """
    mock_call = ToolCall(id="call_1", name="read_file", arguments={"path": "a.txt"})
    mock_response = LLMResponse(
        model="test", content="I will read this.", tool_calls=[mock_call]
    )

    parsed = base_node._parse_response(mock_response)

    assert parsed["stop_reason"] == StopReason.CALL
    assert len(parsed["tool_calls"]) == 1
    assert parsed["tool_calls"][0].name == "read_file"


def test_parse_response_json_with_injected_stop_reason(base_node):
    """Verifica que si el JSON no trae stop_reason, se inyecte CALL por defecto."""
    mock_response = LLMResponse(
        model="test", content='{"result": "success"}', tool_calls=[]
    )

    with patch("domain.utils.response_parser.ResponseParser.parse_json") as mock_parser:
        # El parser devuelve el dict, pero sin stop_reason
        mock_parser.return_value = {"result": "success"}

        parsed = base_node._parse_response(mock_response)

        assert parsed["result"] == "success"
        # Debe inyectar CALL para que el orquestador siga al siguiente nodo
        assert parsed["stop_reason"] == StopReason.CALL


def test_parse_response_error_on_invalid_json(base_node):
    """Valida que un JSON roto resulte en StopReason.ERROR."""
    mock_response = LLMResponse(model="test", content="{broken json", tool_calls=[])

    with patch("domain.utils.response_parser.ResponseParser.parse_json") as mock_parser:
        mock_parser.return_value = None  # Simula fallo de parsing

        parsed = base_node._parse_response(mock_response)

        assert parsed["stop_reason"] == StopReason.ERROR
        assert parsed["parsing_failed"] is True

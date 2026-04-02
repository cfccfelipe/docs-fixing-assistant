import uuid
from unittest.mock import AsyncMock, patch

import pytest

from domain.models.enums import MessageRole, ToolType
from domain.models.llm_provider_model import (
    LLMInferenceConfig,
    LLMRequest,
    OllamaConfig,
)
from domain.models.message_model import MessageDefinition
from domain.models.tool_model import ToolDefinition
from domain.utils.exceptions import InfrastructureException
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter

# --- Fixtures ---


@pytest.fixture
def mock_ollama_config():
    """Configuración mock para el adaptador."""
    return OllamaConfig(
        host="http://localhost:11434",
        model_id="llama3.1",
        timeout=30,
        inference=LLMInferenceConfig(temperature=0.0, max_tokens=100),
    )


@pytest.fixture
def adapter(mock_ollama_config):
    """Instancia del adaptador con config mock."""
    return OllamaAdapter(mock_ollama_config)


# --- Unit Tests ---


@pytest.mark.asyncio
async def test_ollama_adapter_mapping_logic(adapter):
    """
    Valida que el adaptador transforme correctamente la petición
    y mapee la respuesta del SDK a nuestro objeto ToolCall.
    """
    tool = ToolDefinition(
        name="write_file",
        server_name="fs_service",
        description="Write to disk",
        arguments={"type": "object"},
        type=ToolType.FUNCTION,
    )

    messages = [
        MessageDefinition(
            id=uuid.uuid4(),
            role=MessageRole.USER,
            content_history="Write hello to a.txt",
        )
    ]
    request = LLMRequest(messages=messages, inference=None, tools_registry=[tool])

    # Simulamos la respuesta del SDK de Ollama
    mock_sdk_response = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "fs_service__write_file",
                        "arguments": {"path": "a.txt", "content": "hello"},
                    }
                }
            ],
        },
        "model": "llama3.1",
        "eval_count": 20,
        "prompt_eval_count": 10,
        "total_duration": 100000000,  # 100ms en nanosegundos
    }

    with patch("ollama.AsyncClient.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_sdk_response

        response = await adapter(request)

        # Validaciones de Mapeo
        assert response.content == ""
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "fs_service__write_file"
        assert response.tool_calls[0].arguments["path"] == "a.txt"
        assert response.token_usage == 30

        # Verificamos que se enviaron las herramientas al SDK
        called_kwargs = mock_chat.call_args.kwargs
        assert "tools" in called_kwargs
        assert called_kwargs["tools"][0]["function"]["name"] == "fs_service__write_file"


def test_transform_to_sdk_message_assistant_with_tool_calls(adapter):
    """Valida la reconstrucción del historial para el SDK."""
    tool_name = "fs_service__write_file"
    registry_map = {tool_name: tool_name}

    msg = MessageDefinition(
        id=uuid.uuid4(),
        role=MessageRole.ASSISTANT,
        content_history="",
        tool_history_ids=[tool_name],  # Historial de herramientas ejecutadas
    )

    sdk_msg = adapter._transform_to_sdk_message(msg, registry_map)

    assert sdk_msg["role"] == "assistant"
    assert "tool_calls" in sdk_msg
    assert sdk_msg["tool_calls"][0]["function"]["name"] == tool_name


@pytest.mark.asyncio
async def test_infrastructure_exception_wrapping(adapter):
    """Verifica que errores de red se conviertan en InfrastructureException."""
    request = LLMRequest(messages=[], inference=None, tools_registry=[])

    with patch("ollama.AsyncClient.chat", side_effect=Exception("Connection refused")):
        with pytest.raises(InfrastructureException):
            await adapter(request)


@pytest.mark.asyncio
async def test_check_health_logic(adapter):
    """Valida el health check del servicio."""
    with patch("ollama.AsyncClient.list", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = {"models": []}
        result = await adapter.check_health()
        assert result is True


def test_build_llm_response_with_missing_metrics(adapter):
    """Valida que el mapper sea robusto ante la falta de métricas."""
    sdk_minimal = {"message": {"content": "Hello"}, "model": "test-model"}

    response = adapter._build_llm_response(sdk_minimal)

    assert response.content == "Hello"
    assert response.input_tokens == 0
    assert response.token_usage == 0

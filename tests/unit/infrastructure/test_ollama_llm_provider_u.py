import uuid
from unittest.mock import MagicMock, patch

import pytest

from domain.models.llm_provider_model import LLMRequest, OllamaConfig
from domain.models.message_model import MessageDefinition, MessageRole
from domain.models.tool_model import ToolDefinition, ToolType
from domain.utils.exceptions import InfrastructureException
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter


@pytest.fixture
def adapter():
    config = OllamaConfig(host="http://localhost:11434", model_id="llama3.1")
    return OllamaAdapter(config)


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

    # Simulamos la respuesta JSON de Ollama
    mock_json = {
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
        "total_duration": 100000000,
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_json
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        response = await adapter(request)

        # Validaciones de Mapeo
        assert response.content == ""
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "fs_service__write_file"
        assert response.token_usage == 30


@pytest.mark.asyncio
async def test_infrastructure_exception_wrapping(adapter):
    """Verifica que errores de red se conviertan en InfrastructureException."""
    request = LLMRequest(messages=[], inference=None, tools_registry=[])

    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection refused")):
        with pytest.raises(InfrastructureException):
            await adapter(request)


def test_build_llm_response_with_missing_metrics(adapter):
    """Valida que el mapper sea robusto ante la falta de métricas."""
    sdk_minimal = {"message": {"content": "Hello"}, "model": "test-model"}

    response = adapter._build_llm_response(sdk_minimal)

    assert response.content == "Hello"
    assert response.input_tokens == 0
    assert response.token_usage == 1

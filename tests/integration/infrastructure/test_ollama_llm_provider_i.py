import uuid

import httpx
import pytest

from domain.models.enums import MessageRole, ToolType
from domain.models.llm_provider_model import (
    LLMInferenceConfig,
    LLMRequest,
    OllamaConfig,
)
from domain.models.message_model import MessageDefinition
from domain.models.tool_model import ToolDefinition
from infrastructure.llm_provider.ollama_llm_provider import OllamaAdapter

OLLAMA_HOST = "http://localhost:11434"
MODEL_NAME = "llama3.1:latest"


def is_ollama_running():
    """Verifica si el servicio local de Ollama está activo."""
    try:
        response = httpx.get(OLLAMA_HOST)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def real_adapter():
    config = OllamaConfig(
        host=OLLAMA_HOST,
        model_id=MODEL_NAME,
        timeout=60,
        inference=LLMInferenceConfig(temperature=0.0, max_tokens=256),
    )
    return OllamaAdapter(config)


@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_ollama_running(), reason="Ollama service is not running locally"
)
async def test_ollama_real_inference_call(real_adapter):
    """EJECUCIÓN REAL: Envía un mensaje a Ollama y valida la respuesta del modelo."""
    messages = [
        MessageDefinition(
            id=uuid.uuid4(),
            role=MessageRole.USER,
            content_history="Responde solo con la palabra 'OK' para verificar conexión.",
        )
    ]
    request = LLMRequest(messages=messages, inference=None, tools_registry=[])

    response = await real_adapter(request)

    assert response is not None
    assert "OK" in response.content.upper()
    assert response.input_tokens > 0
    assert response.output_tokens > 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    not is_ollama_running(), reason="Ollama service is not running locally"
)
async def test_ollama_tool_calling_real_flow(real_adapter):
    """
    EJECUCIÓN REAL: Valida que el adaptador detecte la herramienta.
    FIX: Ahora valida contra la lista de objetos ToolCall.
    """
    tool = ToolDefinition(
        name="get_weather",
        server_name="weather_service",
        description="Get the current weather in a given city",
        arguments={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        type=ToolType.FUNCTION,
    )

    messages = [
        MessageDefinition(
            id=uuid.uuid4(),
            role=MessageRole.SYSTEM,
            content_history="Eres un asistente técnico. Si preguntan por el clima, usa 'get_weather'.",
        ),
        MessageDefinition(
            id=uuid.uuid4(),
            role=MessageRole.USER,
            content_history="¿Cómo está el clima en Londres?",
        ),
    ]

    request = LLMRequest(messages=messages, tools_registry=[tool])
    response = await real_adapter(request)

    expected_tool_name = "weather_service__get_weather"

    # 80/20: Extraemos los nombres de los objetos ToolCall para la aserción
    actual_tool_names = [tc.name for tc in response.tool_calls]

    assert expected_tool_name in actual_tool_names, (
        f"Se esperaba {expected_tool_name} pero se obtuvo {actual_tool_names}. "
        f"Content: {response.content}"
    )

    # Validamos que los argumentos se hayan parseado como diccionario
    weather_call = next(
        tc for tc in response.tool_calls if tc.name == expected_tool_name
    )
    assert isinstance(weather_call.arguments, dict)
    assert "city" in weather_call.arguments

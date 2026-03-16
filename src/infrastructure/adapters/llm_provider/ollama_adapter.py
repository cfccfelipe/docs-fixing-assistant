import asyncio
import logging
from typing import Any

import ollama

from domain.ports.llm_provider import LLMProviderPort
from domain.utils.decorators import handle_errors
from domain.utils.exceptions import LLMConnectionException
from infrastructure.adapters.config.ollama import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaAdapter(LLMProviderPort):
    def __init__(self, config: OllamaConfig):
        self.client = ollama.AsyncClient(host=str(config.base_url))
        self.config = config
        self.fallback_model = "qwen2.5-coder:1.5b"

    @handle_errors(
        exception_cls=LLMConnectionException,
        provider="Ollama",
        layer="Infrastructure",
        component="OllamaAdapter",
    )
    async def generate(
        self, messages: list[dict[str, str]], tools: list[dict[str, Any]] | None = None
    ) -> dict[str, str]:
        """
        Genera una respuesta con reintento automático y fallback.
        Orden: [Principal, Reintento Principal, Fallback Ligero]
        """
        options = self._get_exec_options()
        timeout = self.config.options.get("timeout", 360)

        # Lista de intentos: 2 con el principal, 1 con el fallback
        models_to_try = [
            self.config.model_name,
            self.config.model_name,
            self.fallback_model,
        ]

        for i, model in enumerate(models_to_try):
            is_fallback = i == len(models_to_try) - 1
            try:
                logger.info(f"Intento {i + 1} con modelo: {model}")
                result = await self._run_with_timeout(
                    model, messages, tools, options, timeout
                )

                if self._is_valid_output(result):
                    return self._format_response(result)

                logger.warning(f"⚠️ Salida vacía/inválida del modelo {model}")

            except LLMConnectionException as e:
                if is_fallback:
                    raise e  # Si el fallback también falla, propagamos
                logger.warning(f"⚠️ Error de conexión en intento {i + 1}: {e}")

            except asyncio.CancelledError:
                raise

        raise LLMConnectionException(
            "Todos los modelos fallaron en generar una respuesta válida."
        )

    async def _run_with_timeout(
        self, model: str, messages, tools, options, timeout: int
    ) -> Any:
        try:
            # ollama.AsyncClient.chat ya es cancelable, no siempre requiere create_task
            return await asyncio.wait_for(
                self.client.chat(
                    model=model,
                    messages=messages,
                    tools=tools or [],
                    options=options,
                    stream=False,
                ),
                timeout=timeout,
            )
        except TimeoutError:
            logger.error(f"⏱️ Timeout: {model} > {timeout}s")
            raise LLMConnectionException(f"Timeout en {model}")
        except Exception as e:
            logger.error(f"❌ Error en {model}: {e}")
            raise LLMConnectionException(str(e))

    def _get_exec_options(self) -> dict:
        return {
            "temperature": self.config.options.get("temperature", 0),
            "num_predict": self.config.options.get("num_predict", 4096),
            "num_ctx": self.config.options.get("num_ctx", 8000),
        }

    def _is_valid_output(self, result: Any) -> bool:
        """Verifica si el resultado tiene contenido útil."""
        if not result or "message" not in result:
            return False
        content = result["message"].get("content", "").strip()
        return len(content) > 5

    def _format_response(self, result: Any) -> dict[str, str]:
        """Estandariza la salida para los agentes."""
        return {"content": result["message"].get("content", "").strip()}

    async def check_health(self) -> bool:
        try:
            await asyncio.wait_for(self.client.list(), timeout=2.0)
            return True
        except Exception:
            return False

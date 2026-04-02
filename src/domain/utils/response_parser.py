import json
import logging
import unicodedata
from typing import Any

from domain.utils.decorators import handle_errors
from domain.utils.exceptions import ParserError

logger = logging.getLogger(__name__)


class ResponseParser:
    """
    Utility for robust response extraction and normalization.
    """

    @staticmethod
    def normalize_str(text: str) -> str:
        """
        Performs NFD normalization and converts to lowercase for intent matching.
        """
        if not text:
            return ""
        normalized = "".join(
            c
            for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        return normalized.lower().strip()

    @staticmethod
    def normalize_data(data: Any) -> Any:
        """
        Deep normalization.
        CRITICAL: Only use this for control fields, not for final content.
        """
        if isinstance(data, str):
            return ResponseParser.normalize_str(data)
        elif isinstance(data, dict):
            return {k: ResponseParser.normalize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [ResponseParser.normalize_data(i) for i in data]
        return data

    @staticmethod
    @handle_errors(exception_cls=ParserError, layer="ResponseParserUtility")
    def parse_json(raw_text: str | Any, fallback: Any = None) -> Any:
        """
        Surgically extracts JSON and handles common LLM formatting artifacts.
        """
        if not isinstance(raw_text, str) or not raw_text.strip():
            return fallback

        content = raw_text.strip()

        # Limpieza de bloques Markdown si el modelo ignoró el prefill
        if content.startswith("```json"):
            content = content.split("```json")[1].split("```")[0].strip()
        elif content.startswith("```"):
            content = content.split("```")[1].split("```")[0].strip()

        start_idx = content.find("{")
        if start_idx == -1:
            start_idx = content.find("[")
        if start_idx == -1:
            return fallback

        opener = content[start_idx]
        closer = "}" if opener == "{" else "]"
        count = 0
        end_idx = -1
        in_string = False

        # Conteo de brackets ignorando contenido dentro de strings
        for i in range(start_idx, len(content)):
            char = content[i]
            # Detectar comillas ignorando escapes como \"
            if char == '"' and (i == 0 or content[i - 1] != "\\"):
                in_string = not in_string

            if not in_string:
                if char == opener:
                    count += 1
                elif char == closer:
                    count -= 1
                    if count == 0:
                        end_idx = i
                        break

        if end_idx == -1:
            return fallback

        json_str = content[start_idx : end_idx + 1]

        try:
            # Intento de parseo directo
            return json.loads(json_str)
        except json.JSONDecodeError:
            try:
                import re
                # 1. Healer: Remover comas finales antes de } o ] (común en 8B models)
                healed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
                # 2. Healer: Escapar saltos de línea literales
                healed_json = healed_json.replace("\n", "\\n").replace("\r", "\\r")
                return json.loads(healed_json)
            except json.JSONDecodeError as e:
                logger.error(
                    f"🚨 Final JSON parse failure: {e} | Snippet: {json_str[:50]}"
                )
                return fallback

    @staticmethod
    def parse_txt(raw_text: str | Any) -> str:
        if not isinstance(raw_text, str):
            return ""
        return raw_text.strip()

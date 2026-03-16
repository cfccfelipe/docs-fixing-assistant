# src/infrastructure/adapters/llm_provider/ollama_embedder_adapter.py

import httpx

from domain.ports.embedder import IEmbedder
from infrastructure.adapters.config.ollama import OllamaConfig


class OllamaEmbedderAdapter(IEmbedder):
    """
    Adapter para usar modelos de embeddings en Ollama (ej. nomic-embed-text:latest).
    Implementa el puerto IEmbedder con un método .embed(text).
    """

    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = httpx.Client(base_url="http://localhost:11434")

    def embed(self, text: str) -> list[float]:
        response = self.client.post(
            "/api/embed", json={"model": self.config.model_name, "input": text}
        )
        data = response.json()

        # Manejar posibles estructuras de respuesta
        if "embedding" in data:
            # Caso: {"embedding": [...]}
            return data["embedding"]
        elif "embeddings" in data:
            # Caso: {"embeddings": [[...]]}
            return data["embeddings"][0]
        elif (
            "data" in data and len(data["data"]) > 0 and "embedding" in data["data"][0]
        ):
            # Caso: {"data": [{"embedding": [...]}]}
            return data["data"][0]["embedding"]
        else:
            raise ValueError(f"Unexpected Ollama embed response: {data}")

from typing import Protocol, runtime_checkable


@runtime_checkable
class IEmbedder(Protocol):
    """Puerto para servicios de embeddings."""

    def embed(self, text: str) -> list[float]:
        """Genera un vector de embeddings para el texto dado."""
        pass

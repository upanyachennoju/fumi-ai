from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract base class for all text embedding models."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a query string."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of document strings."""
        pass


class MockEmbedder(BaseEmbedder):
    """Mock implementation returning dummy embeddings for development/testing."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def embed_query(self, text: str) -> List[float]:
        # Return simple deterministic mock vector based on text hash
        val = float(hash(text) % 100) / 100.0
        return [val] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_query(text) for text in texts]

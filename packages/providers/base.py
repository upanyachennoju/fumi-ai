from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Fumi."""

    @abstractmethod
    def generate(self, message: str | list[Any], tools: list[Any] | None = None) -> Any:
        """Generate a response for the given user message or structured messages."""
        pass

class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Generate an embedding for the given text."""
        raise NotImplementedError
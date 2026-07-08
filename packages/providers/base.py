from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Fumi."""

    @abstractmethod
    def generate(self, message: str) -> str:
        """Generate a response for the given user message."""
        pass

from ollama import chat
from packages.providers.base import BaseLLMProvider
from ollama import Client
from .base import EmbeddingProvider
from packages.knowledge.schemas import Message

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model

    async def generate(self, message: str | list[Message]) -> str:
        if isinstance(message, str):
            formatted_messages = [
                {
                    "role": "user",
                    "content": message,
                }
            ]
        else:
            formatted_messages = [
                {
                    "role": msg.role,
                    "content": msg.content,
                }
                for msg in message
            ]

        response = chat(
            model=self.model,
            messages=formatted_messages,
        )

        return response.message.content

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        model: str = "nomic-embed-text",
        host: str = "http://localhost:11434",
    ):
        self.model = model
        self.client = Client(host=host)

    async def embed(self, text: str) -> list[float]:
        response = self.client.embed(
            model=self.model,
            input=text,
        )

        return response.embeddings[0]
from ollama import chat
from packages.providers.base import BaseLLMProvider
from ollama import Client
from .base import EmbeddingProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "gemma3:4b"):
        self.model = model

    async def generate(self, message: str) -> str: # should i?
        response = chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
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
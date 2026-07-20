import time
from ollama import chat
from packages.providers.base import BaseLLMProvider
from ollama import Client
from .base import EmbeddingProvider
from packages.knowledge.schemas import Message
from config import llm_model, llm_embed

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = llm_model):
        self.model = model

    async def generate(self, message: str | list[Message]) -> dict:
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

        start = time.perf_counter()

        response = chat(
            model=self.model,
            messages=formatted_messages,
        )

        elapsed = time.perf_counter() - start

        # Ollama returns eval_count (tokens generated) and eval_duration (nanoseconds)
        eval_count = getattr(response, "eval_count", 0) or 0
        eval_duration_ns = getattr(response, "eval_duration", 0) or 0
        prompt_eval_count = getattr(response, "prompt_eval_count", 0) or 0

        if eval_duration_ns > 0:
            tokens_per_sec = eval_count / (eval_duration_ns / 1e9)
        else:
            # fallback: estimate from wall-clock time
            tokens_per_sec = eval_count / elapsed if elapsed > 0 else 0.0

        return {
            "content": response.message.content,
            "metrics": {
                "response_time_sec": round(elapsed, 2),
                "tokens_generated": eval_count,
                "prompt_tokens": prompt_eval_count,
                "tokens_per_sec": round(tokens_per_sec, 1),
                "model": self.model,
            },
        }

class OllamaEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        model: str = llm_embed,
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
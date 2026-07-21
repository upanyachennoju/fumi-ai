import time
from ollama import chat
from packages.providers.base import BaseLLMProvider
from ollama import Client
from .base import EmbeddingProvider
from packages.knowledge.schemas import Message
from config import llm_model, llm_embed

import json
import re

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = llm_model):
        self.model = model

    async def generate(self, message: str | list[Message], tools: list[dict] | None = None) -> dict:
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

        formatted_tools = None
        if tools:
            formatted_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    },
                }
                for t in tools
            ]

        start = time.perf_counter()

        kwargs = {
            "model": self.model,
            "messages": formatted_messages,
        }
        if formatted_tools:
            kwargs["tools"] = formatted_tools

        response = chat(**kwargs)

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

        # Extract tool calls if present
        raw_message = getattr(response, "message", None)
        content = getattr(raw_message, "content", "") if raw_message else ""
        tool_calls = []

        if raw_message:
            raw_tool_calls = getattr(raw_message, "tool_calls", None)
            if raw_tool_calls:
                for tc in raw_tool_calls:
                    func = getattr(tc, "function", None)
                    if func:
                        name = getattr(func, "name", None)
                        args = getattr(func, "arguments", {})
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                pass
                        if name:
                            tool_calls.append({"name": name, "args": args or {}})

        # Fallback JSON parsing if native tool_calls were not parsed but content contains JSON tool block
        if not tool_calls and content and tools:
            pattern = r'\{[^{}]*"(?:name|tool)"[^{}]*\}'
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    name = data.get("name") or data.get("tool")
                    args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
                    if name and isinstance(args, dict):
                        tool_calls.append({"name": name, "args": args})
                except Exception:
                    pass

        return {
            "content": content or "",
            "tool_calls": tool_calls,
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
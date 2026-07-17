import json
import re
import inspect
from typing import Union
from packages.knowledge.schemas import Message
from packages.providers.base import BaseLLMProvider
from .schemas import MemoryExtraction
from .prompts import EXTRACTION_PROMPT


class MemoryExtractor:
    """
    Extracts structured long-term memories from a conversation using a local LLM.
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def extract(self, conversation: Union[list[Message], str]) -> MemoryExtraction:
        """
        Queries the local LLM using the EXTRACTION_PROMPT and sanitizes the output
        into a structured MemoryExtraction object.
        """
        if isinstance(conversation, list):
            convo_text = ""
            for msg in conversation:
                role = "User" if msg.role.lower() == "user" else "Fumi"
                convo_text += f"{role}: {msg.content}\n"
        else:
            convo_text = conversation

        prompt = EXTRACTION_PROMPT.replace("{conversation}", convo_text)


        try:
            res = self.llm_provider.generate(prompt)
            if inspect.iscoroutine(res):
                response_text = await res
            else:
                response_text = res
        except Exception:
            return MemoryExtraction(
                preferences=[], goals=[], projects=[], people=[], habits=[], memories=[], ignore=True
            )

        try:
            cleaned_text = response_text.strip()
            # Clean markdown code blocks if the LLM wraps the response
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                if len(lines) >= 2:
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()

            # Isolate JSON object string inside braces
            match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if match:
                cleaned_text = match.group(0)

            data = json.loads(cleaned_text)

            return MemoryExtraction(
                preferences=list(data.get("preferences", [])),
                goals=list(data.get("goals", [])),
                projects=list(data.get("projects", [])),
                people=list(data.get("people", [])),
                habits=list(data.get("habits", [])),
                memories=list(data.get("memories", [])),
                ignore=bool(data.get("ignore", False)),
            )
        except Exception:
            return MemoryExtraction(
                preferences=[], goals=[], projects=[], people=[], habits=[], memories=[], ignore=True
            )

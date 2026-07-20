import inspect
from typing import Union
from packages.knowledge.schemas import Message
from packages.providers.base import BaseLLMProvider
from .prompts import SUMMARIZATION_PROMPT


class ConversationSummarizer:
    """
    Generates a concise, single-sentence summary of a conversation using a local LLM.
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider

    async def summarize(self, conversation: Union[list[Message], str]) -> str:
        """
        Analyze the conversation history, format it into the template, and
        call the LLM to get a clean summary.
        """
        if isinstance(conversation, list):
            convo_text = ""
            for msg in conversation:
                role = "User" if msg.role.lower() == "user" else "Fumi"
                convo_text += f"{role}: {msg.content}\n"
        else:
            convo_text = conversation

        prompt = SUMMARIZATION_PROMPT.replace("{conversation}", convo_text)


        try:
            res = self.llm_provider.generate(prompt)
            if inspect.iscoroutine(res):
                result = await res
            else:
                result = res
            # Provider may return dict with content + metrics, or plain string
            summary = result["content"] if isinstance(result, dict) else result
            return summary.strip()
        except Exception:
            return "A conversation session."

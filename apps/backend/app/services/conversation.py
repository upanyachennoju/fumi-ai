from packages.providers.factory import get_llm_provider


class ConversationService:
    def __init__(self):
        self.provider = get_llm_provider()

    def chat(self, message: str) -> str:
        return self.provider.generate(message)



"""
Retrieve memories

↓

Build prompt

↓

LLM

↓

Execute tools

↓

Save conversation

↓

Return response
"""
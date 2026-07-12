from .schemas import Chunk, Message


class PromptBuilder:
    """
    Assembles the final structured prompt (list of Message objects) for LLM consumption.
    Combines system prompt instructions, retrieved semantic chunks context,
    conversation history, and the user's latest message.
    """

    def __init__(self, context_template: str = "Relevant Context:\n{context}"):
        self.context_template = context_template

    def build(
        self,
        system_prompt: str,
        retrieved_chunks: list[Chunk],
        current_conversation: list[Message],
        current_user_message: str,
    ) -> list[Message]:
        """
        Build the final list of structured messages.
        """
        # Format the retrieved semantic context
        context_str = ""
        if retrieved_chunks:
            context_blocks = []
            for chunk in retrieved_chunks:
                context_blocks.append(f"---\n{chunk.text}")
            context_str = "\n".join(context_blocks)

        # Build the system message incorporating context if available
        full_system_content = system_prompt
        if context_str:
            formatted_context = self.context_template.format(context=context_str)
            full_system_content = f"{system_prompt}\n\n{formatted_context}"

        messages = [Message(role="system", content=full_system_content)]

        # Append existing conversation history
        messages.extend(current_conversation)

        # Append the new user message
        messages.append(Message(role="user", content=current_user_message))

        return messages

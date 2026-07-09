from typing import List, Optional
from packages.knowledge.schemas import Document


class KnowledgeSummarizer:
    """Handles condensing and summarizing documents or retrieval contexts."""

    def __init__(self, llm_generate_fn=None):
        """Initializes with an optional function to generate text from an LLM.

        Args:
            llm_generate_fn: A function that takes a prompt string and returns a string response.
        """
        self.llm_generate = llm_generate_fn

    def summarize_document(self, document: Document, max_length: int = 200) -> str:
        """Generates a summary of a document."""
        if self.llm_generate:
            prompt = (
                f"Summarize the following document in under {max_length} characters:\n\n"
                f"{document.content}"
            )
            return self.llm_generate(prompt)
        
        # Simple fallback (first 3 sentences or prefix) if no LLM is provided
        sentences = document.content.split(". ")
        fallback_summary = ". ".join(sentences[:3])
        if len(fallback_summary) > max_length:
            return fallback_summary[:max_length] + "..."
        return fallback_summary

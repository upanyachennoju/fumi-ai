import re
from typing import Any, Dict, List


class MetadataExtractor:
    """Extracts structured metadata, keywords, and facts from unstructured text."""

    def __init__(self, llm_generate_fn=None):
        self.llm_generate = llm_generate_fn

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extracts key terms from the text."""
        if self.llm_generate:
            prompt = (
                f"Extract up to {max_keywords} comma-separated keywords from this text:\n\n"
                f"{text}"
            )
            response = self.llm_generate(prompt)
            return [k.strip() for k in response.split(",") if k.strip()][:max_keywords]

        # Rule-based fallback: find words with capitalization or length > 5
        words = re.findall(r"\b[a-zA-Z]{6,}\b", text)
        unique_words = list(dict.fromkeys(words))
        return unique_words[:max_keywords]

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts named entities (e.g., Dates, Names, Places)."""
        entities: Dict[str, List[str]] = {"dates": [], "proper_nouns": []}
        
        # Match potential dates (e.g. YYYY-MM-DD or Month DD, YYYY)
        date_pattern = r"\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b"
        entities["dates"] = list(set(re.findall(date_pattern, text)))

        # Match proper nouns (capitalized words not at start of sentence, or sequences)
        proper_noun_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
        found_nouns = re.findall(proper_noun_pattern, text)
        entities["proper_nouns"] = list(set(found_nouns))[:10]

        return entities

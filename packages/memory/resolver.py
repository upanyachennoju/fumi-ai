import inspect
from dataclasses import dataclass
from typing import Any

from packages.knowledge.index import VectorIndex, SearchResult
from packages.providers.base import BaseLLMProvider
from .schemas import MemoryExtraction

try:
    from config import similarity_threshold
except ImportError:
    similarity_threshold = 0.90


@dataclass
class MemoryOperation:
    action: str  # "create", "update", "ignore"
    category: str  # singular form: "preference", "goal", "project", "person", "habit", "memory"
    extracted_memory: str
    existing_memory: SearchResult | None = None


class MemoryResolver:
    """
    Decides whether to CREATE, UPDATE, or IGNORE extracted memories
    by comparing them to existing memories retrieved from ChromaDB.
    """

    def __init__(
        self,
        index: VectorIndex,
        llm_provider: BaseLLMProvider,
        threshold: float | None = None
    ):
        self.index = index
        self.llm_provider = llm_provider
        self.threshold = threshold if threshold is not None else similarity_threshold

    async def resolve(self, extraction: MemoryExtraction) -> list[MemoryOperation]:
        """
        Processes a MemoryExtraction and returns a structured list of MemoryOperations.
        """
        if extraction.ignore:
            return []

        operations = []
        categories = ["preferences", "goals", "projects", "people", "habits", "memories"]

        for category in categories:
            items = getattr(extraction, category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not item or not isinstance(item, str):
                    continue
                op = await self.resolve_item(item.strip(), category)
                operations.append(op)

        return operations

    async def resolve_item(self, item: str, category_plural: str) -> MemoryOperation:
        """
        Resolves a single memory item by querying ChromaDB and potentially querying the LLM.
        """
        # Map category to singular type used in metadata and operation representation
        plural_to_singular = {
            "preferences": "preference",
            "goals": "goal",
            "projects": "project",
            "people": "person",
            "habits": "habit",
            "memories": "memory",
        }
        category_singular = plural_to_singular.get(category_plural, "memory")

        # 1. Search ChromaDB for the top 3 candidates of the same category
        results = await self.index.search(
            query_text=item,
            n_results=3,
            where={"type": category_singular}
        )

        if not results:
            return MemoryOperation(
                action="create",
                category=category_singular,
                extracted_memory=item
            )

        # 2. Find the candidate with the highest similarity score
        best_candidate = None
        best_score = -1.0
        for res in results:
            if res.score > best_score:
                best_score = res.score
                best_candidate = res

        # 3. Apply threshold logic
        if best_score >= self.threshold:
            return MemoryOperation(
                action="update",
                category=category_singular,
                extracted_memory=item,
                existing_memory=best_candidate
            )
        elif 0.70 <= best_score < self.threshold:
            decision = await self._ask_llm(category_singular, item, best_candidate.text)
            if decision == "UPDATE":
                return MemoryOperation(
                    action="update",
                    category=category_singular,
                    extracted_memory=item,
                    existing_memory=best_candidate
                )
            elif decision == "IGNORE":
                return MemoryOperation(
                    action="ignore",
                    category=category_singular,
                    extracted_memory=item,
                    existing_memory=best_candidate
                )
            else:
                return MemoryOperation(
                    action="create",
                    category=category_singular,
                    extracted_memory=item
                )
        else:
            return MemoryOperation(
                action="create",
                category=category_singular,
                extracted_memory=item
            )

    async def _ask_llm(self, category: str, new_content: str, existing_content: str) -> str:
        """
        Ask local LLM to decide whether a memory refers to the same concept/entity.
        Must reply with only UPDATE, CREATE, or IGNORE.
        """
        prompt = f"""You are Fumi's Memory Resolver.
Your task is to compare a newly extracted memory item against an existing memory candidate of the same category, and decide on the correct action.

Category: {category}
New Extracted Item: "{new_content}"
Existing Memory Candidate: "{existing_content}"

Decide whether:
1. The new item is about the exact same long-term memory, goal, preference, project, person, or habit as the existing candidate (and thus we should merge the information into it). Action: UPDATE.
2. The new item refers to a completely new, distinct long-term memory, goal, preference, project, person, or habit that is different from the existing candidate. Action: CREATE.
3. The new item is irrelevant, redundant, contains no useful new information, or should not be saved. Action: IGNORE.

You MUST reply with exactly one of the following words:
UPDATE
CREATE
IGNORE

Do not write any explanation, introduction, markdown blocks, or other text. Reply with only one word."""

        try:
            res = self.llm_provider.generate(prompt)
            if inspect.iscoroutine(res):
                result = await res
            else:
                result = res

            content = result["content"] if isinstance(result, dict) else result
            cleaned = content.strip().upper()

            if "UPDATE" in cleaned:
                return "UPDATE"
            elif "IGNORE" in cleaned:
                return "IGNORE"
            else:
                return "CREATE"
        except Exception:
            return "CREATE"

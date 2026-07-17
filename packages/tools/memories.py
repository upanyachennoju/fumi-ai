from typing import Any, Type
from pydantic import BaseModel
from packages.knowledge.retriever import Retriever
from .base import BaseTool
from .schemas import SearchMemoryArgs


class SearchMemoryTool(BaseTool):
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search the user's long-term memory vector index for matching information."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return SearchMemoryArgs

    async def execute(self, **kwargs: Any) -> list:
        chunks = await self.retriever.retrieve(
            query=kwargs["query"],
            n_results=kwargs["n_results"],
        )
        return [
            {
                "id": c.id,
                "text": c.text,
                "metadata": c.metadata,
            }
            for c in chunks
        ]

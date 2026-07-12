from typing import Any
from .index import VectorIndex
from .schemas import Chunk
from packages.providers.base import EmbeddingProvider


class Retriever:
    """
    Coordinates semantic search: generates an embedding for a user query,
    queries the Chroma index, and returns ranked Chunk objects.
    Does not know anything about prompts.
    """

    def __init__(self, index: VectorIndex, embedding_provider: EmbeddingProvider):
        self.index = index
        self.embedding_provider = embedding_provider

    async def retrieve(
        self, query: str, n_results: int = 5, where: dict[str, Any] | None = None
    ) -> list[Chunk]:
        """
        Given a user query, generates its embedding, searches VectorIndex,
        and returns a list of ranked Chunk dataclasses.
        """
        query_embedding = await self.embedding_provider.embed(query)

        results = self.index.search(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

        chunks = []
        for r in results:
            chunks.append(
                Chunk(
                    id=r["id"],
                    text=r["text"],
                    metadata=r["metadata"],
                )
            )
        return chunks

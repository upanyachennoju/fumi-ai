from pathlib import Path
from typing import Any
from dataclasses import dataclass
import chromadb

from packages.providers.base import EmbeddingProvider

@dataclass
class SearchResult:
    id: str
    score: float
    text: str
    metadata: dict[str, Any]


class VectorIndex:
    """
    Wrapper around ChromaDB for semantic vector indexing and retrieval.
    """

    def __init__(
        self,
        persist_directory: str | Path = "./chroma",
        collection_name: str = "fumi_index",
        embedding_provider: EmbeddingProvider | None = None
    ):
        self.persist_directory = Path(persist_directory)
        self.client = chromadb.PersistentClient(path=str(self.persist_directory))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embedding_provider = embedding_provider

    def add(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
        embeddings: list[list[float]],
    ):
        """
        Add chunks with pre-computed embeddings to the Chroma collection.
        """
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def delete(self, ids: list[str] | None = None, where: dict[str, Any] | None = None):
        """
        Delete chunks from the Chroma collection by IDs or metadata filter.
        """
        if ids is not None:
            self.collection.delete(ids=ids)
        elif where is not None:
            self.collection.delete(where=where)

    async def search(
        self,
        query_embeddings: list[list[float]] | None = None,
        query_text: str | None = None,
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Query the Chroma collection using pre-computed embeddings or raw query text.
        Returns a formatted list of SearchResult objects.
        """
        if query_embeddings is None and query_text is not None:
            if self.embedding_provider is None:
                from packages.providers.ollama import OllamaEmbeddingProvider
                self.embedding_provider = OllamaEmbeddingProvider()
            embedded = await self.embedding_provider.embed(query_text)
            query_embeddings = [embedded]

        if query_embeddings is None:
            return []

        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where,
        )

        formatted = []
        if not results or not results.get("ids") or len(results["ids"]) == 0:
            return formatted

        # Determine metric space of collection for normalized scoring
        space = "l2"
        if self.collection.metadata and "hnsw:space" in self.collection.metadata:
            space = self.collection.metadata["hnsw:space"]

        ids = results["ids"][0]
        documents = results["documents"][0] if results.get("documents") else [None] * len(ids)
        metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for i in range(len(ids)):
            distance = distances[i]
            if space in ("cosine", "ip"):
                score = 1.0 - distance
            else:  # l2
                score = 1.0 - (distance / 2.0)
            score = max(0.0, min(1.0, score))

            formatted.append(SearchResult(
                id=ids[i],
                score=score,
                text=documents[i] if documents[i] is not None else "",
                metadata=metadatas[i] if metadatas[i] is not None else {}
            ))

        return formatted

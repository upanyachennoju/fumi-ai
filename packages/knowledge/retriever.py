from typing import List
from packages.knowledge.schemas import SearchResult
from packages.knowledge.indexer import VectorIndexer


class KnowledgeRetriever:
    """Retrieves relevant chunks and documents from the indexed knowledge base."""

    def __init__(self, indexer: VectorIndexer):
        self.indexer = indexer

    def retrieve(self, query: str, top_k: int = 3) -> List[SearchResult]:
        """Retrieves top-k closest chunks matching the query string."""
        raw_results = self.indexer.search_similarity(query, top_k=top_k)
        
        search_results = []
        for chunk, score in raw_results:
            search_results.append(
                SearchResult(
                    chunk=chunk,
                    score=score
                )
            )
            
        return search_results

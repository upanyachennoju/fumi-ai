import math
from typing import Dict, List
from packages.knowledge.schemas import Chunk
from packages.knowledge.embedder import BaseEmbedder


class VectorIndexer:
    """Manages indexing, storing, and computing vector similarity on chunks."""

    def __init__(self, embedder: BaseEmbedder):
        self.embedder = embedder
        # Map of chunk ID to Chunk object (which contains the embedding)
        self.index: Dict[str, Chunk] = {}

    def index_chunks(self, chunks: List[Chunk]) -> None:
        """Embeds and indexes a list of text chunks."""
        texts_to_embed = [c.content for c in chunks if c.embedding is None]
        
        if texts_to_embed:
            embeddings = self.embedder.embed_documents(texts_to_embed)
            embed_idx = 0
            for chunk in chunks:
                if chunk.embedding is None:
                    chunk.embedding = embeddings[embed_idx]
                    embed_idx += 1
        
        for chunk in chunks:
            self.index[chunk.id] = chunk

    def search_similarity(self, query: str, top_k: int = 5) -> List[tuple[Chunk, float]]:
        """Computes cosine similarity of query against indexed chunks."""
        query_vector = self.embedder.embed_query(query)
        results = []

        for chunk in self.index.values():
            if chunk.embedding is None:
                continue
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(query_vector, chunk.embedding)
            results.append((chunk, similarity))

        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

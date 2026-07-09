from typing import List
from packages.knowledge.schemas import Chunk, Document


class TextChunker:
    """Splits Documents into smaller, semantic chunks for indexing and retrieval."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> List[Chunk]:
        """Splits a Document into overlapping Chunks based on character count."""
        text = document.content
        chunks = []
        start = 0
        index = 0

        if not text:
            return []

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_content = text[start:end]
            
            chunk_id = f"{document.id}-c{index}"
            chunks.append(
                Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    content=chunk_content,
                    index=index,
                    metadata=document.metadata.copy(),
                )
            )
            
            index += 1
            # Move start pointer forward, considering the overlap
            start += self.chunk_size - self.chunk_overlap
            if start >= len(text) or (self.chunk_size - self.chunk_overlap) <= 0:
                break

        return chunks

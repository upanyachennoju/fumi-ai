from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Represents a document in the knowledge base."""
    id: str = Field(description="Unique identifier for the document")
    content: str = Field(description="Raw text content of the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata key-value pairs")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    """Represents a smaller text chunk derived from a document."""
    id: str = Field(description="Unique identifier for the chunk")
    document_id: str = Field(description="Reference to the parent document ID")
    content: str = Field(description="Text content of the chunk")
    index: int = Field(description="Sequence index of the chunk within the document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata inherited/extracted for this chunk")
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding representation")


class SearchResult(BaseModel):
    """Represents a search result returned from the retriever."""
    chunk: Chunk = Field(description="The matched chunk of text")
    score: float = Field(description="Similarity score (usually between 0.0 and 1.0)")

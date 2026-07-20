import re
from typing import Any
from .schemas import Chunk


def chunk(document: Any) -> list[Chunk]:
    """
    Convert a document into semantic chunks.
    Supports objects representing Goals, Journals, or Conversations.

    Returns a list of Chunk dataclass instances.
    """
    doc_id = getattr(document, "id", "unknown")

    # Determine the content/text of the document
    text = ""
    for attr in ["content", "description", "text"]:
        val = getattr(document, attr, None)
        if val is not None:
            text = val
            break

    # Build metadata from the object fields or metadata dict
    metadata = getattr(document, "metadata", {})
    if not metadata:
        metadata = {}
        # Fallback to gathering dataclass fields
        if hasattr(document, "__dataclass_fields__"):
            for field in document.__dataclass_fields__:
                if field not in ["content", "description", "text"]:
                    val = getattr(document, field, None)
                    if val is not None:
                        if hasattr(val, "isoformat"):
                            val = val.isoformat()
                        metadata[field] = val

    # Semantic markdown chunking
    # Match markdown headers starting with # up to ######
    header_pattern = re.compile(r"^(#{1,6}\s+.*)$", re.MULTILINE)
    matches = list(header_pattern.finditer(text))

    chunks_data = []

    if not matches:
        # Fallback: split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p in paragraphs:
            chunks_data.append((p, {}))
    else:
        # Split into sections based on headers
        first_text = text[:matches[0].start()].strip()
        if first_text:
            chunks_data.append((first_text, {}))

        for i, match in enumerate(matches):
            header_text = match.group(1).strip()
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start_pos:end_pos].strip()
            chunks_data.append((section_text, {"header": header_text}))

    # Construct Chunk objects
    chunks = []
    for index, (chunk_text, extra_meta) in enumerate(chunks_data):
        chunk_id = f"{doc_id}_chunk_{index}"
        chunk_metadata = {
            **metadata,
            **extra_meta,
            "chunk_index": index,
            "doc_id": doc_id,
        }
        chunks.append(Chunk(id=chunk_id, text=chunk_text, metadata=chunk_metadata))

    return chunks

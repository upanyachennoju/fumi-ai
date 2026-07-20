import asyncio
from typing import Any
from .vault import Vault
from .index import VectorIndex
from .chunker import chunk
from packages.providers.base import EmbeddingProvider

class Indexer:
    """
    Orchestrates the indexing pipeline: Reads Markdown from the Vault,
    semantically chunks it, generates embeddings using a provider, and
    saves them in the VectorIndex.
    """

    def __init__(self, vault: Vault, index: VectorIndex, embedding_provider: EmbeddingProvider):
        self.vault = vault
        self.index = index
        self.embedding_provider = embedding_provider

    async def index_document(self, document: Any):
        """
        Chunks a document, generates vector embeddings for each chunk concurrently,
        and adds them to the vector index.
        """
        chunks = chunk(document)
        if not chunks:
            return

        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # Generate embeddings concurrently using the async embedding provider
        embed_tasks = [self.embedding_provider.embed(text) for text in documents]
        embeddings = await asyncio.gather(*embed_tasks)

        self.index.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    async def delete_document(self, doc_id: str):
        """
        Delete all indexed chunks associated with a document ID.
        """
        self.index.delete(where={"doc_id": doc_id})

    async def rebuild_index(self):
        """
        Rebuilds the entire Chroma vector index from the Vault source of truth.
        """
        # Clear the Chroma collection by resetting it
        try:
            self.index.client.delete_collection(self.index.collection.name)
            self.index.collection = self.index.client.get_or_create_collection(self.index.collection.name)
        except Exception:
            try:
                self.index.delete(where={})
            except Exception:
                pass

        # Index all goals
        for goal in self.vault.list_goals():
            await self.index_document(goal)

        # Index all journals
        for journal in self.vault.list_journals():
            await self.index_document(journal)

        # Index all conversations
        for session_summary in self.vault.list_sessions():
            try:
                session, messages = self.vault.load_session(session_summary.id)
                content_parts = []
                for msg in messages:
                    role_header = "## User" if msg.role.lower() == "user" else "## Fumi"
                    content_parts.append(f"{role_header}\n\n{msg.content}")
                full_content = "\n\n".join(content_parts)

                # Construct a duck-typed document object for the conversation session
                class ConversationDoc:
                    def __init__(self, id_val, content_val, created_val, updated_val, title_val, model_val):
                        self.id = id_val
                        self.content = content_val
                        self.created = created_val
                        self.updated = updated_val
                        self.title = title_val
                        self.model = model_val

                doc = ConversationDoc(
                    id_val=session.id,
                    content_val=full_content,
                    created_val=session.created,
                    updated_val=session.updated,
                    title_val=session.title,
                    model_val=session.model,
                )
                await self.index_document(doc)
            except Exception:
                continue

import os
from typing import Dict, List, Optional
from packages.knowledge.schemas import Document


class KnowledgeVault:
    """Manages the persistent storage of documents and files in the local vault."""

    def __init__(self, vault_dir: str = "~/.fumi/vault"):
        self.vault_dir = os.path.expanduser(vault_dir)
        os.makedirs(self.vault_dir, exist_ok=True)
        # Placeholder for in-memory or database document registry
        self._documents: Dict[str, Document] = {}

    def add_document(self, document: Document) -> None:
        """Saves a document to the vault."""
        self._documents[document.id] = document
        # Optionally write file to disk
        file_path = os.path.join(self.vault_dir, f"{document.id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(document.content)

    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieves a document from the vault by its ID."""
        return self._documents.get(document_id)

    def list_documents(self) -> List[Document]:
        """Lists all documents stored in the vault."""
        return list(self._documents.values())

    def delete_document(self, document_id: str) -> bool:
        """Deletes a document from the vault."""
        if document_id in self._documents:
            del self._documents[document_id]
            file_path = os.path.join(self.vault_dir, f"{document_id}.txt")
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        return False

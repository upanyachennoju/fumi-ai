import json
import os
import tarfile
from datetime import datetime
from typing import List
from packages.knowledge.schemas import Document


class KnowledgeArchiver:
    """Manages backup, export, import, and archiving of knowledge vault contents."""

    def __init__(self, archive_dir: str = "~/.fumi/archive"):
        self.archive_dir = os.path.expanduser(archive_dir)
        os.makedirs(self.archive_dir, exist_ok=True)

    def export_vault(self, documents: List[Document], archive_name: str = "vault_backup") -> str:
        """Exports a list of Document schemas to a compressed tarball archive."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file_path = os.path.join(self.archive_dir, f"{archive_name}_{timestamp}.json")
        tar_file_path = os.path.join(self.archive_dir, f"{archive_name}_{timestamp}.tar.gz")

        # Write to temp JSON
        data = [doc.model_dump() for doc in documents]
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, default=str, indent=2)

        # Compress to tar.gz
        with tarfile.open(tar_file_path, "w:gz") as tar:
            tar.add(json_file_path, arcname=os.path.basename(json_file_path))

        # Cleanup temp JSON file
        if os.path.exists(json_file_path):
            os.remove(json_file_path)

        return tar_file_path

    def import_vault(self, archive_path: str) -> List[Document]:
        """Imports Document schemas from a previously exported archive."""
        documents: List[Document] = []
        if not os.path.exists(archive_path):
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                if member.name.endswith(".json"):
                    f = tar.extractfile(member)
                    if f:
                        content = f.read().decode("utf-8")
                        data_list = json.loads(content)
                        for item in data_list:
                            # Convert datetime string to datetime object
                            if "created_at" in item and isinstance(item["created_at"], str):
                                item["created_at"] = datetime.fromisoformat(item["created_at"])
                            if "updated_at" in item and isinstance(item["updated_at"], str):
                                item["updated_at"] = datetime.fromisoformat(item["updated_at"])
                            documents.append(Document(**item))
        return documents

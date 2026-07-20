import secrets
from datetime import datetime
from pathlib import Path
import frontmatter
from packages.knowledge.vault import Vault
from .schemas import MemoryExtraction


class MemoryManager:
    """
    Manages structured memory updates in the Vault by converting MemoryExtraction
    categories into Markdown files.
    """

    def __init__(self, vault: Vault):
        self.vault = vault

    def update_vault(self, extraction: MemoryExtraction) -> list[Path]:
        """
        Creates new Markdown files inside the appropriate Vault folders based on
        the memory categories extracted from the LLM.
        Returns a list of Path objects for all newly created files.
        """
        updated_paths = []
        if extraction.ignore:
            return updated_paths

        now = datetime.now()

        # Map extraction category keys to their vault target folder and semantic types
        categories = {
            "preferences": (self.vault.root / "preferences", "preference"),
            "goals": (self.vault.root / "goals", "goal"),
            "projects": (self.vault.root / "projects", "project"),
            "people": (self.vault.root / "people", "person"),
            "habits": (self.vault.root / "memories", "habit"),  # habits are stored in memories directory
            "memories": (self.vault.root / "memories", "memory"),
        }

        for key, (folder_path, entry_type) in categories.items():
            items = getattr(extraction, key, [])
            if not isinstance(items, list):
                continue

            for item in items:
                if not item or not isinstance(item, str):
                    continue

                # Generate a unique hex ID for the new memory entry
                entry_id = secrets.token_hex(4)
                file_path = folder_path / f"{entry_id}.md"

                # Ensure target folder directory exists
                folder_path.mkdir(parents=True, exist_ok=True)

                # Prepare frontmatter post payload
                post = frontmatter.Post(
                    content=item.strip(),
                    id=entry_id,
                    created=now.isoformat(),
                    updated=now.isoformat(),
                    type=entry_type,
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    frontmatter.dump(post, f)

                # Track path for downstream indexing trigger
                updated_paths.append(file_path)

        return updated_paths

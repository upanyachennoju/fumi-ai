import secrets
from datetime import datetime
from pathlib import Path
import frontmatter
from packages.knowledge.vault import Vault
from .schemas import MemoryExtraction


import re

def _normalize_text(text: str) -> str:
    """Normalize text for deduplication comparison (lowercase, strip non-alphanumeric)."""
    return re.sub(r'[\W_]+', '', text.strip().lower())


class MemoryManager:
    """
    Manages structured memory updates in the Vault by converting MemoryExtraction
    categories into Markdown files. Ensures duplicate memory files are not created.
    """

    def __init__(self, vault: Vault):
        self.vault = vault

    def _get_existing_normalized_map(self, folder_path: Path) -> dict[str, Path]:
        """
        Returns a mapping of normalized content string -> file Path for existing files in a folder.
        """
        existing = {}
        if not folder_path.exists():
            return existing

        for p in folder_path.glob("*.md"):
            try:
                post = frontmatter.load(p)
                content = post.content if post.content else ""
                norm = _normalize_text(content)
                if norm:
                    existing[norm] = p
            except Exception:
                continue
        return existing

    def update_vault(self, extraction: MemoryExtraction) -> list[Path]:
        """
        Creates new Markdown files inside the appropriate Vault folders based on
        the memory categories extracted from the LLM. Prevents duplicate memory entries.
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

            folder_path.mkdir(parents=True, exist_ok=True)
            existing_map = self._get_existing_normalized_map(folder_path)

            for item in items:
                if not item or not isinstance(item, str):
                    continue

                cleaned_item = item.strip()
                norm_item = _normalize_text(cleaned_item)

                # Skip creating a new file if a memory with the same content or substring overlap exists
                is_duplicate = False
                for existing_norm in existing_map.keys():
                    if norm_item == existing_norm:
                        is_duplicate = True
                        break
                    if len(norm_item) > 10 and len(existing_norm) > 10:
                        if norm_item in existing_norm or existing_norm in norm_item:
                            is_duplicate = True
                            break

                if is_duplicate:
                    continue

                # Generate a unique hex ID for the new memory entry
                entry_id = secrets.token_hex(4)
                file_path = folder_path / f"{entry_id}.md"

                # Prepare frontmatter post payload
                post = frontmatter.Post(
                    content=cleaned_item,
                    id=entry_id,
                    created=now.isoformat(),
                    updated=now.isoformat(),
                    type=entry_type,
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    frontmatter.dump(post, f)

                # Track path for downstream indexing trigger and add to existing map
                updated_paths.append(file_path)
                existing_map[norm_item] = file_path

        return updated_paths

    def clean_duplicates(self) -> int:
        """
        Scans all vault memory folders and deletes duplicate files with identical normalized content.
        Returns the total number of duplicate files removed.
        """
        folders = [
            self.vault.root / "preferences",
            self.vault.root / "goals",
            self.vault.root / "projects",
            self.vault.root / "people",
            self.vault.root / "memories",
        ]
        removed_count = 0

        for folder in folders:
            if not folder.exists():
                continue

            seen_contents = {}
            for p in sorted(folder.glob("*.md")):
                try:
                    post = frontmatter.load(p)
                    norm = _normalize_text(post.content if post.content else "")
                    if not norm:
                        continue

                    if norm in seen_contents:
                        # Duplicate file found! Remove it.
                        p.unlink()
                        removed_count += 1
                    else:
                        seen_contents[norm] = p
                except Exception:
                    continue

        return removed_count

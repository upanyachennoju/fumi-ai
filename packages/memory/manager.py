import secrets
import re
from datetime import datetime
from pathlib import Path
import frontmatter

from packages.knowledge.vault import Vault
from .resolver import MemoryResolver, MemoryOperation


def _normalize_text(text: str) -> str:
    """Normalize text for deduplication comparison (lowercase, strip non-alphanumeric)."""
    return re.sub(r'[\W_]+', '', text.strip().lower())


def _sanitize_filename(text: str) -> str:
    """Sanitize text to be used safely as a filename."""
    # Strip any leading markdown headings or lists
    cleaned = re.sub(r'^[#\-\*\s]+', '', text)
    # Remove characters that are unsafe for filenames: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/:*?"<>|]', '', cleaned)
    # Replace newlines or multiple spaces with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.strip()
    # Limit length to 50 chars to avoid very long filenames
    if len(cleaned) > 50:
        cleaned = cleaned[:50].strip()
    return cleaned


def merge_memory(post: frontmatter.Post, new_content: str):
    """
    Merges new content into the existing frontmatter Post object in a structured way.
    """
    new_content_stripped = new_content.strip()
    norm_new = _normalize_text(new_content_stripped)

    # 1. Check for list fields in the frontmatter (excluding system keys)
    system_keys = {"id", "created", "updated", "type", "aliases", "tags"}
    list_keys = [k for k, v in post.metadata.items() if isinstance(v, list) and k not in system_keys]

    # Special case: if "progress" is in post.metadata and is not a list, convert it
    if "progress" in post.metadata and not isinstance(post.metadata["progress"], list):
        val = post.metadata["progress"]
        post.metadata["progress"] = [val] if val else []
        list_keys = ["progress"] + [lk for lk in list_keys if lk != "progress"]

    if list_keys:
        # Append to the first found list field
        target_key = list_keys[0]
        existing_list = post.metadata[target_key]
        if not any(_normalize_text(str(item)) == norm_new for item in existing_list):
            existing_list.append(new_content_stripped)
    else:
        # No list keys in frontmatter. Merge into the content body.
        existing_body = post.content.strip() if post.content else ""
        if existing_body:
            # Check if new_content is already a substring of the existing body
            if norm_new not in _normalize_text(existing_body):
                # If existing body starts with bullet list, append as a list item
                if existing_body.startswith("-") or "\n-" in existing_body:
                    post.content = f"{existing_body}\n- {new_content_stripped}"
                elif existing_body.startswith("*") or "\n*" in existing_body:
                    post.content = f"{existing_body}\n* {new_content_stripped}"
                else:
                    post.content = f"{existing_body}\n\n{new_content_stripped}"
        else:
            post.content = new_content_stripped


class MemoryManager:
    """
    Manages structured memory updates in the Vault by converting MemoryOperations
    into Markdown files.
    """

    def __init__(self, vault: Vault, resolver: MemoryResolver):
        self.vault = vault
        self.resolver = resolver

    def _find_file_by_id(self, folder_path: Path, entry_id: str) -> Path | None:
        """Scan folder for a markdown file with the matching ID in filename or frontmatter."""
        if not folder_path.exists():
            return None

        # Check if direct name-based match exists (e.g. 05a89a9f.md)
        direct_path = folder_path / f"{entry_id}.md"
        if direct_path.exists():
            return direct_path

        # Scan folder files and load frontmatter to find ID match
        for p in folder_path.glob("*.md"):
            try:
                post = frontmatter.load(p)
                if post.metadata.get("id") == entry_id:
                    return p
            except Exception:
                continue
        return None

    def _generate_unique_path(self, folder_path: Path, title: str) -> Path:
        """Generate a safe, unique file path based on title/content."""
        sanitized = _sanitize_filename(title)
        if not sanitized:
            sanitized = secrets.token_hex(4)
        file_path = folder_path / f"{sanitized}.md"
        counter = 1
        while file_path.exists():
            file_path = folder_path / f"{sanitized} {counter}.md"
            counter += 1
        return file_path

    async def update_vault(self, operations: list[MemoryOperation]) -> list[Path]:
        """
        Creates or updates Vault Markdown files based on resolved memory operations.
        Returns a list of Path objects for all modified files.
        """
        updated_paths = []
        now = datetime.now()

        # Plural folder paths mapping (habits are in memories directory)
        categories = {
            "preference": (self.vault.root / "preferences", "preference"),
            "goal": (self.vault.root / "goals", "goal"),
            "project": (self.vault.root / "projects", "project"),
            "person": (self.vault.root / "people", "person"),
            "habit": (self.vault.root / "memories", "habit"),
            "memory": (self.vault.root / "memories", "memory"),
        }

        # Deduplicate and group operations to avoid redundant modifications
        unique_ops = []
        seen_keys = set()

        for op in operations:
            action = op.action
            category = op.category
            content = op.extracted_memory
            norm_content = _normalize_text(content)

            if action == "ignore":
                continue

            if action == "create":
                key = (category, "create", norm_content)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                unique_ops.append(op)
            elif action == "update":
                if not op.existing_memory:
                    continue
                existing_id = op.existing_memory.metadata.get("doc_id") or op.existing_memory.id
                if "_chunk_" in existing_id:
                    existing_id = existing_id.split("_chunk_")[0]
                content_key = (category, "update", existing_id, norm_content)
                if content_key in seen_keys:
                    continue
                seen_keys.add(content_key)
                unique_ops.append(op)

        for op in unique_ops:
            action = op.action
            category = op.category
            content = op.extracted_memory
            folder_path, entry_type = categories.get(category, (self.vault.root / "memories", "memory"))
            folder_path.mkdir(parents=True, exist_ok=True)

            if action == "create":
                file_path = self._generate_unique_path(folder_path, content)
                entry_id = secrets.token_hex(4)
                post = frontmatter.Post(
                    content=content,
                    id=entry_id,
                    created=now.isoformat(),
                    updated=now.isoformat(),
                    type=entry_type,
                )
            elif action == "update":
                existing_id = op.existing_memory.metadata.get("doc_id") or op.existing_memory.id
                if "_chunk_" in existing_id:
                    existing_id = existing_id.split("_chunk_")[0]
                file_path = self._find_file_by_id(folder_path, existing_id)

                if file_path and file_path.exists():
                    post = frontmatter.load(file_path)
                    merge_memory(post, content)
                    post.metadata["updated"] = now.isoformat()
                else:
                    # Fallback to create if existing file was deleted/not found
                    file_path = self._generate_unique_path(folder_path, content)
                    post = frontmatter.Post(
                        content=content,
                        id=existing_id,
                        created=now.isoformat(),
                        updated=now.isoformat(),
                        type=entry_type,
                    )
            else:
                continue

            with open(file_path, "w", encoding="utf-8") as f:
                frontmatter.dump(post, f)

            updated_paths.append(file_path)

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
                        p.unlink()
                        removed_count += 1
                    else:
                        seen_contents[norm] = p
                except Exception:
                    continue

        return removed_count

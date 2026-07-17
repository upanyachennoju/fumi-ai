import secrets
from datetime import datetime
from typing import Any, Type
import frontmatter
from pydantic import BaseModel
from packages.knowledge.vault import Vault
from .base import BaseTool
from .schemas import CreateNoteArgs, UpdateNoteArgs


def _serialize_note_post(post, note_id: str) -> dict:
    return {
        "id": post.metadata.get("id", note_id),
        "title": post.metadata.get("title", ""),
        "created": post.metadata.get("created", ""),
        "updated": post.metadata.get("updated", ""),
        "content": post.content,
    }


class CreateNoteTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "create_note"

    @property
    def description(self) -> str:
        return "Create a new note in the user's vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CreateNoteArgs

    async def execute(self, **kwargs: Any) -> dict:
        note_id = secrets.token_hex(4)
        notes_dir = self.vault.root / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        file_path = notes_dir / f"{note_id}.md"

        now = datetime.now()
        post = frontmatter.Post(
            content=kwargs["content"],
            id=note_id,
            title=kwargs["title"],
            created=now.isoformat(),
            updated=now.isoformat(),
            type="note",
        )

        with open(file_path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        return _serialize_note_post(post, note_id)


class UpdateNoteTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "update_note"

    @property
    def description(self) -> str:
        return "Update the title or content of an existing note in the user's vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return UpdateNoteArgs

    async def execute(self, **kwargs: Any) -> dict:
        note_id = kwargs["note_id"]
        notes_dir = self.vault.root / "notes"
        file_path = notes_dir / f"{note_id}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"Note with ID '{note_id}' not found.")

        post = frontmatter.load(file_path)

        # Apply updates if provided
        if kwargs.get("title") is not None:
            post.metadata["title"] = kwargs["title"]
        if kwargs.get("content") is not None:
            post.content = kwargs["content"]

        post.metadata["updated"] = datetime.now().isoformat()

        with open(file_path, "w", encoding="utf-8") as f:
            frontmatter.dump(post, f)

        return _serialize_note_post(post, note_id)

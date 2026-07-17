from typing import Any, Type
from pydantic import BaseModel
from packages.knowledge.vault import Vault
from .base import BaseTool
from .schemas import CreateJournalArgs


def _serialize_journal(journal) -> dict:
    return {
        "id": journal.id,
        "created": journal.created.isoformat() if hasattr(journal.created, "isoformat") else str(journal.created),
        "updated": journal.updated.isoformat() if hasattr(journal.updated, "isoformat") else str(journal.updated),
        "content": journal.content,
    }


class CreateJournalTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "create_journal"

    @property
    def description(self) -> str:
        return "Create a new daily journal entry in the user's vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CreateJournalArgs

    async def execute(self, **kwargs: Any) -> dict:
        journal = self.vault.create_journal(content=kwargs["content"])
        return _serialize_journal(journal)

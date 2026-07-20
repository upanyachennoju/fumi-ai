from typing import Any, Type
from pydantic import BaseModel, Field
from packages.knowledge.vault import Vault
from .base import BaseTool


class CreateCheckinArgs(BaseModel):
    message: str = Field(..., description="The generated check-in accountability message.")


class MarkCheckinReadArgs(BaseModel):
    checkin_id: str = Field(..., description="The unique ID of the check-in notification to mark as read.")


class CreateCheckinTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "create_checkin"

    @property
    def description(self) -> str:
        return "Save an LLM-generated accountability check-in notification to the vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CreateCheckinArgs

    async def execute(self, **kwargs: Any) -> dict:
        return self.vault.create_checkin(kwargs["message"])


class ListPendingCheckinsTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "list_pending_checkins"

    @property
    def description(self) -> str:
        return "List all unread/pending check-in notifications from the vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        class EmptyArgs(BaseModel):
            pass
        return EmptyArgs

    async def execute(self, **kwargs: Any) -> list:
        return self.vault.list_pending_checkins()


class MarkCheckinReadTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "mark_checkin_read"

    @property
    def description(self) -> str:
        return "Mark a check-in notification as read by its unique ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return MarkCheckinReadArgs

    async def execute(self, **kwargs: Any) -> dict:
        success = self.vault.mark_checkin_as_read(kwargs["checkin_id"])
        return {"id": kwargs["checkin_id"], "success": success}

from datetime import datetime
from typing import Any, Type, Optional
from pydantic import BaseModel, Field
from packages.knowledge.vault import Vault
from .base import BaseTool


def _serialize_reminder(reminder) -> dict:
    return {
        "id": reminder.id,
        "text": reminder.text,
        "due_time": reminder.due_time.isoformat() if hasattr(reminder.due_time, "isoformat") else str(reminder.due_time),
        "status": reminder.status,
        "created_at": reminder.created_at.isoformat() if hasattr(reminder.created_at, "isoformat") else str(reminder.created_at),
    }


class CreateReminderArgs(BaseModel):
    text: str = Field(..., description="The reminder text content (e.g. 'Water the plants').")
    due_time: datetime = Field(..., description="The ISO 8601 date and time when the reminder is due.")


class UpdateReminderArgs(BaseModel):
    reminder_id: str = Field(..., description="ID of the reminder to update.")
    text: Optional[str] = Field(None, description="Updated reminder text.")
    due_time: Optional[datetime] = Field(None, description="Updated ISO 8601 date/time when due.")
    status: Optional[str] = Field(None, description="Updated status, e.g., 'pending', 'triggered', 'dismissed'.")


class DeleteReminderArgs(BaseModel):
    reminder_id: str = Field(..., description="ID of the reminder to delete.")


class CreateReminderTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "create_reminder"

    @property
    def description(self) -> str:
        return "Create a new scheduled reminder."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CreateReminderArgs

    async def execute(self, **kwargs: Any) -> dict:
        reminder = self.vault.create_reminder(
            text=kwargs["text"],
            due_time=kwargs["due_time"]
        )
        return _serialize_reminder(reminder)


class ListRemindersTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "list_reminders"

    @property
    def description(self) -> str:
        return "List all reminders stored in the vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        class EmptyArgs(BaseModel):
            pass
        return EmptyArgs

    async def execute(self, **kwargs: Any) -> list:
        reminders = self.vault.list_reminders()
        return [_serialize_reminder(r) for r in reminders]


class UpdateReminderTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "update_reminder"

    @property
    def description(self) -> str:
        return "Update properties of an existing reminder by its ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return UpdateReminderArgs

    async def execute(self, **kwargs: Any) -> dict:
        reminder = self.vault.update_reminder(
            reminder_id=kwargs["reminder_id"],
            text=kwargs.get("text"),
            due_time=kwargs.get("due_time"),
            status=kwargs.get("status")
        )
        return _serialize_reminder(reminder)


class DeleteReminderTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "delete_reminder"

    @property
    def description(self) -> str:
        return "Delete a reminder by its ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return DeleteReminderArgs

    async def execute(self, **kwargs: Any) -> dict:
        success = self.vault.delete_reminder(kwargs["reminder_id"])
        return {"id": kwargs["reminder_id"], "deleted": success}

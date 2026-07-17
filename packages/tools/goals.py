from typing import Any, Type
from pydantic import BaseModel
from packages.knowledge.vault import Vault
from .base import BaseTool
from .schemas import CreateGoalArgs, UpdateGoalArgs, CompleteGoalArgs, DeleteGoalArgs, ListGoalsArgs


def _serialize_goal(goal) -> dict:
    return {
        "id": goal.id,
        "title": goal.title,
        "status": goal.status,
        "priority": goal.priority,
        "created": goal.created.isoformat() if hasattr(goal.created, "isoformat") else str(goal.created),
        "updated": goal.updated.isoformat() if hasattr(goal.updated, "isoformat") else str(goal.updated),
        "description": goal.description,
    }


class CreateGoalTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "create_goal"

    @property
    def description(self) -> str:
        return "Create a new goal in the user's vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CreateGoalArgs

    async def execute(self, **kwargs: Any) -> dict:
        goal = self.vault.create_goal(
            title=kwargs["title"],
            status=kwargs["status"],
            priority=kwargs["priority"],
            description=kwargs["description"],
        )
        return _serialize_goal(goal)


class UpdateGoalTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "update_goal"

    @property
    def description(self) -> str:
        return "Update properties of an existing goal by its ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return UpdateGoalArgs

    async def execute(self, **kwargs: Any) -> dict:
        goal = self.vault.update_goal(
            goal_id=kwargs["goal_id"],
            title=kwargs.get("title"),
            status=kwargs.get("status"),
            priority=kwargs.get("priority"),
            description=kwargs.get("description"),
        )
        return _serialize_goal(goal)


class CompleteGoalTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "complete_goal"

    @property
    def description(self) -> str:
        return "Mark an existing goal as completed by its ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return CompleteGoalArgs

    async def execute(self, **kwargs: Any) -> dict:
        goal = self.vault.complete_goal(goal_id=kwargs["goal_id"])
        return _serialize_goal(goal)


class DeleteGoalTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "delete_goal"

    @property
    def description(self) -> str:
        return "Delete a goal from the user's vault by its ID."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return DeleteGoalArgs

    async def execute(self, **kwargs: Any) -> dict:
        self.vault.delete_goal(goal_id=kwargs["goal_id"])
        return {"id": kwargs["goal_id"], "deleted": True}


class ListGoalsTool(BaseTool):
    def __init__(self, vault: Vault):
        self.vault = vault

    @property
    def name(self) -> str:
        return "list_goals"

    @property
    def description(self) -> str:
        return "List all goals currently stored in the user's vault."

    @property
    def args_schema(self) -> Type[BaseModel]:
        return ListGoalsArgs

    async def execute(self, **kwargs: Any) -> list:
        goals = self.vault.list_goals()
        return [_serialize_goal(g) for g in goals]

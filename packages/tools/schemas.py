from typing import Optional
from pydantic import BaseModel, Field


# --- Goals Tool Args ---
class CreateGoalArgs(BaseModel):
    title: str = Field(..., description="The title of the goal (e.g. 'Exercise')")
    status: str = Field("todo", description="The initial status (e.g. 'todo', 'active', 'completed')")
    priority: str = Field("medium", description="The goal priority (e.g. 'low', 'medium', 'high')")
    description: str = Field("", description="A detailed description of the goal")


class UpdateGoalArgs(BaseModel):
    goal_id: str = Field(..., description="The 6-character hex ID of the goal to update")
    title: Optional[str] = Field(None, description="The new title of the goal")
    status: Optional[str] = Field(None, description="The new status of the goal")
    priority: Optional[str] = Field(None, description="The new priority of the goal")
    description: Optional[str] = Field(None, description="The new description of the goal")


class CompleteGoalArgs(BaseModel):
    goal_id: str = Field(..., description="The 6-character hex ID of the goal to complete")


class DeleteGoalArgs(BaseModel):
    goal_id: str = Field(..., description="The 6-character hex ID of the goal to delete")


class ListGoalsArgs(BaseModel):
    pass


# --- Journal Tool Args ---
class CreateJournalArgs(BaseModel):
    content: str = Field(..., description="The markdown content of the daily journal entry")


# --- Notes Tool Args ---
class CreateNoteArgs(BaseModel):
    title: str = Field(..., description="The title of the note")
    content: str = Field(..., description="The markdown content of the note")


class UpdateNoteArgs(BaseModel):
    note_id: str = Field(..., description="The unique ID of the note to update")
    title: Optional[str] = Field(None, description="The new title of the note")
    content: Optional[str] = Field(None, description="The new markdown content of the note")


# --- Memory Tool Args ---
class SearchMemoryArgs(BaseModel):
    query: str = Field(..., description="The semantic search query (e.g. 'user likes espresso')")
    n_results: int = Field(5, description="The number of search results to return")

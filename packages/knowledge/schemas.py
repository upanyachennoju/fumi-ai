from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class ConversationSession:
    id: str
    created: datetime
    updated: datetime
    title: str = "New Conversation"
    model: str = ""
    message_count: int = 0


@dataclass
class Message:
    role: str
    content: str


@dataclass
class Goal:
    id: str
    title: str
    status: str
    priority: str
    created: datetime
    updated: datetime
    description: str


@dataclass
class Journal:
    id: str
    created: datetime
    updated: datetime
    content: str


@dataclass
class Chunk:
    id: str
    text: str
    metadata: dict[str, Any]


@dataclass
class MemoryExtraction:
    """
    Structured long-term memory extracted from a conversation.
    """
    preferences: list[str]
    goals: list[str]
    projects: list[str]
    people: list[str]
    habits: list[str]
    memories: list[str]
    ignore: bool = False
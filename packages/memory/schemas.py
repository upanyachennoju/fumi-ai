from dataclasses import dataclass


@dataclass
class MemoryExtraction:
    """
    Structured long-term memory points extracted from a conversation.
    """
    preferences: list[str]
    goals: list[str]
    projects: list[str]
    people: list[str]
    habits: list[str]
    memories: list[str]
    ignore: bool = False

from enum import Enum

class VaultDirectory(str, Enum):
    CONVERSATIONS = "conversations"
    GOALS = "goals"
    JOURNALS = "journals"
    MEMORIES = "memories"
    PREFERENCES = "preferences"
    PEOPLE = "people"
    PROJECTS = "projects"
    DAILY = "daily"
    ARCHIVE = "archive"

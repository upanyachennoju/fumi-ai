from abc import ABC, abstractmethod
from typing import Any, Type
from pydantic import BaseModel


class BaseTool(ABC):
    """
    Abstract base class for all Fumi tools.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the tool (e.g. 'create_goal')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A detailed description of what the tool does, used by the LLM."""
        pass

    @property
    @abstractmethod
    def args_schema(self) -> Type[BaseModel]:
        """The Pydantic model class representing the tool arguments."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool asynchronously with the validated arguments."""
        pass


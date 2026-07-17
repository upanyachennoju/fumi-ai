from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from .base import BaseTool


class ToolRegistry:
    """
    Registry for registering, describing, and executing Fumi tools.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """
        Register a tool instance into the registry.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool with name '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Retrieve a tool instance by its name.
        """
        return self._tools.get(name)

    def list_tools(self) -> List[BaseTool]:
        """
        Get a list of all registered tools.
        """
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        Returns JSON-schema representations of all registered tools
        suitable for feeding to an LLM context.
        """
        schemas = []
        for name, tool in self._tools.items():
            schemas.append(
                {
                    "name": name,
                    "description": tool.description,
                    "parameters": tool.args_schema.model_json_schema(),
                }
            )
        return schemas

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates arguments against the tool's schema and executes the tool.
        Returns a structured dict matching success/result/error.
        """
        tool = self.get_tool(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found."}

        try:
            # Validate input arguments
            validated_args = tool.args_schema(**args)
            # Execute and retrieve the result using model_dump values
            result = await tool.execute(**validated_args.model_dump())
            return {"success": True, "result": result}
        except ValidationError as e:
            return {"success": False, "error": f"Validation Error: {e.errors()}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


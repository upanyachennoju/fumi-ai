import sys
from pathlib import Path
import asyncio

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex
from packages.knowledge.retriever import Retriever
from packages.providers.ollama import OllamaEmbeddingProvider
from packages.tools.registry import ToolRegistry
from packages.tools.goals import CreateGoalTool, UpdateGoalTool, CompleteGoalTool, DeleteGoalTool, ListGoalsTool
from packages.tools.journal import CreateJournalTool
from packages.tools.notes import CreateNoteTool, UpdateNoteTool
from packages.tools.memories import SearchMemoryTool


async def main():
    print("Initializing Fumi Tools Verification...")
    vault = Vault()
    index = VectorIndex(persist_directory="./chroma")
    embedder = OllamaEmbeddingProvider()
    retriever = Retriever(index, embedder)

    # Initialize ToolRegistry
    registry = ToolRegistry()

    # Register all tools
    registry.register(CreateGoalTool(vault))
    registry.register(UpdateGoalTool(vault))
    registry.register(CompleteGoalTool(vault))
    registry.register(DeleteGoalTool(vault))
    registry.register(ListGoalsTool(vault))
    registry.register(CreateJournalTool(vault))
    registry.register(CreateNoteTool(vault))
    registry.register(UpdateNoteTool(vault))
    registry.register(SearchMemoryTool(retriever))

    print(f"Registered tools: {[t.name for t in registry.list_tools()]}")

    # Inspect JSON schemas
    print("\n--- Tool Schemas for LLM ---")
    schemas = registry.get_schemas()
    for s in schemas:
        print(f"Name: {s['name']}\nDescription: {s['description']}\nParameters: {list(s['parameters']['properties'].keys())}\n")

    # 1. Test Create Goal Tool Execution
    print("Testing create_goal tool...")
    goal_res = await registry.execute_tool(
        "create_goal",
        {
            "title": "Study Python",
            "status": "todo",
            "priority": "high",
            "description": "Learn async tool calling in Fumi.",
        },
    )
    print(f"Create Goal Result: {goal_res}")
    goal_id = goal_res["result"]["id"]

    # 2. Test Complete Goal Tool Execution
    print("\nTesting complete_goal tool...")
    complete_res = await registry.execute_tool("complete_goal", {"goal_id": goal_id})
    print(f"Complete Goal Result: {complete_res}")

    # 3. Test Create Journal Tool Execution
    print("\nTesting create_journal tool...")
    journal_res = await registry.execute_tool(
        "create_journal", {"content": "Tested Fumi tool calling framework successfully today!"}
    )
    print(f"Create Journal Result: {journal_res}")

    # 4. Test Create Note Tool Execution
    print("\nTesting create_note tool...")
    note_res = await registry.execute_tool(
        "create_note", {"title": "Fumi Project Idea", "content": "Build memory pipelines."}
    )
    print(f"Create Note Result: {note_res}")
    note_id = note_res["result"]["id"]

    # 5. Test Update Note Tool Execution
    print("\nTesting update_note tool...")
    update_note_res = await registry.execute_tool(
        "update_note",
        {
            "note_id": note_id,
            "title": "Fumi Project Idea (Updated)",
            "content": "Build memory pipelines + tool calling.",
        },
    )
    print(f"Update Note Result: {update_note_res}")

    # 6. Test Search Memory Tool Execution
    print("\nTesting search_memory tool...")
    search_res = await registry.execute_tool("search_memory", {"query": "espresso", "n_results": 2})
    print(f"Search Memory Result: {search_res}")


if __name__ == "__main__":
    asyncio.run(main())

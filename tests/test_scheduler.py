import sys
from pathlib import Path
import asyncio
from datetime import datetime, timedelta
import pytest

# Bootstrap project root to allow importing packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.knowledge.vault import Vault
from packages.knowledge.index import VectorIndex
from packages.knowledge.retriever import Retriever
from packages.providers.ollama import OllamaEmbeddingProvider
from packages.tools.registry import ToolRegistry
from packages.tools.goals import CreateGoalTool, ListGoalsTool
from packages.tools.memories import SearchMemoryTool
from packages.tools.checkins import CreateCheckinTool, ListPendingCheckinsTool, MarkCheckinReadTool
from packages.tools.reminders import CreateReminderTool, ListRemindersTool, UpdateReminderTool, DeleteReminderTool
from packages.schedulers.scheduler import FumiScheduler
from packages.schedulers.jobs import run_daily_checkin, run_reminder_check


class MockLLMProvider:
    def __init__(self, model="qwen3:4b"):
        self.model = model

    def generate(self, messages):
        return {
            "content": "Keep studying Python! Consistency is key to mastering tool calling in Fumi.",
            "metrics": {"response_time_sec": 0.1, "tokens_generated": 10}
        }


@pytest.mark.asyncio
async def test_scheduler_and_jobs(tmp_path):
    # Initialize vault pointing to temp path to avoid dirtying actual vault
    vault = Vault(root=tmp_path)

    # Initialize index, embedding provider, and retriever
    index = VectorIndex(persist_directory=str(tmp_path / "chroma"))
    embedder = OllamaEmbeddingProvider()
    retriever = Retriever(index, embedder)

    # Build ToolRegistry
    registry = ToolRegistry()
    registry.register(CreateGoalTool(vault))
    registry.register(ListGoalsTool(vault))
    registry.register(SearchMemoryTool(retriever))
    registry.register(CreateCheckinTool(vault))
    registry.register(ListPendingCheckinsTool(vault))
    registry.register(MarkCheckinReadTool(vault))
    registry.register(CreateReminderTool(vault))
    registry.register(ListRemindersTool(vault))
    registry.register(UpdateReminderTool(vault))
    registry.register(DeleteReminderTool(vault))

    llm = MockLLMProvider()

    # 1. Test Reminder tool execution
    print("Testing reminder tools...")
    now = datetime.now()
    due = now + timedelta(seconds=2)

    # Create reminder
    reminder_res = await registry.execute_tool("create_reminder", {"text": "Take a short walk", "due_time": due})
    assert reminder_res["success"]
    assert reminder_res["result"]["text"] == "Take a short walk"
    assert reminder_res["result"]["status"] == "pending"
    reminder_id = reminder_res["result"]["id"]

    # List reminders
    list_res = await registry.execute_tool("list_reminders", {})
    assert list_res["success"]
    assert len(list_res["result"]) == 1

    # 2. Test Reminder Job trigger logic
    # First check: not due yet (current time < due time)
    await run_reminder_check(registry)

    # Reminder should still be pending
    list_res = await registry.execute_tool("list_reminders", {})
    assert list_res["result"][0]["status"] == "pending"

    # Simulate passing of time by modifying the reminder file due_time to be in the past
    past_due = now - timedelta(seconds=10)
    update_res = await registry.execute_tool(
        "update_reminder",
        {"reminder_id": reminder_id, "due_time": past_due}
    )
    assert update_res["success"]

    # Trigger job check again
    await run_reminder_check(registry)

    # Reminder should now be triggered
    list_res = await registry.execute_tool("list_reminders", {})
    assert list_res["result"][0]["status"] == "triggered"

    # A check-in notification should have been generated
    pending_checkins_res = await registry.execute_tool("list_pending_checkins", {})
    assert pending_checkins_res["success"]
    assert len(pending_checkins_res["result"]) == 1
    assert "Reminder: Take a short walk" in pending_checkins_res["result"][0]["message"]
    checkin_id = pending_checkins_res["result"][0]["id"]

    # Mark check-in read
    mark_read_res = await registry.execute_tool("mark_checkin_read", {"checkin_id": checkin_id})
    assert mark_read_res["success"]

    pending_checkins_res = await registry.execute_tool("list_pending_checkins", {})
    assert len(pending_checkins_res["result"]) == 0

    # 3. Test Daily Check-in Job
    print("Testing daily check-in accountability message generation...")
    # Add an active goal first so check-in triggers
    await registry.execute_tool("create_goal", {
        "title": "Study Python",
        "status": "in_progress",
        "priority": "high",
        "description": "Learn async tool calling in Fumi."
    })

    # Run check-in job
    await run_daily_checkin(registry, llm)

    # A new check-in should be available
    pending_checkins_res = await registry.execute_tool("list_pending_checkins", {})
    assert len(pending_checkins_res["result"]) == 1
    assert "Keep studying Python" in pending_checkins_res["result"][0]["message"]

    # 4. Test Scheduler init and lifespan start/shutdown
    print("Testing scheduler start/stop...")
    scheduler = FumiScheduler(registry, llm)
    scheduler.start(daily_interval_hours=0.01, reminder_interval_seconds=0.1)
    assert scheduler._is_running
    scheduler.shutdown()
    assert not scheduler._is_running

    print("All verification tests passed successfully!")

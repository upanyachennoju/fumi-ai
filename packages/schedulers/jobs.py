import logging
from datetime import datetime
import inspect

logger = logging.getLogger(__name__)


async def run_daily_checkin(registry, llm_provider):
    """
    Checks active goals and generates a daily accountability check-in message.
    """
    logger.info("Starting Daily Check-in Job...")
    try:
        # 1. List goals
        goals_res = await registry.execute_tool("list_goals", {})
        if not goals_res.get("success"):
            logger.error(f"Failed to list goals: {goals_res.get('error')}")
            return

        goals = goals_res["result"]
        active_goals = [g for g in goals if g.get("status") in ("todo", "in_progress")]

        if not active_goals:
            logger.info("No active goals found. Skipping daily accountability message.")
            return

        # 2. Check for overdue/inactive goals
        now = datetime.now()
        inactive_goals_info = []
        for g in active_goals:
            updated_str = g.get("updated")
            try:
                updated_dt = datetime.fromisoformat(updated_str)
                days_inactive = (now - updated_dt).days
            except Exception:
                days_inactive = 0

            inactive_goals_info.append(
                f"- Goal: '{g.get('title')}' (Status: {g.get('status')}, Priority: {g.get('priority')}). Inactive for {days_inactive} days."
            )

        # 3. Optionally retrieve relevant memories
        memories_res = await registry.execute_tool("search_memory", {"query": "user goals productivity habits", "n_results": 3})
        memories = memories_res.get("result", []) if memories_res.get("success") else []
        memories_text = "\n".join([f"- {m['text']}" for m in memories]) if memories else "No relevant memories found."

        # 4. Ask the LLM to generate a short accountability message
        goals_summary = "\n".join(inactive_goals_info)
        prompt = (
            "You are Fumi, a supportive, friendly personal AI companion. Below is a list of the user's active goals and their inactive days, along with some relevant context from their memories.\n\n"
            f"Active Goals:\n{goals_summary}\n\n"
            f"Context from Memories:\n{memories_text}\n\n"
            "Based on this, generate a short, encouraging accountability check-in message (1 or 2 sentences max). "
            "Address the user directly. Be friendly, warm, and brief. Do not use generic placeholders."
        )

        from packages.knowledge.schemas import Message
        messages = [
            Message(role="system", content="You are Fumi, a supportive personal AI companion."),
            Message(role="user", content=prompt)
        ]

        res = llm_provider.generate(messages)
        if inspect.iscoroutine(res):
            result = await res
        else:
            result = res

        llm_reply = result["content"] if isinstance(result, dict) else result

        # 5. Save the notification using CreateCheckinTool
        checkin_res = await registry.execute_tool("create_checkin", {"message": llm_reply})
        if checkin_res.get("success"):
            logger.info(f"Daily Check-in message generated and saved: {llm_reply}")
        else:
            logger.error(f"Failed to save check-in notification: {checkin_res.get('error')}")

    except Exception as e:
        logger.exception(f"Error in Daily Check-in Job: {e}")


async def run_reminder_check(registry):
    """
    Checks for pending reminders that are due, logs/triggers them, and creates check-ins.
    """
    logger.info("Starting Reminder Job...")
    try:
        reminders_res = await registry.execute_tool("list_reminders", {})
        if not reminders_res.get("success"):
            logger.error(f"Failed to list reminders: {reminders_res.get('error')}")
            return

        reminders = reminders_res["result"]
        now = datetime.now()

        for r in reminders:
            if r.get("status") != "pending":
                continue

            due_time_str = r.get("due_time")
            try:
                due_time = datetime.fromisoformat(due_time_str)
            except Exception:
                continue

            if due_time <= now:
                reminder_id = r["id"]
                reminder_text = r["text"]
                logger.info(f"Triggering reminder {reminder_id}: '{reminder_text}'")

                # Mark reminder as triggered
                update_res = await registry.execute_tool(
                    "update_reminder",
                    {"reminder_id": reminder_id, "status": "triggered"}
                )

                if not update_res.get("success"):
                    logger.error(f"Failed to update reminder status: {update_res.get('error')}")
                    continue

                # Create a check-in notification message
                notification_msg = f"Reminder: {reminder_text}"
                checkin_res = await registry.execute_tool("create_checkin", {"message": notification_msg})
                if not checkin_res.get("success"):
                    logger.error(f"Failed to save check-in for triggered reminder: {checkin_res.get('error')}")

    except Exception as e:
        logger.exception(f"Error in Reminder Job: {e}")

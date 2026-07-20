import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from packages.tools.registry import ToolRegistry
from packages.schedulers.jobs import run_daily_checkin, run_reminder_check

logger = logging.getLogger(__name__)


class FumiScheduler:
    """
    Core background scheduler for Fumi, responsible for orchestrating
    periodic jobs such as daily check-ins and reminder triggers.
    """

    def __init__(self, registry: ToolRegistry, llm_provider):
        self.registry = registry
        self.llm_provider = llm_provider
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self, daily_interval_hours: float = 24.0, reminder_interval_seconds: float = 30.0):
        """
        Starts the background scheduler and registers the default jobs.
        """
        if self._is_running:
            logger.warning("FumiScheduler is already running.")
            return

        logger.info("Starting Fumi background scheduler...")

        # Schedule the daily check-in accountability job
        self.scheduler.add_job(
            run_daily_checkin,
            "interval",
            hours=daily_interval_hours,
            args=[self.registry, self.llm_provider],
            id="daily_checkin",
            replace_existing=True
        )

        # Schedule the periodic reminder checker
        self.scheduler.add_job(
            run_reminder_check,
            "interval",
            seconds=reminder_interval_seconds,
            args=[self.registry],
            id="reminder_check",
            replace_existing=True
        )

        self.scheduler.start()
        self._is_running = True
        logger.info(
            f"FumiScheduler successfully started. (Daily check-in: {daily_interval_hours}h, "
            f"Reminder check: {reminder_interval_seconds}s)"
        )

    def shutdown(self):
        """
        Gracefully shuts down the background scheduler.
        """
        if not self._is_running:
            logger.warning("FumiScheduler is not currently running.")
            return

        self.scheduler.shutdown()
        self._is_running = False
        logger.info("FumiScheduler has been shut down.")

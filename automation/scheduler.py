# scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


def create_scheduler(briefing_job, reminder_job):
    scheduler = AsyncIOScheduler(timezone="America/New_York")

    scheduler.add_job(
        briefing_job,
        CronTrigger(hour=8, minute=0),
        id="daily_briefing",
        name="Daily Briefing",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.add_job(
        reminder_job,
        IntervalTrigger(minutes=30),
        id="reminder_check",
        name="Reminder Check",
        replace_existing=True,
    )

    return scheduler
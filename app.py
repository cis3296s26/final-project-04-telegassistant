# app.py
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# --- Swap these imports out as real implementations become ready ---
<<<<<<< Automation-role
from stubs.fake_db  import FakeDB
from stubs.fake_ai  import FakeAI
from stubs.fake_bot import FakeBot
=======
from data.database_client import DatabaseClient
from ai.llm_client        import LLMClient
from bot.telegram_client import TelegramBotClient
>>>>>>> local

from scheduler      import create_scheduler
from jobs.briefing  import run_daily_briefing
from jobs.reminders import run_reminder_check


async def main():
    logger.info("TeleGAssistant starting up...")

    # Initialize components
<<<<<<< Automation-role
    db  = FakeDB()
    ai  = FakeAI()
    bot = FakeBot()
=======
    db  = DatabaseClient(db_path=os.getenv("DB_PATH", "data/telegassistant.db"))
    ai  = LLMClient()
    bot = TelegramBotClient(token=os.getenv("BOT_TOKEN"))
>>>>>>> local

    db.connect()

    llm_ok = await ai.health_check()
    if not llm_ok:
        logger.warning("LLM server unreachable — briefings will use fallback")

    # Wire jobs with injected dependencies
    async def briefing_job():
        await run_daily_briefing(db, ai, bot)

    async def reminder_job():
        await run_reminder_check(db, bot)

    # --- WEEK 1 SMOKE TEST ---
    # Run both jobs immediately on startup so you can
    # see them work without waiting for 8 AM.
    logger.info("Running smoke test jobs...")
    await briefing_job()
    await reminder_job()
    logger.info("Smoke test complete.")

    # Start scheduler
    scheduler = create_scheduler(briefing_job, reminder_job)
    scheduler.start()
    logger.info("Scheduler started. Jobs will run on schedule.")

    # Start fake bot polling
    bot_task = asyncio.create_task(bot.start_polling())

    # Keep running until Ctrl+C
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass

    logger.info("Shutting down...")
    scheduler.shutdown(wait=False)
    bot_task.cancel()
    db.close()
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
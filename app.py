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

from data.database_client import DatabaseClient
from ai.llm_client        import LLMClient
from bot.telegram_client  import TelegramBotClient

from scheduler      import create_scheduler
from jobs.briefing  import run_daily_briefing
from jobs.reminders import run_reminder_check


async def main():
    logger.info("TeleGAssistant starting up...")

    db  = DatabaseClient(db_path=os.getenv("DB_PATH", "data/telegassistant.db"))
    ai  = LLMClient()
    bot = TelegramBotClient(token=os.getenv("BOT_TOKEN"), db=db, ai=ai)

    db.connect()

    llm_ok = await ai.health_check()
    if not llm_ok:
        logger.warning("LLM server unreachable — briefings will use fallback")

    async def briefing_job():
        await run_daily_briefing(db, ai, bot)

    async def reminder_job():
        await run_reminder_check(db, bot)

    logger.info("Startup complete. Briefings will run on schedule.")

    scheduler = create_scheduler(briefing_job, reminder_job)
    scheduler.start()
    logger.info("Scheduler started. Jobs will run on schedule.")

    bot_task = asyncio.create_task(bot.start_polling())

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

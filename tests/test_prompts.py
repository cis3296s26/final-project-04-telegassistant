# tests/test_prompts.py
# ============================================================
# Manual prompt engineering test — runs 3 scenarios against
# the real LLM and prints output for review.
# Run with: python -m tests.test_prompts
# ============================================================

import asyncio
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from ai.llm_client import LLMClient
from bot.telegram_client import TelegramBotClient
from jobs.briefing import _build_briefing_context

load_dotenv()


SCENARIOS = {
    "Scenario 1 — Normal day": {
        "name": "Sid",
        "events": [
            {"title": "Team standup", "time": "10:00 AM"},
        ],
        "tasks": [
            {"title": "Finish Software Design report", "due_date": date.today() + timedelta(days=1), "status": "in progress"},
            {"title": "Review teammate's PR",           "due_date": date.today() + timedelta(days=3), "status": "pending"},
        ],
        "deadlines": [
            {"id": 1, "title": "CIS 3850 Homework 6", "due_date": date.today() + timedelta(days=2)},
        ],
    },

    "Scenario 2 — Empty day": {
        "name": "Sid",
        "events":    [],
        "tasks":     [],
        "deadlines": [],
    },

    "Scenario 3 — High-load day": {
        "name": "Sid",
        "events": [
            {"title": "Team standup",        "time": "9:00 AM"},
            {"title": "Project demo",        "time": "1:00 PM"},
            {"title": "Office hours",        "time": "4:00 PM"},
        ],
        "tasks": [
            {"title": "Finish Software Design report",    "due_date": date.today(),                      "status": "in progress"},
            {"title": "Review teammate's PR",             "due_date": date.today(),                      "status": "pending"},
            {"title": "Submit AGI simulation writeup",    "due_date": date.today() + timedelta(days=1),  "status": "pending"},
            {"title": "Push TeleGAssistant branch",       "due_date": date.today() + timedelta(days=2),  "status": "in progress"},
            {"title": "Study for Wireless Networks exam", "due_date": date.today() + timedelta(days=4),  "status": "pending"},
        ],
        "deadlines": [
            {"id": 1, "title": "CIS 3850 Homework 6",      "due_date": date.today()},
            {"id": 2, "title": "Software Design final sub", "due_date": date.today() + timedelta(days=1)},
        ],
    },
}


async def run():
    client = LLMClient()
    bot    = TelegramBotClient(token=os.getenv("BOT_TOKEN"))
    chat_id = int(os.getenv("MY_CHAT_ID"))

    for label, data in SCENARIOS.items():
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"{'='*60}")

        context = _build_briefing_context(
            user_name=data["name"],
            tasks=data["tasks"],
            deadlines=data["deadlines"],
            events=data["events"],
            today=date.today(),
        )

        print("\n--- CONTEXT SENT TO LLM ---")
        print(context)
        print("\n--- LLM OUTPUT ---")

        try:
            output = await client.generate_briefing(context)
            print(output)
            header = f"*{label}*\n\n"
            await bot.send_message(chat_id=chat_id, text=header + output)
            print(f"[Sent to Telegram]")
        except Exception as e:
            print(f"[FAILED] {e}")

        print()


if __name__ == "__main__":
    asyncio.run(run())

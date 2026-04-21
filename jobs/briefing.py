# jobs/briefing.py
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def run_daily_briefing(db, ai_client, telegram_bot):
    logger.info("=== Daily Briefing Pipeline started ===")

    try:
        users = db.get_active_users()
    except Exception as e:
        logger.error(f"FATAL: Could not fetch users from DB: {e}")
        return

    if not users:
        logger.info("No active users. Briefing skipped.")
        return

    logger.info(f"Sending briefings to {len(users)} user(s)")

    tasks = [
        send_briefing_for_user(user, db, ai_client, telegram_bot)
        for user in users
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Briefing failed for user {users[i]['id']}: {result}")
        else:
            logger.info(f"Briefing sent to user {users[i]['id']}")

    logger.info("=== Daily Briefing Pipeline complete ===")


async def send_briefing_for_user(user, db, ai_client, telegram_bot):
    telegram_id = user["telegram_id"]
    user_id     = user["id"]

    today    = datetime.now().date()
    week_end = today + timedelta(days=7)

    tasks     = db.get_tasks_for_user(user_id, due_before=week_end)
    deadlines = db.get_deadlines_for_user(user_id, due_before=week_end)
    events    = db.get_events_for_user(user_id, on_date=today)

    context = _build_briefing_context(
        user_name=user.get("name", "there"),
        tasks=tasks,
        deadlines=deadlines,
        events=events,
        today=today,
    )

    try:
        briefing_text = await ai_client.generate_briefing(context)
    except Exception as e:
        logger.warning(f"LLM failed for user {telegram_id}: {e}. Using fallback.")
        briefing_text = _build_fallback_briefing(tasks, deadlines, events)

    for attempt in range(3):
        try:
            await telegram_bot.send_message(chat_id=telegram_id, text=briefing_text)
            return
        except Exception as e:
            logger.warning(f"Telegram send attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(5)

    raise RuntimeError(f"All send attempts failed for chat_id {telegram_id}")


def _build_briefing_context(user_name, tasks, deadlines, events, today):
    lines = [
        f"Today is {today.strftime('%A, %B %d, %Y')}.",
        f"Generate a friendly morning briefing for {user_name}.",
        "",
    ]

    if events:
        lines.append("TODAY'S EVENTS:")
        for e in events:
            lines.append(f"  - {e['title']} at {e['time']}")
        lines.append("")

    if tasks:
        lines.append("UPCOMING TASKS (next 7 days):")
        for t in tasks:
            lines.append(f"  - [{t['due_date']}] {t['title']} — {t['status']}")
        lines.append("")

    if deadlines:
        lines.append("DEADLINES:")
        for d in deadlines:
            days_left = (d["due_date"] - today).days
            urgency   = "TODAY" if days_left == 0 else f"in {days_left} day(s)"
            lines.append(f"  - {d['title']} due {urgency}")
        lines.append("")

    if not tasks and not deadlines and not events:
        lines.append("Nothing scheduled. Tell them to enjoy a light day.")

    lines.append("Keep the briefing concise, warm, and motivating. Use bullet points.")
    return "\n".join(lines)


def _build_fallback_briefing(tasks, deadlines, events):
    lines = ["☀️ Good morning! (AI unavailable — here's your plain summary)\n"]
    if events:
        lines.append("📅 Today: " + ", ".join(e["title"] for e in events))
    if deadlines:
        lines.append("⚠️ Deadlines: " + ", ".join(d["title"] for d in deadlines))
    if tasks:
        lines.append(f"✅ Tasks this week: {len(tasks)} pending")
    return "\n".join(lines) or "Nothing on your schedule today!"
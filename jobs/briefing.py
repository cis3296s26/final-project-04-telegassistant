# jobs/briefing.py
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def _get_weather():
    try:
        from ai.weather_client import get_weather
        return await get_weather()
    except Exception as e:
        logger.warning(f"Weather fetch failed: {e}")
        return None


async def _get_email_count() -> int | None:
    try:
        from ai.gmail_client import get_recent_emails, is_connected
        if not is_connected():
            return None
        emails = await get_recent_emails()
        return len(emails) if emails is not None else None
    except Exception as e:
        logger.warning(f"Email count fetch failed: {e}")
        return None


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

    weather = await _get_weather()

    # Count unread emails for the briefing summary line — full triage is /emails
    email_count = await _get_email_count()

    context = _build_briefing_context(
        user_name=user.get("name", "there"),
        tasks=tasks,
        deadlines=deadlines,
        events=events,
        weather=weather,
        email_count=email_count,
        today=today,
    )

    try:
        briefing_text = await ai_client.generate_briefing(context)
    except Exception as e:
        logger.warning(f"LLM failed for user {telegram_id}: {e}. Using fallback.")
        briefing_text = _build_fallback_briefing(tasks, deadlines, events, weather, email_count)

    for attempt in range(3):
        try:
            await telegram_bot.send_message(chat_id=telegram_id, text=briefing_text)
            return
        except Exception as e:
            logger.warning(f"Telegram send attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(5)

    raise RuntimeError(f"All send attempts failed for chat_id {telegram_id}")


def _build_briefing_context(user_name, tasks, deadlines, events, weather, email_count, today):
    day_str = today.strftime('%A, %B %d, %Y')
    prompt = f"""Generate a professional morning briefing for {user_name} for {day_str}.

Use this exact format with emojis and clean sections. Add blank lines between sections for spacing:

📋 YOUR BRIEFING — {day_str}

"""

    if weather:
        prompt += f"🌤️ Weather\n{weather['condition'].capitalize()}, {weather['temp']}°F | High {weather['high']}° / Low {weather['low']}°\n\n"

    if events:
        prompt += "📅 Today's Schedule\n"
        for e in events:
            prompt += f"{e['title']} at {e['time']}\n"
        prompt += "\n"

    if tasks:
        prompt += f"✅ Tasks ({len(tasks)} pending)\n"
        for t in tasks:
            prompt += f"{t['title']} — {t['status']}\n"
        prompt += "\n"

    if deadlines:
        prompt += f"⏰ Deadlines ({len(deadlines)} upcoming)\n"
        for d in deadlines:
            days_left = (d["due_date"] - today).days
            if days_left == 0:
                urgency = "🔴 TODAY"
            elif days_left == 1:
                urgency = "🟡 TOMORROW"
            else:
                urgency = f"🟢 {d['due_date'].strftime('%b %d')}"
            prompt += f"{urgency} — {d['title']}\n"
        prompt += "\n"

    if email_count is not None:
        if email_count > 0:
            prompt += f"📧 Emails\n{email_count} unread emails — send /emails to review.\n\n"
        else:
            prompt += "📧 Emails\nInbox clear.\n\n"

    if not tasks and not deadlines and not events:
        prompt += "You have a clear day ahead. Enjoy!\n\n"

    prompt += "Reformat the above data into the exact layout shown. Keep blank lines between sections. No extra commentary."
    return prompt


def _build_fallback_briefing(tasks, deadlines, events, weather=None, email_count=None):
    from datetime import date
    today = date.today()
    day_str = today.strftime('%A, %B %d, %Y')

    lines = [
        f"📋 YOUR BRIEFING — {day_str}",
        "(AI unavailable — here's your summary)",
        "",
    ]

    if weather:
        lines.append("🌤️ Weather")
        lines.append(f"{weather['condition'].capitalize()}, {weather['temp']}°F | High {weather['high']}° / Low {weather['low']}°")
        lines.append("")

    if events:
        lines.append("📅 Today's Schedule")
        for e in events:
            lines.append(f"{e['title']} at {e['time']}")
        lines.append("")

    if deadlines:
        lines.append(f"⏰ Deadlines ({len(deadlines)} upcoming)")
        for d in deadlines:
            days_left = (d["due_date"] - today).days
            if days_left == 0:
                urgency = "🔴 TODAY"
            elif days_left == 1:
                urgency = "🟡 TOMORROW"
            else:
                urgency = f"🟢 {d['due_date'].strftime('%b %d')}"
            lines.append(f"{urgency} — {d['title']}")
        lines.append("")

    if tasks:
        lines.append(f"✅ Tasks ({len(tasks)} pending)")
        for t in tasks:
            lines.append(f"{t['title']} — {t['status']}")
        lines.append("")

    if email_count is not None:
        lines.append("📧 Emails")
        if email_count > 0:
            lines.append(f"{email_count} unread — send /emails to review.")
        else:
            lines.append("Inbox clear.")
        lines.append("")

    if not tasks and not deadlines and not events:
        lines.append("You have a clear day ahead. Enjoy!")

    return "\n".join(lines)
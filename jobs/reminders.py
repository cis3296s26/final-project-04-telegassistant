# jobs/reminders.py
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

REMINDER_WINDOWS = [
    (timedelta(hours=24), "24h"),
    (timedelta(hours=2),  "2h"),
    (timedelta(minutes=30), "30min"),
]


async def run_reminder_check(db, telegram_bot):
    logger.info("Reminder check started")
    users = db.get_active_users()

    for user in users:
        try:
            await _check_reminders_for_user(user, db, telegram_bot)
        except Exception as e:
            logger.error(f"Reminder check failed for user {user['id']}: {e}")

    logger.info("Reminder check complete")


async def _check_reminders_for_user(user, db, telegram_bot):
    now         = datetime.now()
    user_id     = user["id"]
    telegram_id = user["telegram_id"]

    deadlines = db.get_all_upcoming_deadlines(user_id)

    for deadline in deadlines:
        due_dt    = deadline["due_datetime"]
        time_left = due_dt - now

        if time_left.total_seconds() < 0:
            continue

        for window, label in REMINDER_WINDOWS:
            if time_left <= window:
                already_sent = db.check_reminder_sent(
                    user_id=user_id,
                    item_id=deadline["id"],
                    item_type="deadline",
                    remind_type=label,
                )

                if not already_sent:
                    await _send_reminder(telegram_bot, telegram_id, deadline, label, time_left)
                    db.log_reminder_sent(
                        user_id=user_id,
                        item_id=deadline["id"],
                        item_type="deadline",
                        remind_type=label,
                    )
                break


async def _send_reminder(telegram_bot, chat_id, deadline, label, time_left):
    hours   = int(time_left.total_seconds() // 3600)
    minutes = int((time_left.total_seconds() % 3600) // 60)
    time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes} minutes"

    message = f"⏰ *Reminder:* {deadline['title']}\nDue in *{time_str}*"
    await telegram_bot.send_message(chat_id=chat_id, text=message)
    logger.info(f"Sent {label} reminder for '{deadline['title']}' to {chat_id}")
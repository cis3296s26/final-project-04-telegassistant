# jobs/reminders.py
import logging
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

REMINDER_WINDOWS = [
    (timedelta(hours=24),   "24h"),
    (timedelta(hours=2),    "2h"),
    (timedelta(minutes=30), "30min"),
]


def _get_reminder_label(time_left: timedelta) -> str | None:
    if time_left <= timedelta(minutes=30):
        return "30min"
    if time_left <= timedelta(hours=2):
        return "2h"
    if time_left <= timedelta(hours=24):
        return "24h"
    return None


async def run_reminder_check(db, telegram_bot):
    logger.info("Reminder check started")
    users = db.get_active_users()

    for user in users:
        try:
            await _check_deadline_reminders(user, db, telegram_bot)
            await _check_task_reminders(user, db, telegram_bot)
        except Exception as e:
            logger.error(f"Reminder check failed for user {user['id']}: {e}")

    await _fire_custom_reminders(db, telegram_bot)

    logger.info("Reminder check complete")


# ------------------------------------------------------------------ #
# Deadline reminders (unchanged behaviour)                           #
# ------------------------------------------------------------------ #

async def _check_deadline_reminders(user, db, telegram_bot):
    now         = datetime.now()
    user_id     = user["id"]
    telegram_id = user["telegram_id"]

    for deadline in db.get_all_upcoming_deadlines(user_id):
        time_left = deadline["due_datetime"] - now
        if time_left.total_seconds() < 0:
            continue

        label = _get_reminder_label(time_left)
        if not label:
            continue

        if not db.check_reminder_sent(user_id, deadline["id"], "deadline", label):
            msg = _format_time(time_left)
            await telegram_bot.send_message(
                chat_id=telegram_id,
                text=f"Reminder: {deadline['title']}\nDue in {msg}",
            )
            db.log_reminder_sent(user_id, deadline["id"], "deadline", label)
            logger.info(f"Sent {label} deadline reminder to {telegram_id}")


# ------------------------------------------------------------------ #
# Task reminders — 30-min warning + due-time completion prompt       #
# ------------------------------------------------------------------ #

async def _check_task_reminders(user, db, telegram_bot):
    now         = datetime.now()
    user_id     = user["id"]
    telegram_id = user["telegram_id"]

    for task in db.get_all_tasks_for_user(user_id):
        time_left = task["due_datetime"] - now
        seconds   = time_left.total_seconds()

        # 30-minute warning
        if 0 < seconds <= 1800:
            if not db.check_reminder_sent(user_id, task["id"], "task", "30min"):
                mins = int(seconds // 60)
                await telegram_bot.send_message(
                    chat_id=telegram_id,
                    text=f"Task due in {mins} minutes: {task['title']}",
                )
                db.log_reminder_sent(user_id, task["id"], "task", "30min")
                logger.info(f"Sent 30min task warning to {telegram_id}")

        # Due-time completion prompt (within 5-min window past due)
        elif -300 <= seconds <= 0:
            if not db.check_reminder_sent(user_id, task["id"], "task", "due"):
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("Yes, done", callback_data=f"TASK_DONE|{task['id']}"),
                    InlineKeyboardButton("Not yet",   callback_data=f"TASK_KEEP|{task['id']}"),
                ]])
                await telegram_bot.send_message_with_keyboard(
                    chat_id=telegram_id,
                    text=f"Your task is due: {task['title']}\n\nDid you complete it?",
                    keyboard=keyboard,
                )
                db.log_reminder_sent(user_id, task["id"], "task", "due")
                logger.info(f"Sent due-time task prompt to {telegram_id}")


# ------------------------------------------------------------------ #
# Custom reminders (/remindme)                                       #
# ------------------------------------------------------------------ #

async def _fire_custom_reminders(db, telegram_bot):
    now = datetime.now()

    for reminder in db.get_due_reminders(now):
        try:
            await telegram_bot.send_message(
                chat_id=reminder["telegram_id"],
                text=f"Reminder: {reminder['text']}",
            )
            logger.info(f"Fired reminder '{reminder['text']}' to {reminder['telegram_id']}")
        except Exception as e:
            logger.error(f"Failed to send reminder {reminder['id']}: {e}")
            continue

        if reminder["recurrence"] == "none":
            db.delete_reminder(reminder["id"])
        elif reminder["recurrence"] == "daily":
            db.update_reminder_time(reminder["id"], reminder["remind_at"] + timedelta(days=1))
        elif reminder["recurrence"] == "weekly":
            db.update_reminder_time(reminder["id"], reminder["remind_at"] + timedelta(weeks=1))


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _format_time(td: timedelta) -> str:
    total = int(td.total_seconds())
    hours   = total // 3600
    minutes = (total % 3600) // 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes} minutes"

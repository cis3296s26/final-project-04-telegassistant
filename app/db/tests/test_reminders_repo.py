from app.db.repositories.users_repo import get_or_create_user
from app.db.repositories.reminders_repo import (
    create_reminder,
    list_user_reminders,
    get_due_reminders,
    mark_reminder_sent,
    get_reminder_by_id,
)

user = get_or_create_user(
    telegram_user_id="12345",
    username="aidan",
    first_name="Aidan",
    last_name="Arena"
)

reminder = create_reminder(
    user_id=user["id"],
    title="Finish TeleGAssistant database work",
    remind_at="2026-04-07T18:00:00"
)

print("Created:", reminder)

all_reminders = list_user_reminders(user["id"])
print("All reminders:", all_reminders)

due_reminders = get_due_reminders("2026-04-07T20:00:00")
print("Due reminders:", due_reminders)

mark_reminder_sent(reminder["id"])

updated_reminder = get_reminder_by_id(reminder["id"])
print("Updated reminder:", updated_reminder)
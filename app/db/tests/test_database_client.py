from db.database_client import DatabaseClient

db = DatabaseClient()

user = db.get_or_create_user(
    telegram_user_id="777",
    username="client_test",
    first_name="Client",
    last_name="Test",
)
print("User:", user)

task = db.create_task(
    user_id=user["id"],
    title="Test DatabaseClient task",
    description="Created through DatabaseClient",
    due_at="2026-04-21T18:00:00",
    priority=1,
)
print("Task:", task)

reminder = db.create_reminder(
    user_id=user["id"],
    title="Test DatabaseClient reminder",
    remind_at="2026-04-21T12:00:00",
)
print("Reminder:", reminder)

print("Open tasks:", db.list_open_tasks(user["id"]))
print("User reminders:", db.list_user_reminders(user["id"]))
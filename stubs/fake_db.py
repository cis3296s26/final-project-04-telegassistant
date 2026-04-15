# stubs/fake_db.py
from datetime import date, datetime, timedelta
from interfaces import AbstractDB


class FakeDB(AbstractDB):
    """
    Fake database for local development and testing.
    Returns hardcoded realistic data.
    Replace with the real DatabaseClient once Data Engineer is ready.
    """

    # Class-level user store so registrations from /start persist across calls
    _users: list[dict] = [
        {"id": 1, "telegram_id": 6926513770, "name": "Andrew"},
    ]
    _next_id: int = 2

    def connect(self):
        print("[FakeDB] connect() called")

    def close(self):
        print("[FakeDB] close() called")

    def get_active_users(self):
        return list(FakeDB._users)

    def register_user(self, telegram_id: int, name: str) -> int:
        for user in FakeDB._users:
            if user["telegram_id"] == telegram_id:
                print(f"[FakeDB] register_user: {name} already registered, id={user['id']}")
                return user["id"]
        new_id = FakeDB._next_id
        FakeDB._next_id += 1
        FakeDB._users.append({"id": new_id, "telegram_id": telegram_id, "name": name})
        print(f"[FakeDB] register_user: new user {name} (telegram_id={telegram_id}) -> id={new_id}")
        return new_id

    def get_tasks_for_user(self, user_id, due_before):
        return [
            {
                "title":    "Finish Software Design report",
                "due_date": date.today() + timedelta(days=1),
                "status":   "in progress",
            },
            {
                "title":    "Review teammate's PR",
                "due_date": date.today() + timedelta(days=3),
                "status":   "pending",
            },
        ]

    def get_deadlines_for_user(self, user_id, due_before):
        return [
            {
                "id":       1,
                "title":    "CIS 3850 Homework 6",
                "due_date": date.today() + timedelta(days=2),
            },
        ]

    def get_events_for_user(self, user_id, on_date):
        return [
            {"title": "Team standup", "time": "10:00 AM"},
        ]

    def get_all_upcoming_deadlines(self, user_id):
        return [
            {
                "id":           1,
                "title":        "CIS 3850 Homework 6",
                "due_datetime": datetime.now() + timedelta(hours=1, minutes=50),
            },
            {
                "id":           2,
                "title":        "CIS 3515 Quiz",
                "due_datetime": datetime.now() + timedelta(hours=25),
            },
        ]

    # Track sent reminders in memory (resets each run — fine for testing)
    _sent = set()

    def check_reminder_sent(self, user_id, item_id, item_type, remind_type):
        key = (user_id, item_id, item_type, remind_type)
        return key in self._sent

    def log_reminder_sent(self, user_id, item_id, item_type, remind_type):
        key = (user_id, item_id, item_type, remind_type)
        self._sent.add(key)
        print(f"[FakeDB] Reminder logged: {key}")
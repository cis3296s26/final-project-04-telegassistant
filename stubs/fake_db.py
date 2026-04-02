# stubs/fake_db.py
from datetime import date, datetime, timedelta
from interfaces import AbstractDB


class FakeDB(AbstractDB):
    """
    Fake database for local development and testing.
    Returns hardcoded realistic data.
    Replace with the real DatabaseClient once Data Engineer is ready.
    """

    def connect(self):
        print("[FakeDB] connect() called")

    def close(self):
        print("[FakeDB] close() called")

    def get_active_users(self):
        return [
            {"id": 1, "telegram_id": 7654120499, "name": "Sid"},
        ]

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
import asyncio
from datetime import datetime, timedelta

from jobs import reminders


class RecordingDB:
	def __init__(self, users, deadlines, already_sent=None):
		self._users = users
		self._deadlines = deadlines
		self._already_sent = already_sent if already_sent is not None else set()
		self.logged = []

	def get_active_users(self):
		return self._users

	def get_all_upcoming_deadlines(self, user_id):
		return self._deadlines.get(user_id, [])

	def check_reminder_sent(self, user_id, item_id, item_type, remind_type):
		return (user_id, item_id, item_type, remind_type) in self._already_sent

	def log_reminder_sent(self, user_id, item_id, item_type, remind_type):
		self.logged.append((user_id, item_id, item_type, remind_type))


class RecordingTelegramBot:
	def __init__(self):
		self.calls = []

	async def send_message(self, chat_id, text):
		self.calls.append((chat_id, text))


def test_reminders_supports_24h_2h_and_30min_windows(monkeypatch):
	fixed_now = datetime(2026, 4, 15, 8, 0, 0)

	class FixedDateTime(datetime):
		@classmethod
		def now(cls, tz=None):
			return fixed_now

	monkeypatch.setattr(reminders, "datetime", FixedDateTime)

	db = RecordingDB(
		users=[{"id": 1, "telegram_id": 2001, "name": "A"}],
		deadlines={
			1: [
				{"id": 11, "title": "Essay", "due_datetime": fixed_now + timedelta(hours=23)},
				{"id": 12, "title": "Quiz", "due_datetime": fixed_now + timedelta(minutes=90)},
				{"id": 13, "title": "Lab", "due_datetime": fixed_now + timedelta(minutes=20)},
			]
		},
	)
	bot = RecordingTelegramBot()

	asyncio.run(reminders.run_reminder_check(db, bot))

	assert len(bot.calls) == 3
	sent_types = {entry[3] for entry in db.logged}
	assert sent_types == {"24h", "2h", "30min"}


def test_reminders_deduplicate_already_sent_items(monkeypatch):
	fixed_now = datetime(2026, 4, 15, 8, 0, 0)

	class FixedDateTime(datetime):
		@classmethod
		def now(cls, tz=None):
			return fixed_now

	monkeypatch.setattr(reminders, "datetime", FixedDateTime)

	already_sent = {(1, 21, "deadline", "24h")}
	db = RecordingDB(
		users=[{"id": 1, "telegram_id": 2002, "name": "A"}],
		deadlines={
			1: [
				{"id": 21, "title": "Duplicate", "due_datetime": fixed_now + timedelta(hours=8)},
			]
		},
		already_sent=already_sent,
	)
	bot = RecordingTelegramBot()

	asyncio.run(reminders.run_reminder_check(db, bot))

	assert bot.calls == []
	assert db.logged == []


def test_reminders_skip_past_due_items(monkeypatch):
	fixed_now = datetime(2026, 4, 15, 8, 0, 0)

	class FixedDateTime(datetime):
		@classmethod
		def now(cls, tz=None):
			return fixed_now

	monkeypatch.setattr(reminders, "datetime", FixedDateTime)

	db = RecordingDB(
		users=[{"id": 1, "telegram_id": 2003, "name": "A"}],
		deadlines={
			1: [
				{"id": 31, "title": "Missed", "due_datetime": fixed_now - timedelta(minutes=10)},
				{"id": 32, "title": "Upcoming", "due_datetime": fixed_now + timedelta(hours=3)},
			]
		},
	)
	bot = RecordingTelegramBot()

	asyncio.run(reminders.run_reminder_check(db, bot))

	assert len(bot.calls) == 1
	assert "Upcoming" in bot.calls[0][1]
	assert db.logged == [(1, 32, "deadline", "24h")]

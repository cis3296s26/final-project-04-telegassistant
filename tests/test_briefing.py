import asyncio
from datetime import date, timedelta

from jobs.briefing import run_daily_briefing


class RecordingDB:
	def __init__(self, users, tasks=None, deadlines=None, events=None):
		self._users = users
		self._tasks = tasks if tasks is not None else []
		self._deadlines = deadlines if deadlines is not None else []
		self._events = events if events is not None else []

		self.task_calls = []
		self.deadline_calls = []
		self.event_calls = []

	def get_active_users(self):
		return self._users

	def get_tasks_for_user(self, user_id, due_before):
		self.task_calls.append((user_id, due_before))
		return self._tasks

	def get_deadlines_for_user(self, user_id, due_before):
		self.deadline_calls.append((user_id, due_before))
		return self._deadlines

	def get_events_for_user(self, user_id, on_date):
		self.event_calls.append((user_id, on_date))
		return self._events


class RecordingAI:
	def __init__(self, should_fail=False):
		self.should_fail = should_fail
		self.calls = []

	async def generate_briefing(self, context):
		self.calls.append(context)
		if self.should_fail:
			raise RuntimeError("llm down")
		return "Daily briefing from AI"


class FlakyTelegramBot:
	def __init__(self, fail_times=0):
		self.fail_times = fail_times
		self.calls = []

	async def send_message(self, chat_id, text):
		self.calls.append((chat_id, text))
		if self.fail_times > 0:
			self.fail_times -= 1
			raise RuntimeError("telegram temporary failure")


def test_briefing_happy_path_builds_context_and_sends_message():
	today = date.today()
	db = RecordingDB(
		users=[{"id": 7, "telegram_id": 1001, "name": "Alex"}],
		tasks=[{"title": "Write report", "due_date": today + timedelta(days=1), "status": "pending"}],
		deadlines=[{"title": "Project due", "due_date": today + timedelta(days=2)}],
		events=[{"title": "Standup", "time": "10:00 AM"}],
	)
	ai = RecordingAI()
	bot = FlakyTelegramBot()

	asyncio.run(run_daily_briefing(db, ai, bot))

	assert len(ai.calls) == 1
	assert "TODAY'S EVENTS" in ai.calls[0]
	assert "UPCOMING TASKS" in ai.calls[0]
	assert "DEADLINES" in ai.calls[0]
	assert bot.calls == [(1001, "Daily briefing from AI")]
	assert len(db.task_calls) == 1
	assert len(db.deadline_calls) == 1
	assert len(db.event_calls) == 1


def test_briefing_uses_fallback_when_llm_fails():
	db = RecordingDB(
		users=[{"id": 8, "telegram_id": 1002, "name": "Taylor"}],
		tasks=[],
		deadlines=[],
		events=[],
	)
	ai = RecordingAI(should_fail=True)
	bot = FlakyTelegramBot()

	asyncio.run(run_daily_briefing(db, ai, bot))

	assert len(bot.calls) == 1
	assert bot.calls[0][0] == 1002
	assert "AI unavailable" in bot.calls[0][1]


def test_briefing_retries_telegram_send_and_succeeds(monkeypatch):
	db = RecordingDB(users=[{"id": 9, "telegram_id": 1003, "name": "Jordan"}])
	ai = RecordingAI()
	bot = FlakyTelegramBot(fail_times=2)

	sleep_calls = []

	async def fake_sleep(seconds):
		sleep_calls.append(seconds)

	monkeypatch.setattr("jobs.briefing.asyncio.sleep", fake_sleep)

	asyncio.run(run_daily_briefing(db, ai, bot))

	assert len(bot.calls) == 3
	assert sleep_calls == [5, 5]


def test_briefing_handles_empty_active_user_list():
	db = RecordingDB(users=[])
	ai = RecordingAI()
	bot = FlakyTelegramBot()

	asyncio.run(run_daily_briefing(db, ai, bot))

	assert ai.calls == []
	assert bot.calls == []


def test_briefing_handles_empty_user_data_context():
	db = RecordingDB(users=[{"id": 10, "telegram_id": 1004, "name": "Chris"}])
	ai = RecordingAI()
	bot = FlakyTelegramBot()

	asyncio.run(run_daily_briefing(db, ai, bot))

	assert len(ai.calls) == 1
	assert "Nothing scheduled" in ai.calls[0]
	assert len(bot.calls) == 1

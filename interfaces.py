# interfaces.py
# ============================================================
# TeleGAssistant — Interface Contracts
# Owned by: Automation Engineer
# Last updated: 
#
# EVERYONE on the team should read this file.
# Each engineer implements the class that matches their role.
# DO NOT change method signatures without a team discussion.
# ============================================================

from abc import ABC, abstractmethod
from datetime import date, datetime


# ------------------------------------------------------------
# DATA ENGINEER implements this
# ------------------------------------------------------------
class AbstractDB(ABC):

    @abstractmethod
    def connect(self):
        """Open the database connection. Call once at startup."""
        ...

    @abstractmethod
    def close(self):
        """Close the database connection. Call on shutdown."""
        ...

    @abstractmethod
    def get_active_users(self) -> list[dict]:
        """
        Returns all users with briefings enabled.

        Expected dict shape:
        {
            "id":          int,   # internal DB user ID
            "telegram_id": int,   # Telegram chat ID (used for sending messages)
            "name":        str,   # display name, e.g. "Alex"
        }
        """
        ...

    @abstractmethod
    def get_tasks_for_user(self, user_id: int, due_before: date) -> list[dict]:
        """
        Returns tasks due before the given date.

        Expected dict shape:
        {
            "title":    str,
            "due_date": date,   # Python date object, NOT a string
            "status":   str,    # e.g. "pending", "in progress", "done"
        }
        """
        ...

    @abstractmethod
    def get_deadlines_for_user(self, user_id: int, due_before: date) -> list[dict]:
        """
        Returns deadlines (Canvas assignments, etc.) due before the given date.

        Expected dict shape:
        {
            "id":       int,
            "title":    str,
            "due_date": date,   # Python date object, NOT a string
        }
        """
        ...

    @abstractmethod
    def get_events_for_user(self, user_id: int, on_date: date) -> list[dict]:
        """
        Returns calendar events on the given date.

        Expected dict shape:
        {
            "title": str,
            "time":  str,   # human-readable, e.g. "10:00 AM"
        }
        """
        ...

    @abstractmethod
    def get_all_upcoming_deadlines(self, user_id: int) -> list[dict]:
        """
        Returns all future deadlines for reminder checking.

        Expected dict shape:
        {
            "id":           int,
            "title":        str,
            "due_datetime": datetime,  # MUST be a datetime object, NOT a string
                                       # MUST include time (not just date)
        }
        """
        ...

    @abstractmethod
    def check_reminder_sent(
        self,
        user_id: int,
        item_id: int,
        item_type: str,     # "task" or "deadline"
        remind_type: str,   # "24h", "2h", or "30min"
    ) -> bool:
        """Returns True if this exact reminder has already been sent."""
        ...

    @abstractmethod
    def log_reminder_sent(
        self,
        user_id: int,
        item_id: int,
        item_type: str,
        remind_type: str,
    ) -> None:
        """Records that a reminder was sent. Used to prevent duplicates."""
        ...

    @abstractmethod
    def register_user(self, telegram_id: int, name: str) -> int:
        """
        Registers a new Telegram user, or returns existing user's internal ID
        if they have already been registered.

        Called by the Bot Engineer when a user sends /start.

        Returns the internal DB user ID (int).
        """
        ...

    @abstractmethod
    def add_task(self, user_id: int, title: str, due_datetime: datetime, description: str = "") -> int:
        """
        Inserts a new task. Returns the new task's DB id.

        due_datetime must be a full datetime (date + time) so the
        reminder job can fire a 30-min warning and a due-time prompt.
        description is optional — pass "" to omit.
        """
        ...

    @abstractmethod
    def remove_task(self, task_id: int) -> None:
        """Deletes a task by its DB id."""
        ...

    @abstractmethod
    def add_reminder(self, user_id: int, text: str, remind_at: datetime, recurrence: str) -> int:
        """
        Inserts a custom reminder. Returns the new reminder's DB id.

        recurrence must be one of: "none", "daily", "weekly".
        remind_at is the first fire time.
        """
        ...

    @abstractmethod
    def get_due_reminders(self, now: datetime) -> list[dict]:
        """
        Returns all reminders whose remind_at <= now.

        Expected dict shape:
        {
            "id":         int,
            "user_id":    int,
            "text":       str,
            "remind_at":  datetime,
            "recurrence": str,   # "none", "daily", "weekly"
        }
        """
        ...

    @abstractmethod
    def update_reminder_time(self, reminder_id: int, next_remind_at: datetime) -> None:
        """Advance remind_at to the next occurrence for recurring reminders."""
        ...

    @abstractmethod
    def delete_reminder(self, reminder_id: int) -> None:
        """Deletes a reminder by its DB id."""
        ...


# ------------------------------------------------------------
# AI ENGINEER implements this
# ------------------------------------------------------------
class AbstractAI(ABC):

    @abstractmethod
    async def generate_briefing(self, context: str) -> str:
        """
        Takes a structured context string, returns a formatted
        briefing message ready to send to the user via Telegram.

        MUST raise an exception (not return None) on failure
        so the caller can trigger the fallback briefing.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Returns True if the LLM server is reachable and responsive.
        Called once at startup — if this returns False, app.py will
        log a warning but continue running (briefings will use fallback).
        """
        ...


# ------------------------------------------------------------
# BOT ENGINEER implements this
# ------------------------------------------------------------
class AbstractBot(ABC):

    @abstractmethod
    async def send_message(self, chat_id: int, text: str) -> None:
        """
        Sends a message to a Telegram user.

        MUST raise an exception on failure (do not swallow errors silently)
        so the briefing pipeline can retry.

        text supports Telegram MarkdownV2 formatting.
        """
        ...

    @abstractmethod
    async def start_polling(self) -> None:
        """
        Starts the Telegram bot's message receive loop.
        This is a long-running coroutine — runs until cancelled.
        Called once in app.py as an asyncio task.
        """
        ...
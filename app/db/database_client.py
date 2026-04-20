from db.repositories.users_repo import get_or_create_user
from db.repositories.tasks_repo import (
    create_task,
    get_task_by_id,
    list_user_tasks,
    list_open_tasks,
    update_task_status,
)
from db.repositories.reminders_repo import (
    create_reminder,
    get_reminder_by_id,
    list_user_reminders,
    get_due_reminders,
    mark_reminder_sent,
    cancel_reminder,
)


class DatabaseClient:
    def get_or_create_user(
        self,
        telegram_user_id: str,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict:
        return get_or_create_user(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

    def create_task(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        due_at: str | None = None,
        priority: int = 3,
    ) -> dict:
        return create_task(
            user_id=user_id,
            title=title,
            description=description,
            due_at=due_at,
            priority=priority,
        )

    def get_task_by_id(self, task_id: int) -> dict | None:
        return get_task_by_id(task_id)

    def list_user_tasks(self, user_id: int) -> list[dict]:
        return list_user_tasks(user_id)

    def list_open_tasks(self, user_id: int) -> list[dict]:
        return list_open_tasks(user_id)

    def update_task_status(self, task_id: int, status: str) -> None:
        update_task_status(task_id, status)

    def create_reminder(
        self,
        user_id: int,
        title: str,
        remind_at: str,
        status: str = "pending",
    ) -> dict:
        return create_reminder(
            user_id=user_id,
            title=title,
            remind_at=remind_at,
            status=status,
        )

    def get_reminder_by_id(self, reminder_id: int) -> dict | None:
        return get_reminder_by_id(reminder_id)

    def list_user_reminders(self, user_id: int) -> list[dict]:
        return list_user_reminders(user_id)

    def get_due_reminders(self, now: str) -> list[dict]:
        return get_due_reminders(now)

    def mark_reminder_sent(self, reminder_id: int) -> None:
        mark_reminder_sent(reminder_id)

    def cancel_reminder(self, reminder_id: int) -> None:
        cancel_reminder(reminder_id)
from app.db.repositories.users_repo import get_or_create_user
from app.db.repositories.tasks_repo import (
    create_task,
    list_user_tasks,
    list_open_tasks,
    update_task_status,
    get_task_by_id
)

user = get_or_create_user(
    telegram_user_id="12345",
    username="aidan",
    first_name="Aidan",
    last_name="Arena"
)

task = create_task(
    user_id=user["id"],
    title="Finish TeleGAssistant DB layer",
    description="Complete tasks repo",
    due_at="2026-04-09T18:00:00",
    priority=2
)

print("Created:", task)

all_tasks = list_user_tasks(user["id"])
print("All tasks:", all_tasks)

open_tasks = list_open_tasks(user["id"])
print("Open tasks:", open_tasks)

update_task_status(task["id"], "done")

updated_task = get_task_by_id(task["id"])
print("Updated:", updated_task)
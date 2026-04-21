from db.repositories.users_repo import get_or_create_user
from db.repositories.deadlines_repo import create_or_update_deadline, list_user_deadlines


user = get_or_create_user(
    telegram_user_id="888",
    username="deadline_test",
    first_name="Deadline",
    last_name="Tester",
)

d1 = create_or_update_deadline(
    user_id=user["id"],
    title="Assignment 1",
    due_at="2026-04-25T23:59:00",
)

d2 = create_or_update_deadline(
    user_id=user["id"],
    title="Assignment 1",
    due_at="2026-04-25T23:59:00",
)

print("Deadline 1:", d1)
print("Deadline 2 (should update, not duplicate):", d2)
print("All deadlines:", list_user_deadlines(user["id"]))
from app.db.repositories.users_repo import get_or_create_user

user = get_or_create_user(
    telegram_user_id="12345",
    username="aidan",
    first_name="Aidan",
    last_name="Arena"
)

print(user)
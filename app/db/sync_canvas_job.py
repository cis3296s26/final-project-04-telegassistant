from db.database_client import DatabaseClient


def sync_canvas_data() -> None:
    db = DatabaseClient()

    user = db.get_or_create_user(
        telegram_user_id="9999",
        username="sync_bot",
        first_name="Sync",
        last_name="Job",
    )

    print(f"Canvas sync job ran successfully for user {user['id']}.")
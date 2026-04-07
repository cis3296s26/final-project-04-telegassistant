from datetime import datetime
from app.db.connection import get_connection


def get_or_create_user(
    telegram_user_id: str,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None
) -> dict:

    conn = get_connection()
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute(
        """
        SELECT * FROM users WHERE telegram_user_id = ?
        """,
        (telegram_user_id,)
    )
    user = cursor.fetchone()

    if user:
        conn.close()
        return dict(user)

    # Create new user
    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO users (
            telegram_user_id,
            username,
            first_name,
            last_name,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_user_id,
            username,
            first_name,
            last_name,
            now,
            now
        )
    )

    conn.commit()

    # Fetch newly created user
    cursor.execute(
        """
        SELECT * FROM users WHERE telegram_user_id = ?
        """,
        (telegram_user_id,)
    )
    new_user = cursor.fetchone()

    conn.close()

    return dict(new_user)
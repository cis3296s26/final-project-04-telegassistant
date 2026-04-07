from datetime import datetime
from app.db.connection import get_connection


def create_reminder(
    user_id: int,
    title: str,
    remind_at: str,
    status: str = "pending"
) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO reminders (
            user_id,
            title,
            remind_at,
            status,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, remind_at, status, now, now)
    )

    conn.commit()

    reminder_id = cursor.lastrowid

    cursor.execute(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,)
    )
    reminder = cursor.fetchone()
    conn.close()

    return dict(reminder)


def get_reminder_by_id(reminder_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,)
    )
    reminder = cursor.fetchone()
    conn.close()

    return dict(reminder) if reminder else None


def list_user_reminders(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM reminders
        WHERE user_id = ?
        ORDER BY remind_at ASC
        """,
        (user_id,)
    )
    reminders = cursor.fetchall()
    conn.close()

    return [dict(r) for r in reminders]


def get_due_reminders(now: str) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM reminders
        WHERE status = 'pending' AND remind_at <= ?
        ORDER BY remind_at ASC
        """,
        (now,)
    )
    reminders = cursor.fetchall()
    conn.close()

    return [dict(r) for r in reminders]


def mark_reminder_sent(reminder_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE reminders
        SET status = 'sent',
            updated_at = ?
        WHERE id = ?
        """,
        (now, reminder_id)
    )

    conn.commit()
    conn.close()


def cancel_reminder(reminder_id: int) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE reminders
        SET status = 'cancelled',
            updated_at = ?
        WHERE id = ?
        """,
        (now, reminder_id)
    )

    conn.commit()
    conn.close()
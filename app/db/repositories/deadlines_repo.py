from datetime import datetime
from db.connection import get_connection
from db.validators import validate_deadline_data


def create_or_update_deadline(
    user_id: int,
    title: str,
    due_at: str,
    status: str = "pending",
    external_id: str | None = None,
) -> dict:

    validate_deadline_data(title, due_at)

    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        SELECT * FROM deadlines
        WHERE user_id = ? AND title = ? AND due_at = ?
        """,
        (user_id, title, due_at)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE deadlines
            SET status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (status, now, existing["id"])
        )
        conn.commit()

        cursor.execute(
            "SELECT * FROM deadlines WHERE id = ?",
            (existing["id"],)
        )
        updated = cursor.fetchone()
        conn.close()
        return dict(updated)

    cursor.execute(
        """
        INSERT INTO deadlines (
            user_id,
            title,
            due_at,
            status,
            external_id,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, due_at, status, external_id, now, now)
    )

    conn.commit()
    deadline_id = cursor.lastrowid

    cursor.execute(
        "SELECT * FROM deadlines WHERE id = ?",
        (deadline_id,)
    )
    deadline = cursor.fetchone()
    conn.close()

    return dict(deadline)


def list_user_deadlines(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM deadlines
        WHERE user_id = ?
        ORDER BY due_at ASC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
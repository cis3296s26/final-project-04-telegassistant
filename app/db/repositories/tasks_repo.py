from datetime import datetime
from db.connection import get_connection


def create_task(
    user_id: int,
    title: str,
    description: str | None = None,
    due_at: str | None = None,
    priority: int = 3
) -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        INSERT INTO tasks (
            user_id,
            title,
            description,
            due_at,
            priority,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, description, due_at, priority, now, now)
    )

    conn.commit()

    task_id = cursor.lastrowid

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )
    task = cursor.fetchone()
    conn.close()

    return dict(task)


def get_task_by_id(task_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    )
    task = cursor.fetchone()
    conn.close()

    return dict(task) if task else None


def list_user_tasks(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY due_at ASC
        """,
        (user_id,)
    )
    tasks = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tasks]


def list_open_tasks(user_id: int) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM tasks
        WHERE user_id = ? AND status = 'open'
        ORDER BY due_at ASC
        """,
        (user_id,)
    )
    tasks = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tasks]


def update_task_status(task_id: int, status: str) -> None:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()

    cursor.execute(
        """
        UPDATE tasks
        SET status = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (status, now, task_id)
    )

    conn.commit()
    conn.close()
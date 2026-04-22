import sqlite3
from datetime import date, datetime
from pathlib import Path

from interfaces import AbstractDB


class DatabaseClient(AbstractDB):
    def __init__(self, db_path="data/telegassistant.db"):
        self._db_path = Path(db_path)
        self._conn = None

    def connect(self):
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ---------------------------------------------------------------- #
    # Users                                                             #
    # ---------------------------------------------------------------- #

    def get_active_users(self) -> list[dict]:
        rows = self._query(
            "SELECT id, telegram_id, name FROM users WHERE active = 1 ORDER BY id"
        )
        return [dict(row) for row in rows]

    def register_user(self, telegram_id: int, name: str) -> int:
        existing = self._query_one(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        if existing:
            return existing["id"]
        self._execute(
            "INSERT INTO users (telegram_id, name, active) VALUES (?, ?, 1)",
            (telegram_id, name),
        )
        row = self._query_one(
            "SELECT id FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return row["id"]

    def get_user_by_telegram_id(self, telegram_id: int) -> dict | None:
        row = self._query_one(
            "SELECT id, telegram_id, name FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        return dict(row) if row else None

    # ---------------------------------------------------------------- #
    # Tasks                                                             #
    # ---------------------------------------------------------------- #

    def get_tasks_for_user(self, user_id: int, due_before: date) -> list[dict]:
        rows = self._query(
            """
            SELECT id, title, due_date, due_datetime, status, description
            FROM tasks
            WHERE user_id = ? AND due_date <= ? AND status != 'done'
            ORDER BY due_datetime
            """,
            (user_id, due_before.isoformat()),
        )
        items = []
        for row in rows:
            items.append({
                "id":           row["id"],
                "title":        row["title"],
                "due_date":     date.fromisoformat(row["due_date"]),
                "due_datetime": datetime.fromisoformat(row["due_datetime"]),
                "status":       row["status"],
                "description":  row["description"] or "",
            })
        return items

    def get_all_tasks_for_user(self, user_id: int) -> list[dict]:
        rows = self._query(
            """
            SELECT id, title, due_date, due_datetime, status, description
            FROM tasks
            WHERE user_id = ? AND status != 'done'
            ORDER BY due_datetime
            """,
            (user_id,),
        )
        items = []
        for row in rows:
            items.append({
                "id":           row["id"],
                "title":        row["title"],
                "due_date":     date.fromisoformat(row["due_date"]),
                "due_datetime": datetime.fromisoformat(row["due_datetime"]),
                "status":       row["status"],
                "description":  row["description"] or "",
            })
        return items

    def add_task(self, user_id: int, title: str, due_datetime: datetime, description: str = "") -> int:
        due_date = due_datetime.date().isoformat()
        self._execute(
            """
            INSERT INTO tasks (user_id, title, due_date, due_datetime, status, description)
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (user_id, title, due_date, due_datetime.isoformat(), description),
        )
        row = self._query_one(
            "SELECT id FROM tasks WHERE user_id = ? AND title = ? AND due_datetime = ?",
            (user_id, title, due_datetime.isoformat()),
        )
        return row["id"]

    def remove_task(self, task_id: int) -> None:
        self._execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_upcoming_tasks_for_reminders(self) -> list[dict]:
        """Returns all pending tasks across all users, joined with telegram_id."""
        rows = self._query(
            """
            SELECT t.id, t.user_id, t.title, t.due_datetime, u.telegram_id
            FROM tasks t
            JOIN users u ON u.id = t.user_id
            WHERE t.status = 'pending'
            ORDER BY t.due_datetime
            """
        )
        items = []
        for row in rows:
            items.append({
                "id":           row["id"],
                "user_id":      row["user_id"],
                "telegram_id":  row["telegram_id"],
                "title":        row["title"],
                "due_datetime": datetime.fromisoformat(row["due_datetime"]),
            })
        return items

    # ---------------------------------------------------------------- #
    # Deadlines                                                         #
    # ---------------------------------------------------------------- #

    def get_deadlines_for_user(self, user_id: int, due_before: date) -> list[dict]:
        rows = self._query(
            """
            SELECT id, title, due_date
            FROM deadlines
            WHERE user_id = ? AND due_date <= ?
            ORDER BY due_date
            """,
            (user_id, due_before.isoformat()),
        )
        items = []
        for row in rows:
            items.append({
                "id":       row["id"],
                "title":    row["title"],
                "due_date": date.fromisoformat(row["due_date"]),
            })
        return items

    def get_all_upcoming_deadlines(self, user_id: int) -> list[dict]:
        rows = self._query(
            """
            SELECT id, title, due_datetime
            FROM deadlines
            WHERE user_id = ?
            ORDER BY due_datetime
            """,
            (user_id,),
        )
        items = []
        for row in rows:
            items.append({
                "id":           row["id"],
                "title":        row["title"],
                "due_datetime": datetime.fromisoformat(row["due_datetime"]),
            })
        return items

    # ---------------------------------------------------------------- #
    # Events                                                            #
    # ---------------------------------------------------------------- #

    def get_events_for_user(self, user_id: int, on_date: date) -> list[dict]:
        rows = self._query(
            """
            SELECT title, time
            FROM events
            WHERE user_id = ? AND event_date = ?
            ORDER BY time
            """,
            (user_id, on_date.isoformat()),
        )
        return [dict(row) for row in rows]

    # ---------------------------------------------------------------- #
    # Reminders                                                         #
    # ---------------------------------------------------------------- #

    def add_reminder(self, user_id: int, text: str, remind_at: datetime, recurrence: str) -> int:
        self._execute(
            """
            INSERT INTO reminders (user_id, text, remind_at, recurrence)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, text, remind_at.isoformat(), recurrence),
        )
        row = self._query_one(
            "SELECT id FROM reminders WHERE user_id = ? AND text = ? AND remind_at = ?",
            (user_id, text, remind_at.isoformat()),
        )
        return row["id"]

    def get_due_reminders(self, now: datetime) -> list[dict]:
        rows = self._query(
            """
            SELECT r.id, r.user_id, r.text, r.remind_at, r.recurrence, u.telegram_id
            FROM reminders r
            JOIN users u ON u.id = r.user_id
            WHERE r.remind_at <= ?
            ORDER BY r.remind_at
            """,
            (now.isoformat(),),
        )
        items = []
        for row in rows:
            items.append({
                "id":          row["id"],
                "user_id":     row["user_id"],
                "telegram_id": row["telegram_id"],
                "text":        row["text"],
                "remind_at":   datetime.fromisoformat(row["remind_at"]),
                "recurrence":  row["recurrence"],
            })
        return items

    def update_reminder_time(self, reminder_id: int, next_remind_at: datetime) -> None:
        self._execute(
            "UPDATE reminders SET remind_at = ? WHERE id = ?",
            (next_remind_at.isoformat(), reminder_id),
        )

    def delete_reminder(self, reminder_id: int) -> None:
        self._execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))

    # ---------------------------------------------------------------- #
    # Reminder log (dedup)                                              #
    # ---------------------------------------------------------------- #

    def check_reminder_sent(self, user_id: int, item_id: int, item_type: str, remind_type: str) -> bool:
        row = self._query_one(
            """
            SELECT 1 FROM reminder_log
            WHERE user_id = ? AND item_id = ? AND item_type = ? AND remind_type = ?
            LIMIT 1
            """,
            (user_id, item_id, item_type, remind_type),
        )
        return row is not None

    def log_reminder_sent(self, user_id: int, item_id: int, item_type: str, remind_type: str) -> None:
        self._execute(
            """
            INSERT OR IGNORE INTO reminder_log (user_id, item_id, item_type, remind_type, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, item_id, item_type, remind_type, datetime.now().isoformat()),
        )

    # ---------------------------------------------------------------- #
    # Schema                                                            #
    # ---------------------------------------------------------------- #

    def _ensure_schema(self):
        self._execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY,
                telegram_id INTEGER NOT NULL UNIQUE,
                name        TEXT    NOT NULL,
                active      INTEGER NOT NULL DEFAULT 1
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id           INTEGER PRIMARY KEY,
                user_id      INTEGER NOT NULL,
                title        TEXT    NOT NULL,
                due_date     TEXT    NOT NULL,
                due_datetime TEXT    NOT NULL,
                status       TEXT    NOT NULL DEFAULT 'pending',
                description  TEXT    NOT NULL DEFAULT ''
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS deadlines (
                id           INTEGER PRIMARY KEY,
                user_id      INTEGER NOT NULL,
                title        TEXT    NOT NULL,
                due_date     TEXT    NOT NULL,
                due_datetime TEXT    NOT NULL
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                title      TEXT    NOT NULL,
                event_date TEXT    NOT NULL,
                time       TEXT    NOT NULL
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id         INTEGER PRIMARY KEY,
                user_id    INTEGER NOT NULL,
                text       TEXT    NOT NULL,
                remind_at  TEXT    NOT NULL,
                recurrence TEXT    NOT NULL DEFAULT 'none'
            )
        """)
        self._execute("""
            CREATE TABLE IF NOT EXISTS reminder_log (
                user_id     INTEGER NOT NULL,
                item_id     INTEGER NOT NULL,
                item_type   TEXT    NOT NULL,
                remind_type TEXT    NOT NULL,
                sent_at     TEXT    NOT NULL,
                UNIQUE(user_id, item_id, item_type, remind_type)
            )
        """)

    # ---------------------------------------------------------------- #
    # Helpers                                                           #
    # ---------------------------------------------------------------- #

    def _query(self, sql, params=()):
        if not self._conn:
            raise RuntimeError("Database is not connected")
        return self._conn.execute(sql, params).fetchall()

    def _query_one(self, sql, params=()):
        if not self._conn:
            raise RuntimeError("Database is not connected")
        return self._conn.execute(sql, params).fetchone()

    def _execute(self, sql, params=()):
        if not self._conn:
            raise RuntimeError("Database is not connected")
        self._conn.execute(sql, params)
        self._conn.commit()

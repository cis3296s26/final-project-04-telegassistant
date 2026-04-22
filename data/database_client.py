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

    def get_active_users(self) -> list[dict]:
        rows = self._query(
            """
            SELECT id, telegram_id, name
            FROM users
            WHERE active = 1
            ORDER BY id
            """
        )
        return [dict(row) for row in rows]

    def get_tasks_for_user(self, user_id: int, due_before: date) -> list[dict]:
        rows = self._query(
            """
            SELECT title, due_date, status
            FROM tasks
            WHERE user_id = ? AND due_date <= ?
            ORDER BY due_date
            """,
            (user_id, due_before.isoformat()),
        )
        items = []
        for row in rows:
            items.append(
                {
                    "title": row["title"],
                    "due_date": date.fromisoformat(row["due_date"]),
                    "status": row["status"],
                }
            )
        return items

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
            items.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "due_date": date.fromisoformat(row["due_date"]),
                }
            )
        return items

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
            items.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "due_datetime": datetime.fromisoformat(row["due_datetime"]),
                }
            )
        return items

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

    def check_reminder_sent(self, user_id: int, item_id: int, item_type: str, remind_type: str) -> bool:
        row = self._query_one(
            """
            SELECT 1
            FROM reminder_log
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

    def _ensure_schema(self):
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                telegram_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS deadlines (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                due_date TEXT NOT NULL,
                due_datetime TEXT NOT NULL
            )
            """
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                time TEXT NOT NULL
            )
            """
        )
        self._execute(
            """
            CREATE TABLE IF NOT EXISTS reminder_log (
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                remind_type TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                UNIQUE(user_id, item_id, item_type, remind_type)
            )
            """
        )

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

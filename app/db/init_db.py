from pathlib import Path
from connection import get_connection


def init_db():
    conn = get_connection()

    schema_path = Path(__file__).with_name("schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.close()
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
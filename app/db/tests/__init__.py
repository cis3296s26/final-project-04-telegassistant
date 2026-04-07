from app.db.connection import get_connection

def init_db():
    conn = get_connection()

    with open("app/db/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
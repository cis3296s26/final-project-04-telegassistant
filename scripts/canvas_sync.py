# scripts/canvas_sync.py
# ============================================================
# One-shot Canvas sync — pulls upcoming assignments from all
# active courses and inserts them as deadlines for a given user.
#
# Usage:
#   python scripts/canvas_sync.py
# ============================================================

import os
import sys
import sqlite3
import httpx
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

BASE_URL   = os.getenv("CANVAS_BASE_URL", "https://templeu.instructure.com")
TOKEN      = os.getenv("CANVAS_API_TOKEN")
DB_PATH    = os.getenv("DB_PATH", "data/telegassistant.db")
USER_ID    = 1  # Sid's DB user_id


def canvas_get(path: str) -> list:
    headers = {"Authorization": f"Bearer {TOKEN}"}
    results = []
    url = f"{BASE_URL}/api/v1{path}"
    while url:
        r = httpx.get(url, headers=headers, params={"per_page": 50}, timeout=15)
        r.raise_for_status()
        results.extend(r.json())
        url = r.links.get("next", {}).get("url")
    return results


def sync():
    if not TOKEN:
        print("ERROR: CANVAS_API_TOKEN not set in .env")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id           INTEGER PRIMARY KEY,
            user_id      INTEGER NOT NULL,
            title        TEXT    NOT NULL,
            due_date     TEXT    NOT NULL,
            due_datetime TEXT    NOT NULL
        )
    """)
    conn.commit()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)  # courses ended more than 30 days ago are skipped

    print("Fetching active courses...")
    courses = canvas_get("/courses?enrollment_state=active&state[]=available")
    print(f"Found {len(courses)} courses")

    # Filter to courses that are currently running or recently started
    def is_current_course(c):
        end_at = c.get("end_at")
        if end_at:
            end_dt = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
            return end_dt >= cutoff
        start_at = c.get("start_at")
        if start_at:
            start_dt = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
            # If it started more than 18 months ago and has no end_at, skip it
            return (now - start_dt).days < 548
        return True  # no dates — include it

    courses = [c for c in courses if is_current_course(c)]
    print(f"Filtered to {len(courses)} current courses")

    inserted = 0
    skipped  = 0

    for course in courses:
        course_id   = course["id"]
        course_name = course.get("name", f"Course {course_id}")

        try:
            assignments = canvas_get(
                f"/courses/{course_id}/assignments"
                f"?bucket=upcoming&order_by=due_at"
            )
        except Exception as e:
            print(f"  Skipping {course_name}: {e}")
            continue

        for a in assignments:
            due_at = a.get("due_at")
            if not due_at:
                continue

            title        = a.get("name", "Untitled Assignment")
            due_dt       = datetime.fromisoformat(due_at.replace("Z", "+00:00"))

            # Skip assignments already past
            if due_dt < now:
                continue

            due_dt_local = due_dt.astimezone().replace(tzinfo=None)
            due_date     = due_dt_local.date().isoformat()
            due_datetime = due_dt_local.isoformat()

            existing = conn.execute(
                "SELECT id FROM deadlines WHERE user_id=? AND title=? AND due_date=?",
                (USER_ID, title, due_date)
            ).fetchone()

            if existing:
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO deadlines (user_id, title, due_date, due_datetime)
                VALUES (?, ?, ?, ?)
                """,
                (USER_ID, f"{course_name}: {title}", due_date, due_datetime)
            )
            inserted += 1
            print(f"  + {course_name}: {title} — due {due_date}")

    conn.commit()
    conn.close()
    print(f"\nDone. {inserted} deadlines inserted, {skipped} already existed.")


if __name__ == "__main__":
    sync()

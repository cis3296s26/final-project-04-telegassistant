from datetime import datetime


def validate_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_deadline_data(title: str | None, due_at: str | None) -> None:
    if not title:
        raise ValueError("Deadline title is required.")
    if not due_at:
        raise ValueError("Deadline due_at is required.")
    if not validate_iso_datetime(due_at):
        raise ValueError("Deadline due_at must be ISO datetime format.")
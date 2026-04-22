# bot/ui.py
# Reusable inline keyboard builders for date and time selection.
# Used by /addtask and /remindme ConversationHandlers.
#
# Callback data format:
#   Calendar day:  "CAL_DAY|YYYY-MM-DD"
#   Calendar nav:  "CAL_NAV|YYYY-MM"   (prev/next month arrows)
#   Calendar noop: "CAL_IGNORE"        (header cells — do nothing)
#   Hour pick:     "TIME_HOUR|HH"
#   Minute pick:   "TIME_MIN|MM"

import calendar
from datetime import date, datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# ------------------------------------------------------------------ #
# Calendar                                                            #
# ------------------------------------------------------------------ #

_DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """
    Returns a month-grid inline keyboard.
    Past days are shown as a dot (·) and are unselectable.
    """
    today = date.today()
    keyboard = []

    # Header row: prev arrow | Month Year | next arrow
    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year  = year if month < 12 else year + 1

    keyboard.append([
        InlineKeyboardButton("«", callback_data=f"CAL_NAV|{prev_year}-{prev_month:02d}"),
        InlineKeyboardButton(f"{_MONTHS[month - 1]} {year}", callback_data="CAL_IGNORE"),
        InlineKeyboardButton("»", callback_data=f"CAL_NAV|{next_year}-{next_month:02d}"),
    ])

    # Day-of-week header
    keyboard.append([
        InlineKeyboardButton(d, callback_data="CAL_IGNORE") for d in _DAYS
    ])

    # Weeks
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="CAL_IGNORE"))
            else:
                d = date(year, month, day)
                if d < today:
                    row.append(InlineKeyboardButton("·", callback_data="CAL_IGNORE"))
                else:
                    row.append(InlineKeyboardButton(
                        str(day),
                        callback_data=f"CAL_DAY|{d.isoformat()}",
                    ))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)


# ------------------------------------------------------------------ #
# Hour picker                                                         #
# ------------------------------------------------------------------ #

_HOURS = list(range(6, 24))  # 6 AM through 11 PM


def build_hour_picker() -> InlineKeyboardMarkup:
    """4-column grid of hours (6 AM – 11 PM)."""
    rows = []
    for i in range(0, len(_HOURS), 4):
        chunk = _HOURS[i:i + 4]
        rows.append([
            InlineKeyboardButton(
                f"{h:02d}:00",
                callback_data=f"TIME_HOUR|{h:02d}",
            )
            for h in chunk
        ])
    return InlineKeyboardMarkup(rows)


# ------------------------------------------------------------------ #
# Minute picker                                                       #
# ------------------------------------------------------------------ #

_MINUTES = ["00", "15", "30", "45"]


def build_minute_picker(hour: str) -> InlineKeyboardMarkup:
    """Single row of minute options for the chosen hour."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{hour}:{m}",
            callback_data=f"TIME_MIN|{m}",
        )
        for m in _MINUTES
    ]])

"""Centralized time utilities for the application."""

import datetime


def now() -> datetime.datetime:
    """Returns the current datetime."""
    return datetime.datetime.now()


def now_timestamp() -> float:
    """Returns the current time as a Unix epoch timestamp (seconds)."""
    return now().timestamp()


def ms_to_seconds(ms: int) -> int:
    """Converts milliseconds to seconds (integer division)."""
    return ms // 1000


def is_night_hours(hour: int | None = None) -> bool:
    """
    Checks if the given hour falls within night hours (6PM - 9AM).
    If no hour is provided, uses the current hour.
    """
    if hour is None:
        hour = now().hour
    return hour >= 18 or hour < 9


def format_time(dt: datetime.datetime, fmt: str = "%H:%M") -> str:
    """Formats a datetime object into a string."""
    return dt.strftime(fmt)

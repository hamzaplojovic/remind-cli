"""Utility functions shared across Remind modules."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from remind.models import PriorityLevel
from remind.platform_utils import get_platform


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_dir() -> Path:
    """Get the Remind application directory (platform-specific).

    Returns platform-specific app data directory:
    - macOS: ~/Library/Application Support/Remind
    - Linux: ~/.local/share/remind
    - Windows: %APPDATA%\\Remind
    """
    return get_platform().get_app_data_dir()


def get_logs_dir() -> Path:
    """Get the Remind logs directory (platform-specific).

    Returns platform-specific logs directory.
    """
    return get_platform().get_logs_dir()


def run_command(
    cmd: list[str],
    check: bool = True,
    timeout: Optional[int] = None,
    cwd: Optional[str] = None,
) -> subprocess.CompletedProcess:
    """
    Run a shell command with standard options.

    Args:
        cmd: Command and arguments as list
        check: Raise exception on non-zero exit code
        timeout: Timeout in seconds
        cwd: Working directory

    Returns:
        CompletedProcess instance
    """
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        timeout=timeout,
        cwd=cwd,
    )


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text and add ellipsis if needed.

    Args:
        text: Text to truncate
        max_length: Maximum length before truncation

    Returns:
        Truncated text with "..." appended if truncated
    """
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def parse_priority(
    priority_str: str,
    default: PriorityLevel = PriorityLevel.MEDIUM,
) -> PriorityLevel:
    """
    Parse a priority string into a PriorityLevel.

    Args:
        priority_str: Priority string ("high", "medium", "low")
        default: Default priority if parsing fails

    Returns:
        PriorityLevel enum value
    """
    try:
        return PriorityLevel(priority_str.lower())
    except (ValueError, AttributeError):
        return default


def format_datetime(dt: datetime) -> str:
    """
    Format datetime in a user-friendly relative format.

    Args:
        dt: DateTime to format (naive or aware)

    Returns:
        Formatted string (e.g., "today at 9am", "in 2 days", "overdue by 3 days")
    """
    # Ensure datetime is timezone-aware for comparison
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    dt_date = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    time_str = dt.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")

    # Check if today
    if dt_date == today:
        return f"today at {time_str}"

    # Check if tomorrow
    tomorrow = today.replace(day=today.day + 1)
    if dt_date == tomorrow:
        return f"tomorrow at {time_str}"

    # Check if overdue
    if dt < now:
        days_ago = (now - dt).days
        if days_ago == 0:
            return f"overdue (today)"
        return f"overdue by {days_ago} day{'s' if days_ago > 1 else ''}"

    # Future dates
    days_ahead = (dt_date - today).days
    if days_ahead < 7:
        return f"in {days_ahead} day{'s' if days_ahead > 1 else ''} at {time_str}"

    # Far future - show the date
    return dt.strftime("%b %d at %I:%M %p").lstrip("0")

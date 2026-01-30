"""Utility functions shared across Remind modules."""

import subprocess
from pathlib import Path
from typing import Optional

from remind.models import PriorityLevel


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist. Returns the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_app_dir() -> Path:
    """Get the Remind application directory (~/.remind)."""
    return ensure_dir(Path.home() / ".remind")


def get_logs_dir() -> Path:
    """Get the Remind logs directory (~/.remind/logs)."""
    return ensure_dir(get_app_dir() / "logs")


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

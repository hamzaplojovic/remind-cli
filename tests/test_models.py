"""Tests for data models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from remind.models import Config, PriorityLevel, Reminder


def test_priority_level_enum():
    """Test priority level enum."""
    assert PriorityLevel.HIGH.value == "high"
    assert PriorityLevel.MEDIUM.value == "medium"
    assert PriorityLevel.LOW.value == "low"


def test_reminder_model():
    """Test reminder model."""
    now = datetime.now(timezone.utc)

    reminder = Reminder(
        id=1,
        text="Test reminder",
        due_at=now,
        created_at=now,
        priority=PriorityLevel.MEDIUM,
    )

    assert reminder.id == 1
    assert reminder.text == "Test reminder"
    assert reminder.done_at is None


def test_config_model():
    """Test configuration model."""
    config = Config(timezone="UTC")
    assert config.timezone == "UTC"
    assert config.scheduler_interval_minutes == 1
    assert config.notifications_enabled
    assert config.nudge_intervals_minutes == [5, 15, 60]


def test_config_validation():
    """Test config validation."""
    # Invalid interval should fail
    with pytest.raises(ValidationError):
        Config(scheduler_interval_minutes=0)

    with pytest.raises(ValidationError):
        Config(scheduler_interval_minutes=120)

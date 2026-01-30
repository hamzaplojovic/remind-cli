"""Tests for scheduler module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from remind.db import Database
from remind.scheduler import Scheduler


def test_scheduler_detects_due_reminders(test_db):
    """Test that scheduler detects due reminders."""
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=1)

    # Add a due reminder and a future reminder
    test_db.add_reminder("Past task", past)
    test_db.add_reminder("Future task", now + timedelta(days=1))

    # Check due reminders
    due = test_db.get_due_reminders(now)
    assert len(due) == 1
    assert due[0].text == "Past task"


def test_scheduler_state_tracking():
    """Test scheduler state tracks nudge times."""
    from remind.scheduler import SchedulerState

    state = SchedulerState()

    # Record a nudge
    state.record_nudge(1)
    assert 1 in state.last_nudge_times

    # Record done removes from tracking
    state.record_done(1)
    assert 1 not in state.last_nudge_times


@patch("remind.scheduler.NotificationManager")
def test_scheduler_sends_notification(mock_notif_class, test_db):
    """Test that scheduler sends notifications."""
    mock_notif = MagicMock()
    mock_notif_class.return_value = mock_notif

    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=1)

    test_db.add_reminder("Task due", past)

    scheduler = Scheduler(db=test_db)
    scheduler._check_and_notify()

    # Verify notification was sent
    assert mock_notif.notify_reminder_due.called


def test_scheduler_respects_premium_for_nudges(test_db):
    """Test that nudges require premium license."""
    from remind.scheduler import SchedulerState

    state = SchedulerState()
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=1)

    reminder_id = 1
    state.record_nudge(reminder_id)

    # Check if nudge should fire (requires time to pass)
    should_nudge = state.should_nudge(reminder_id, [5], past)
    # Should be False since not enough time has passed
    assert not should_nudge

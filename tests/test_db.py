"""Tests for database module."""

from datetime import datetime, timezone

from remind.models import PriorityLevel


def test_add_reminder(test_db):
    """Test adding a reminder to the database."""
    due_time = datetime(2025, 1, 31, 9, 0, 0, tzinfo=timezone.utc)

    reminder = test_db.add_reminder(
        text="Test reminder",
        due_at=due_time,
        priority=PriorityLevel.HIGH,
    )

    assert reminder.id > 0
    assert reminder.text == "Test reminder"
    assert reminder.priority == PriorityLevel.HIGH
    assert reminder.done_at is None


def test_list_active_reminders(test_db):
    """Test listing active reminders."""
    now = datetime.now(timezone.utc)

    test_db.add_reminder("Task 1", now)
    test_db.add_reminder("Task 2", now)

    reminders = test_db.list_active_reminders()
    assert len(reminders) == 2


def test_mark_done(test_db):
    """Test marking a reminder as done."""
    now = datetime.now(timezone.utc)
    reminder = test_db.add_reminder("Test reminder", now)

    done_reminder = test_db.mark_done(reminder.id)

    assert done_reminder is not None
    assert done_reminder.done_at is not None

    # Verify it doesn't show in active list
    active = test_db.list_active_reminders()
    assert len(active) == 0

    # But shows in all reminders
    all_reminders = test_db.list_all_reminders()
    assert len(all_reminders) == 1


def test_search_reminders(test_db):
    """Test searching reminders."""
    now = datetime.now(timezone.utc)

    test_db.add_reminder("Call mom", now)
    test_db.add_reminder("Buy groceries", now)
    test_db.add_reminder("Call dad", now)

    results = test_db.search_reminders("call")
    assert len(results) == 2

    results = test_db.search_reminders("groceries")
    assert len(results) == 1


def test_get_due_reminders(test_db):
    """Test getting due reminders."""
    now = datetime.now(timezone.utc)
    past = datetime(2025, 1, 20, 0, 0, 0, tzinfo=timezone.utc)
    future = datetime(2026, 12, 31, 0, 0, 0, tzinfo=timezone.utc)

    test_db.add_reminder("Past task", past)
    test_db.add_reminder("Future task", future)

    due = test_db.get_due_reminders(now)
    assert len(due) == 1
    assert due[0].text == "Past task"

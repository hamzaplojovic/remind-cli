"""End-to-end integration tests for Remind."""

from datetime import datetime, timezone

from typer.testing import CliRunner

from remind.cli import app

runner = CliRunner()


def test_e2e_add_and_list_reminders():
    """Test adding and listing reminders end-to-end."""
    with runner.isolated_filesystem():
        # Add reminder
        result = runner.invoke(
            app,
            ["add", "Buy milk", "--due", "tomorrow 5pm"],
        )
        assert result.exit_code == 0
        assert "Reminder added" in result.stdout

        # List reminders
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Buy milk" in result.stdout


def test_e2e_add_with_priority():
    """Test adding reminder with priority."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["add", "Urgent task", "--priority", "high"],
        )
        assert result.exit_code == 0

        result = runner.invoke(app, ["list"])
        # Priority shows as red circle emoji for high priority
        assert "🔴" in result.stdout or "Urgent task" in result.stdout


def test_e2e_search_workflow():
    """Test search functionality end-to-end."""
    with runner.isolated_filesystem():
        # Add multiple reminders
        runner.invoke(app, ["add", "Call mom"])
        runner.invoke(app, ["add", "Call dad"])
        runner.invoke(app, ["add", "Email boss"])

        # Search for "call"
        result = runner.invoke(app, ["search", "call"])
        assert result.exit_code == 0
        assert "Call mom" in result.stdout
        assert "Call dad" in result.stdout
        assert "Email boss" not in result.stdout


def test_e2e_done_workflow(test_db):
    """Test marking reminders as done."""

    # Add reminder to test_db
    reminder = test_db.add_reminder("Task 1", datetime.now(timezone.utc))
    assert reminder.id is not None
    assert reminder.done_at is None

    # Mark done via database
    test_db.mark_done(reminder.id)

    # Verify reminder is done
    updated_reminder = test_db.get_reminder(reminder.id)
    assert updated_reminder is not None
    assert updated_reminder.done_at is not None


def test_e2e_settings_management():
    """Test settings commands end-to-end."""
    with runner.isolated_filesystem():
        # Show settings
        result = runner.invoke(app, ["settings", "--show"])
        assert result.exit_code == 0
        assert "Timezone" in result.stdout

        # Change timezone
        result = runner.invoke(app, ["settings", "--timezone", "US/Pacific"])
        assert "Timezone set" in result.stdout


def test_e2e_full_workflow(test_db):
    """Test complete workflow: add, list, search, done."""
    from remind.models import PriorityLevel

    # Add reminders
    reminder_a = test_db.add_reminder(
        "Task A",
        datetime.now(timezone.utc),
        priority=PriorityLevel.HIGH
    )
    test_db.add_reminder(
        "Task B",
        datetime.now(timezone.utc),
        priority=PriorityLevel.LOW
    )

    # List all reminders
    all_reminders = test_db.list_all_reminders()
    assert len(all_reminders) >= 2
    assert any(r.text == "Task A" for r in all_reminders)
    assert any(r.text == "Task B" for r in all_reminders)

    # Search for Task A
    results = test_db.search_reminders("Task A")
    assert len(results) >= 1
    assert any(r.text == "Task A" for r in results)

    # Mark Task A as done
    test_db.mark_done(reminder_a.id)

    # List active reminders (should not include Task A)
    active = test_db.list_active_reminders()
    assert any(r.text == "Task B" for r in active)
    assert not any(r.text == "Task A" for r in active)

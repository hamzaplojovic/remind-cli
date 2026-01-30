"""End-to-end integration tests for Remind."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from remind.cli import app
from remind.db import Database

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
        result = runner.invoke(app, ["list-reminders"])
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

        result = runner.invoke(app, ["list-reminders"])
        assert "high" in result.stdout


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
    def mock_get_db():
        return test_db

    with patch("remind.cli.get_db", mock_get_db):
        # Add reminder
        result = runner.invoke(app, ["add", "Task 1"])
        assert "Reminder added" in result.stdout
        # Extract ID from output
        import re
        match = re.search(r"ID: (\d+)", result.stdout)
        assert match
        reminder_id = match.group(1)

        # List active
        result = runner.invoke(app, ["list-reminders"])
        assert "Task 1" in result.stdout

        # Mark done
        result = runner.invoke(app, ["done", reminder_id])
        assert "marked done" in result.stdout

        # List active (should be empty)
        result = runner.invoke(app, ["list-reminders"])
        assert "No reminders found" in result.stdout or "Task 1" not in result.stdout

        # List all
        result = runner.invoke(app, ["list-reminders", "--all"])
        assert "Task 1" in result.stdout


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
    with runner.isolated_filesystem():
        def mock_get_db():
            return test_db

        with patch("remind.cli.get_db", mock_get_db):
            # Add reminders
            result = runner.invoke(app, ["add", "Task A", "--priority", "high"])
            assert result.exit_code == 0

            result = runner.invoke(app, ["add", "Task B", "--priority", "low"])
            assert result.exit_code == 0

            # List all
            result = runner.invoke(app, ["list-reminders"])
            assert "Task A" in result.stdout
            assert "Task B" in result.stdout
            assert "2" in result.stdout or "ID 1" in result.stdout  # At least 2 reminders

            # Search
            result = runner.invoke(app, ["search", "Task A"])
            assert "Task A" in result.stdout

            # Mark first as done
            result = runner.invoke(app, ["done", "1"])
            assert "marked done" in result.stdout

            # List active (should show only Task B)
            result = runner.invoke(app, ["list-reminders"])
            assert "Task B" in result.stdout

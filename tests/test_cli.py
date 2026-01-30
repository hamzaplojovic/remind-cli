"""Tests for CLI module."""

from typer.testing import CliRunner

from remind.cli import app

runner = CliRunner()


def test_add_command(test_db, monkeypatch):
    """Test add command."""

    # Mock the database
    def mock_get_db():
        return test_db

    monkeypatch.setattr("remind.cli.get_db", mock_get_db)

    result = runner.invoke(
        app,
        ["add", "Test reminder", "--due", "tomorrow 3pm"],
    )
    assert result.exit_code == 0
    assert "Reminder added" in result.stdout


def test_list_command(test_db, monkeypatch):
    """Test list command."""

    def mock_get_db():
        return test_db

    monkeypatch.setattr("remind.cli.get_db", mock_get_db)

    # Add a reminder first
    from datetime import datetime, timezone

    test_db.add_reminder("Test task", datetime.now(timezone.utc))

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Test task" in result.stdout


def test_done_command(test_db, monkeypatch):
    """Test marking reminder as done."""

    def mock_get_db():
        return test_db

    monkeypatch.setattr("remind.cli.get_db", mock_get_db)

    from datetime import datetime, timezone

    reminder = test_db.add_reminder("Test task", datetime.now(timezone.utc))

    result = runner.invoke(app, ["done", str(reminder.id)])
    assert result.exit_code == 0
    assert "marked done" in result.stdout

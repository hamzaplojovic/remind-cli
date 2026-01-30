"""Tests for scheduler daemon and service installation."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from remind.scheduler import Scheduler


def test_scheduler_main_loop(test_db):
    """Test scheduler main loop logic."""
    now = datetime.now(timezone.utc)
    past = now - timedelta(minutes=5)

    # Add reminders
    test_db.add_reminder("Task 1", past)
    test_db.add_reminder("Task 2", now + timedelta(days=1))

    scheduler = Scheduler(db=test_db)

    # Check and notify should find due reminders
    with patch.object(scheduler, "_send_notification") as mock_notify:
        scheduler._check_and_notify()
        # Should have called notify for one reminder
        assert mock_notify.called


def test_scheduler_tracks_nudge_state():
    """Test scheduler properly tracks which reminders have been nudged."""
    from remind.scheduler import SchedulerState

    state = SchedulerState()

    # Initially empty
    assert len(state.last_nudge_times) == 0

    # Record nudges
    state.record_nudge(1)
    state.record_nudge(2)
    assert len(state.last_nudge_times) == 2

    # Mark done removes from tracking
    state.record_done(1)
    assert len(state.last_nudge_times) == 1
    assert 2 in state.last_nudge_times


@patch("remind.scheduler.subprocess.run")
def test_install_macos_agent(mock_subprocess, tmp_path):
    """Test macOS LaunchAgent installation."""

    with patch("sys.argv", ["/usr/local/bin/remind"]):
        with patch.object(Path, "home", return_value=tmp_path):
            scheduler = Scheduler()
            scheduler._install_macos_agent()

    # Verify plist was created
    plist_path = tmp_path / "Library" / "LaunchAgents" / "com.remind.scheduler.plist"
    assert plist_path.exists()

    # Verify content
    content = plist_path.read_text()
    assert "com.remind.scheduler" in content
    assert "/usr/local/bin/remind" in content


@patch("remind.scheduler.subprocess.run")
def test_install_linux_service(mock_subprocess, tmp_path):
    """Test Linux systemd service installation."""
    with patch("sys.argv", ["/usr/local/bin/remind"]):
        with patch.object(Path, "home", return_value=tmp_path):
            scheduler = Scheduler()
            scheduler._install_linux_service()

    # Verify service file was created
    service_path = tmp_path / ".config" / "systemd" / "user" / "remind-scheduler.service"
    assert service_path.exists()

    # Verify content
    content = service_path.read_text()
    assert "scheduler" in content
    assert "/usr/local/bin/remind" in content
    assert "Type=simple" in content


def test_scheduler_respects_check_interval(test_db):
    """Test scheduler respects configured check interval."""
    config = MagicMock()
    config.scheduler_interval_minutes = 5
    config.notifications_enabled = True
    config.notification_sound_enabled = False
    config.nudge_intervals_minutes = [5, 15, 60]

    with patch("remind.scheduler.load_config", return_value=config):
        scheduler = Scheduler(db=test_db)
        assert scheduler.config.scheduler_interval_minutes == 5


@patch("remind.scheduler.time.sleep")
def test_scheduler_handles_sigterm(mock_sleep, test_db):
    """Test scheduler gracefully handles SIGTERM."""
    import signal

    scheduler = Scheduler(db=test_db)
    scheduler.running = True

    # Simulate SIGTERM by directly calling the handler
    with patch.object(scheduler, "_shutdown"):
        with pytest.raises(SystemExit):
            scheduler._handle_shutdown(signal.SIGTERM, None)
        assert not scheduler.running


def test_scheduler_notification_error_handling(test_db):
    """Test scheduler continues on notification errors."""
    from remind.scheduler import Scheduler

    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=1)

    test_db.add_reminder("Task", past)

    scheduler = Scheduler(db=test_db)

    # Mock notifications to raise exception
    with patch.object(scheduler, "notifications") as mock_notif:
        mock_notif.notify_reminder_due.side_effect = Exception("Notif failed")

        # Should not crash
        scheduler._check_and_notify()
        # Exception should be caught
        mock_notif.notify_reminder_due.assert_called_once()

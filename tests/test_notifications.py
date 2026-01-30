"""Tests for notifications module."""

from unittest.mock import MagicMock, patch

from remind.notifications import NotificationManager


@patch("remind.notifications.Notify")
def test_notification_manager_init(mock_notify_class):
    """Test notification manager initialization."""
    mock_notify_class.return_value = MagicMock()

    manager = NotificationManager()
    assert manager.app_name == "Remind"
    assert manager.platform_info.system in ["Darwin", "Linux", "Windows"]


@patch("remind.notifications.Notify")
def test_send_notification(mock_notify_class):
    """Test sending a notification."""
    mock_notify = MagicMock()
    mock_notify_class.return_value = mock_notify

    manager = NotificationManager()
    result = manager.notify(
        title="Test",
        message="Test message",
        urgency="normal",
    )

    assert result is True
    mock_notify.send.assert_called_once()


@patch("remind.notifications.Notify")
def test_notify_reminder_due(mock_notify_class):
    """Test reminder due notification."""
    mock_notify = MagicMock()
    mock_notify_class.return_value = mock_notify

    manager = NotificationManager()
    result = manager.notify_reminder_due(
        "Buy groceries",
        sound=True,
    )

    assert result is True
    mock_notify.send.assert_called_once()


@patch("remind.notifications.Notify")
def test_notify_nudge(mock_notify_class):
    """Test nudge notification."""
    mock_notify = MagicMock()
    mock_notify_class.return_value = mock_notify

    manager = NotificationManager()
    result = manager.notify_nudge(
        "Still need to do this task",
        sound=True,
    )

    assert result is True
    # Nudges should call send
    mock_notify.send.assert_called_once()


@patch("remind.notifications.Notify")
def test_notification_error_handling(mock_notify_class):
    """Test error handling in notifications."""
    mock_notify = MagicMock()
    mock_notify.send.side_effect = Exception("Notification failed")
    mock_notify_class.return_value = mock_notify

    manager = NotificationManager()
    result = manager.notify(
        title="Test",
        message="Test",
    )

    # Should return False on error
    assert result is False

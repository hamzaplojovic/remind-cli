"""Notification system for Remind."""

import platform
from typing import Callable, Optional

try:
    from notifypy import Notify
except ImportError:
    Notify = None  # type: ignore


class NotificationManager:
    """Unified notification interface across platforms."""

    def __init__(self, app_name: str = "Remind"):
        """Initialize notification manager."""
        self.app_name = app_name
        self.platform = platform.system()

        if Notify is None:
            raise ImportError(
                "notify-py not installed. Install with: pip install notify-py"
            )

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        callback: Optional[Callable[[], None]] = None,
        sound: bool = False,
    ) -> bool:
        """
        Send a native desktop notification.

        Args:
            title: Notification title
            message: Notification body
            urgency: "low", "normal", "critical"
            callback: Optional callback function when notification is clicked
            sound: Whether to play a sound

        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            notification = Notify()
            notification.title = title
            notification.message = message
            notification.app_name = self.app_name

            # Note: notify-py has limited callback support across platforms
            # This is a placeholder for future enhancement
            if callback:
                # Callback support varies by platform
                pass

            notification.send()
            return True
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False

    def notify_reminder_due(
        self, reminder_text: str, sound: bool = False, callback: Optional[Callable] = None
    ) -> bool:
        """Send a notification for a due reminder."""
        title = "Reminder"
        message = reminder_text[:100] + ("..." if len(reminder_text) > 100 else "")
        return self.notify(
            title=title,
            message=message,
            urgency="normal",
            callback=callback,
            sound=sound,
        )

    def notify_nudge(self, reminder_text: str, sound: bool = False) -> bool:
        """Send a nudge notification for an escalated reminder."""
        title = "Reminder Nudge"
        message = reminder_text[:100] + ("..." if len(reminder_text) > 100 else "")
        return self.notify(
            title=title,
            message=message,
            urgency="critical",
            sound=sound,
        )

    @staticmethod
    def is_supported() -> bool:
        """Check if notifications are supported on this platform."""
        return Notify is not None

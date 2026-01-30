"""Notification system for Remind."""

import subprocess
from collections.abc import Callable

from remind.platform_capabilities import PlatformCapabilities
from remind.platform_utils import get_platform

try:
    from notifypy import Notify
except ImportError:
    Notify = None  # type: ignore


class NotificationManager:
    """Unified notification interface across platforms.

    Provides graceful degradation:
    - If notify-py unavailable: prints to console
    - If sound player unavailable: sends notification without sound
    """

    def __init__(self, app_name: str = "Remind", strict: bool = False):
        """Initialize notification manager.

        Args:
            app_name: Application name for notifications
            strict: If True, raise error if notify-py unavailable.
                   If False, gracefully degrade to console output.

        Raises:
            ImportError: If strict=True and notify-py not available
        """
        self.app_name = app_name
        self.platform_info = get_platform()
        self.notifications_available = Notify is not None
        self.sound_available = PlatformCapabilities.test_sound_player(
            self.platform_info.get_sound_player()
        )

        if not self.notifications_available and strict:
            raise ImportError("notify-py not installed. Install with: pip install notify-py")

    def is_available(self) -> bool:
        """Check if notifications can be sent.

        Returns:
            True if notify-py is available
        """
        return self.notifications_available

    def is_sound_available(self) -> bool:
        """Check if sound playback is available.

        Returns:
            True if sound player is available
        """
        return self.sound_available

    def _play_sound(self, urgency: str = "normal") -> None:
        """Play an annoying alert sound based on urgency.

        Sound playback is best-effort - if the player is unavailable or
        playback fails, the notification is still sent without sound.

        Args:
            urgency: Sound urgency level ("low", "normal", "critical")
        """
        if not self.sound_available:
            return  # Sound player not available, skip silently

        if self.platform_info.is_macos:
            # Use system alert sounds on macOS
            sounds = {
                "critical": "Glass",  # Very annoying
                "normal": "Ping",  # Medium annoying
                "low": "Pop",  # Less annoying
            }
            sound = sounds.get(urgency, "Ping")
            try:
                subprocess.run(
                    ["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                    timeout=10,
                    capture_output=True,
                )
            except subprocess.TimeoutExpired:
                pass  # Sound playback timed out but notification sent
            except FileNotFoundError:
                pass  # afplay not found, skip silently
            except Exception:
                pass  # Other errors, skip silently

        elif self.platform_info.is_linux:
            # Use freedesktop system sounds on Linux
            sounds = {
                "critical": "alarm-clock-elapsed",
                "normal": "dialog-warning",
                "low": "complete",
            }
            sound = sounds.get(urgency, "dialog-warning")
            try:
                subprocess.run(
                    ["paplay", f"/usr/share/sounds/freedesktop/stereo/{sound}.oga"],
                    timeout=10,
                    capture_output=True,
                )
            except subprocess.TimeoutExpired:
                pass  # Sound playback timed out but notification sent
            except FileNotFoundError:
                pass  # paplay not found, skip silently
            except Exception:
                pass  # Other errors, skip silently

    def notify(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        callback: Callable[[], None] | None = None,
        sound: bool = False,
    ) -> bool:
        """Send a native desktop notification.

        Args:
            title: Notification title
            message: Notification body
            urgency: "low", "normal", "critical"
            callback: Optional callback function when notification is clicked
            sound: Whether to play an annoying alert sound

        Returns:
            True if notification sent successfully, False otherwise.
            Returns False if notifications unavailable (graceful degradation).
        """
        # Play sound first if enabled and available
        if sound:
            self._play_sound(urgency)

        # If notifications not available, print to console and return False
        if not self.notifications_available:
            print(f"[{title}] {message}")
            return False

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
            # Log error but don't fail - notification was attempted
            print(f"Warning: Error sending notification: {e}")
            return False

    def notify_reminder_due(
        self, reminder_text: str, sound: bool = False, callback: Callable | None = None
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

"""Cross-platform utilities and providers."""

import platform
from pathlib import Path
from typing import Literal


class PlatformProvider:
    """Platform-specific configuration and paths."""

    def __init__(self):
        """Initialize with current platform."""
        self.system = platform.system()
        self.is_macos = self.system == "Darwin"
        self.is_linux = self.system == "Linux"
        self.is_windows = self.system == "Windows"

    def get_app_data_dir(self) -> Path:
        """Get platform-specific app data directory.

        Returns:
            Path to app data directory (created if doesn't exist)
        """
        if self.is_macos:
            # macOS: ~/Library/Application Support/Remind
            app_dir = Path.home() / "Library" / "Application Support" / "Remind"
        elif self.is_linux:
            # Linux: Follow XDG spec, default to ~/.local/share/remind
            xdg_data = Path.home() / ".local" / "share"
            app_dir = xdg_data / "remind"
        elif self.is_windows:
            # Windows: %APPDATA%\Remind
            app_dir = Path.home() / "AppData" / "Roaming" / "Remind"
        else:
            # Fallback
            app_dir = Path.home() / ".remind"

        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir

    def get_config_dir(self) -> Path:
        """Get platform-specific config directory."""
        if self.is_linux:
            # Linux: Follow XDG spec, ~/.config/remind
            xdg_config = Path.home() / ".config"
            config_dir = xdg_config / "remind"
        else:
            # macOS/Windows: Use app data dir
            config_dir = self.get_app_data_dir()

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def get_logs_dir(self) -> Path:
        """Get platform-specific logs directory."""
        if self.is_linux:
            # Linux: ~/.local/share/remind/logs
            logs_dir = self.get_app_data_dir() / "logs"
        else:
            # macOS/Windows: app_data/logs
            logs_dir = self.get_app_data_dir() / "logs"

        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir

    def get_sound_player(self) -> str:
        """Get available sound player command.

        Returns:
            Command name (afplay, paplay, etc.)
        """
        if self.is_macos:
            return "afplay"
        elif self.is_linux:
            return "paplay"
        elif self.is_windows:
            return "powershell"
        else:
            return "unknown"

    def get_scheduler_backend(self) -> Literal["launchd", "systemd", "windows", "unknown"]:
        """Get scheduler backend for this platform.

        Returns:
            Backend name (launchd, systemd, windows, or unknown)
        """
        if self.is_macos:
            return "launchd"
        elif self.is_linux:
            return "systemd"
        elif self.is_windows:
            return "windows"
        else:
            return "unknown"

    def get_scheduler_service_name(self) -> str:
        """Get scheduler service name.

        Returns:
            Service identifier appropriate for this platform
        """
        if self.is_macos:
            return "com.remind.scheduler"
        elif self.is_linux:
            return "remind-scheduler"
        elif self.is_windows:
            return "RemindScheduler"
        else:
            return "remind-scheduler"

    def supports_notifications(self) -> bool:
        """Check if platform supports native notifications.

        Returns:
            True if platform supports notifications
        """
        return self.is_macos or self.is_linux

    def supports_sound(self) -> bool:
        """Check if platform theoretically supports sound playback.

        Returns:
            True if platform should support sound (actual support checked separately)
        """
        return self.is_macos or self.is_linux

    def get_notification_backend_name(self) -> str:
        """Get notification backend name.

        Returns:
            Backend description
        """
        if self.is_macos:
            return "native"
        elif self.is_linux:
            return "dbus"
        elif self.is_windows:
            return "windows_toast"
        else:
            return "unknown"

    def __repr__(self) -> str:
        """String representation."""
        return f"PlatformProvider(system={self.system})"


def get_platform() -> PlatformProvider:
    """Get the current platform provider.

    Returns:
        PlatformProvider instance for current system
    """
    return PlatformProvider()


def get_app_dir() -> Path:
    """Get application data directory (backwards compatible).

    Returns:
        Path to app data directory
    """
    provider = get_platform()
    return provider.get_app_data_dir()


def get_config_path() -> Path:
    """Get config file path (backwards compatible).

    Returns:
        Path to config.toml file
    """
    return get_platform().get_config_dir() / "config.toml"


def get_db_path() -> Path:
    """Get database path (backwards compatible).

    Returns:
        Path to reminders.db file
    """
    return get_platform().get_app_data_dir() / "reminders.db"


def get_license_path() -> Path:
    """Get license file path (backwards compatible).

    Returns:
        Path to license.json file
    """
    return get_platform().get_app_data_dir() / "license.json"


def get_logs_dir() -> Path:
    """Get logs directory (backwards compatible).

    Returns:
        Path to logs directory
    """
    return get_platform().get_logs_dir()

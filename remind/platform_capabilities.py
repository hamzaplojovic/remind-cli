"""Platform capability detection and health checks."""

import shutil
import subprocess


class PlatformCapabilities:
    """Check what's actually available on this system."""

    @staticmethod
    def has_command(cmd: str) -> bool:
        """Check if a command is available in PATH.

        Args:
            cmd: Command name to check

        Returns:
            True if command found in PATH
        """
        return shutil.which(cmd) is not None

    @staticmethod
    def test_sound_player(player: str) -> bool:
        """Test if a specific sound player is available and working.

        Args:
            player: Sound player command (afplay, paplay, etc.)

        Returns:
            True if player is available and responds to help
        """
        if not PlatformCapabilities.has_command(player):
            return False

        try:
            if player == "afplay":
                # afplay -h should return 0
                result = subprocess.run(
                    [player, "-h"],
                    capture_output=True,
                    timeout=2,
                )
                return result.returncode == 0
            elif player == "paplay":
                # paplay --version should work
                result = subprocess.run(
                    [player, "--version"],
                    capture_output=True,
                    timeout=2,
                )
                return result.returncode == 0
            else:
                # For unknown players, just check if they're in PATH
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def test_notifications() -> bool:
        """Test if notifications are available.

        Returns:
            True if notify-py can be imported
        """
        try:
            import notifypy  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def test_systemd() -> bool:
        """Test if systemd is available (Linux).

        Returns:
            True if systemctl command is available
        """
        return PlatformCapabilities.has_command("systemctl")

    @staticmethod
    def test_launchctl() -> bool:
        """Test if launchctl is available (macOS).

        Returns:
            True if launchctl command is available
        """
        return PlatformCapabilities.has_command("launchctl")

    @staticmethod
    def test_launchd_user_services() -> bool:
        """Test if macOS launchd user services are available.

        Returns:
            True if launchctl can access user services
        """
        if not PlatformCapabilities.test_launchctl():
            return False

        try:
            # Try to list user LaunchAgents
            result = subprocess.run(
                ["launchctl", "list"],
                capture_output=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def test_dbus() -> bool:
        """Test if D-Bus is available (Linux notifications).

        Returns:
            True if dbus-daemon is running
        """
        try:
            result = subprocess.run(
                ["pgrep", "-x", "dbus-daemon"],
                capture_output=True,
                timeout=1,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @staticmethod
    def get_capabilities_report() -> dict[str, bool]:
        """Get a comprehensive report of all available capabilities.

        Returns:
            Dictionary mapping feature names to availability
        """
        from remind.platform_utils import get_platform

        platform = get_platform()

        report = {
            "platform": platform.system,
            "notifications_available": PlatformCapabilities.test_notifications(),
            "sound_player_available": PlatformCapabilities.test_sound_player(
                platform.get_sound_player()
            ),
        }

        if platform.is_macos:
            report["launchctl_available"] = PlatformCapabilities.test_launchctl()
            report["launchd_services_available"] = PlatformCapabilities.test_launchd_user_services()
        elif platform.is_linux:
            report["systemd_available"] = PlatformCapabilities.test_systemd()
            report["dbus_available"] = PlatformCapabilities.test_dbus()

        return report

    @staticmethod
    def print_report() -> None:
        """Print a human-readable capabilities report."""
        report = PlatformCapabilities.get_capabilities_report()

        print("\n📊 Platform Capabilities Report")
        print("=" * 50)
        print(f"Platform: {report.pop('platform')}")
        print()

        for feature, available in report.items():
            status = "✅" if available else "❌"
            feature_name = feature.replace("_", " ").title()
            print(f"  {status} {feature_name}")

        print("=" * 50)


def check_critical_capabilities() -> list[str]:
    """Check for critical capability issues.

    Returns:
        List of warning messages for missing critical features
    """
    warnings = []
    report = PlatformCapabilities.get_capabilities_report()

    if not report["notifications_available"]:
        warnings.append("⚠️  Notifications not available. Install with: pip install notify-py")

    if not report["sound_player_available"]:
        from remind.platform_utils import get_platform

        platform = get_platform()
        player = platform.get_sound_player()

        if platform.is_linux:
            warnings.append(
                f"⚠️  Sound player '{player}' not found. Install with: sudo apt install pulseaudio"
            )
        elif platform.is_macos:
            warnings.append(
                f"⚠️  Sound player '{player}' not found. "
                "This should not happen on standard macOS installations."
            )

    if report.get("systemd_available") is False and report.get("launchctl_available") is False:
        warnings.append("⚠️  No supported scheduler backend found. Daemon mode will not work.")

    return warnings


if __name__ == "__main__":
    """Run capability checks when invoked as a module."""
    PlatformCapabilities.print_report()
    warnings = check_critical_capabilities()
    if warnings:
        print()
        for warning in warnings:
            print(warning)

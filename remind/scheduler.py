"""Background scheduler for Remind."""

import platform
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from remind.config import load_config
from remind.db import Database
from remind.models import Reminder
from remind.notifications import NotificationManager
from remind.premium import get_license_manager


class SchedulerState:
    """Tracks scheduler state and nudge timing."""

    def __init__(self):
        """Initialize scheduler state."""
        self.running = False
        self.last_nudge_times: dict[int, datetime] = {}
        self.last_check = datetime.now(timezone.utc)

    def should_nudge(
        self, reminder_id: int, nudge_intervals: list[int], last_due_time: datetime
    ) -> bool:
        """
        Check if a reminder should be nudged.

        Returns True if enough time has passed since last nudge.
        """
        # First nudge: reminder hasn't been nudged yet but is overdue
        if reminder_id not in self.last_nudge_times:
            # Check if reminder is past first nudge interval
            time_since_due = (datetime.now(timezone.utc) - last_due_time).total_seconds() / 60
            return time_since_due > nudge_intervals[0] if nudge_intervals else False

        last_nudge = self.last_nudge_times[reminder_id]
        # Get the next nudge interval
        time_since_due = (datetime.now(timezone.utc) - last_due_time).total_seconds() / 60

        for interval in nudge_intervals:
            if (
                time_since_due > interval
                and (datetime.now(timezone.utc) - last_nudge).total_seconds()
                > interval * 60
            ):
                return True

        return False

    def record_nudge(self, reminder_id: int) -> None:
        """Record that a nudge was sent for a reminder."""
        self.last_nudge_times[reminder_id] = datetime.now(timezone.utc)

    def record_done(self, reminder_id: int) -> None:
        """Record that a reminder was marked done."""
        if reminder_id in self.last_nudge_times:
            del self.last_nudge_times[reminder_id]


class Scheduler:
    """Background scheduler for sending reminders."""

    def __init__(self, db: Optional[Database] = None):
        """Initialize scheduler."""
        self.db = db or Database()
        self.config = load_config()
        self.license_manager = get_license_manager()
        self.state = SchedulerState()
        self.running = False

        # Try to initialize notifications
        try:
            self.notifications = NotificationManager()
        except ImportError:
            print("Warning: Notifications not available")
            self.notifications = None  # type: ignore

    def start(self) -> None:
        """Start the scheduler daemon."""
        self.state.running = True
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        print(f"Scheduler started. Check interval: {self.config.scheduler_interval_minutes}m")

        try:
            while self.running:
                self._check_and_notify()
                time.sleep(self.config.scheduler_interval_minutes * 60)
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
            self._shutdown()

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print("\nShutting down scheduler...")
        self.running = False
        self._shutdown()
        sys.exit(0)

    def _shutdown(self) -> None:
        """Clean shutdown."""
        self.state.running = False
        self.db.close()

    def _check_and_notify(self) -> None:
        """Check for due reminders and send notifications."""
        try:
            now = datetime.now(timezone.utc)
            due_reminders = self.db.get_due_reminders(now)

            for reminder in due_reminders:
                # Check if this is a new due reminder or an existing one
                is_new_due = reminder.id not in self.state.last_nudge_times

                if is_new_due:
                    # First notification for this reminder
                    self._send_notification(reminder)
                    self.state.record_nudge(reminder.id)
                elif self.license_manager.has_license():
                    # Check if we should send a nudge (premium feature)
                    if self.state.should_nudge(
                        reminder.id,
                        self.config.nudge_intervals_minutes,
                        reminder.due_at,
                    ):
                        self._send_nudge(reminder)
                        self.state.record_nudge(reminder.id)

        except Exception as e:
            print(f"Error in scheduler check: {e}")

    def _send_notification(self, reminder: Reminder) -> None:
        """Send initial notification for a due reminder."""
        if not self.notifications:
            print(f"Reminder due: {reminder.text}")
            return

        try:
            self.notifications.notify_reminder_due(
                reminder.text,
                sound=self.config.notification_sound_enabled,
            )
        except Exception as e:
            print(f"Error sending notification: {e}")

    def _send_nudge(self, reminder: Reminder) -> None:
        """Send nudge notification for an overdue reminder (premium)."""
        if not self.notifications:
            print(f"Nudge: {reminder.text}")
            return

        try:
            self.notifications.notify_nudge(
                reminder.text,
                sound=self.config.notification_sound_enabled,
            )
        except Exception as e:
            print(f"Error sending nudge: {e}")

    def install_background_service(self) -> None:
        """Install scheduler as a background service."""
        system = platform.system()

        if system == "Darwin":
            self._install_macos_agent()
        elif system == "Linux":
            self._install_linux_service()
        else:
            print(f"Unsupported platform: {system}")

    def _install_macos_agent(self) -> None:
        """Install macOS launchd agent."""
        import os

        # Get the path to the remind binary
        remind_path = os.path.abspath(sys.argv[0])

        # Create LaunchAgent directory
        la_dir = Path.home() / "Library" / "LaunchAgents"
        la_dir.mkdir(parents=True, exist_ok=True)

        # Create plist file
        plist_path = la_dir / "com.remind.scheduler.plist"

        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.remind.scheduler</string>
    <key>Program</key>
    <string>{remind_path}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{remind_path}</string>
        <string>scheduler</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home()}/.remind/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/.remind/logs/scheduler.error.log</string>
</dict>
</plist>
"""

        # Write plist file
        plist_path.write_text(plist_content)

        # Create logs directory
        logs_dir = Path.home() / ".remind" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Load the service
        try:
            subprocess.run(
                ["launchctl", "load", str(plist_path)],
                check=True,
                capture_output=True,
            )
            print(f"✓ macOS LaunchAgent installed: {plist_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error loading LaunchAgent: {e.stderr.decode()}")

    def _install_linux_service(self) -> None:
        """Install Linux systemd user service."""
        import os

        # Get the path to the remind binary
        remind_path = os.path.abspath(sys.argv[0])

        # Create systemd user services directory
        sd_dir = Path.home() / ".config" / "systemd" / "user"
        sd_dir.mkdir(parents=True, exist_ok=True)

        # Create service file
        service_path = sd_dir / "remind-scheduler.service"

        service_content = f"""[Unit]
Description=Remind - Background Reminder Scheduler
After=network.target

[Service]
Type=simple
ExecStart={remind_path} scheduler
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
"""

        # Write service file
        service_path.write_text(service_content)
        service_path.chmod(0o644)

        # Create logs directory
        logs_dir = Path.home() / ".remind" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Reload and enable the service
        try:
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["systemctl", "--user", "enable", "remind-scheduler.service"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["systemctl", "--user", "start", "remind-scheduler.service"],
                check=True,
                capture_output=True,
            )
            print(f"✓ Linux systemd service installed: {service_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error setting up systemd service: {e.stderr.decode()}")


def run_scheduler() -> None:
    """Entry point for running the scheduler as a daemon."""
    db = Database()
    scheduler = Scheduler(db)
    scheduler.start()

"""CLI interface for Remind."""

from datetime import datetime, timezone
from typing import Optional

import typer
from dateparser import parse as dateparser_parse

from remind.ai import get_ai_manager
from remind.config import load_config, save_config
from remind.db import Database
from remind.models import Config as ConfigModel
from remind.models import PriorityLevel, Reminder
from remind.premium import PremiumRequired, get_license_manager
from remind.scheduler import Scheduler
from remind.utils import format_datetime, parse_priority

app = typer.Typer(help="Remind: AI-powered reminder CLI")


def ensure_scheduler_installed() -> None:
    """Ensure scheduler is installed on first use (auto-setup on first reminder)."""
    import os
    import platform

    system = platform.system()
    scheduler_installed = False

    if system == "Darwin":  # macOS
        plist_path = os.path.expanduser(
            "~/Library/LaunchAgents/com.remind.scheduler.plist"
        )
        scheduler_installed = os.path.exists(plist_path)
    elif system == "Linux":
        service_path = os.path.expanduser(
            "~/.config/systemd/user/remind-scheduler.service"
        )
        scheduler_installed = os.path.exists(service_path)

    # Auto-install on first use
    if not scheduler_installed and system in ("Darwin", "Linux"):
        try:
            from remind.scheduler import Scheduler

            typer.echo(
                "ℹ️  Setting up background scheduler for the first time...",
                err=True,
            )
            s = Scheduler()
            s.install_background_service()
            typer.echo(
                "✓ Scheduler installed! Reminders will now run in the background.",
                err=True,
            )
        except Exception as e:
            # Don't fail if scheduler setup doesn't work - graceful degradation
            typer.echo(
                f"⚠️  Could not auto-install scheduler: {e}. "
                "Run 'remind scheduler --install' manually.",
                err=True,
            )


def display_reminder(
    reminder: Reminder,
    show_priority: bool = False,
    show_ai_text: bool = False,
) -> None:
    """Display a single reminder with consistent formatting."""
    status = "✓" if reminder.done_at else "○"
    typer.echo(f"{status} ID {reminder.id}: {reminder.text}")

    due_str = format_datetime(reminder.due_at)
    if show_priority:
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            reminder.priority.value, "⚪"
        )
        typer.echo(f"  {due_str} {priority_icon}")
    else:
        typer.echo(f"  {due_str}")

    if show_ai_text and reminder.ai_suggested_text:
        typer.echo(f"  Suggested: {reminder.ai_suggested_text}")


def get_db() -> Database:
    """Get database instance."""
    return Database()


def parse_datetime(text: str) -> Optional[datetime]:
    """Parse natural language datetime string."""
    parsed = dateparser_parse(text, settings={"RETURN_AS_TIMEZONE_AWARE": True})
    if parsed:
        return parsed
    # Try parsing as absolute datetime
    return None


@app.command()
def add(
    text: str = typer.Argument(..., help="Reminder text"),
    due: Optional[str] = typer.Option(
        None, "--due", "-d", help="Due time (natural language, e.g., 'tomorrow 3pm')"
    ),
    priority: Optional[str] = typer.Option(
        None, "--priority", "-p", help="Priority level: high, medium, low"
    ),
    project: Optional[str] = typer.Option(
        None, "--project", "-c", help="Project context"
    ),
    no_ai: bool = typer.Option(False, "--no-ai", help="Skip AI suggestions"),
) -> None:
    """Add a new reminder."""
    # Ensure scheduler is running in background
    ensure_scheduler_installed()

    db = get_db()
    config = load_config()

    # Parse due time
    if due:
        due_dt = parse_datetime(due)
        if not due_dt:
            typer.echo(f"✗ Could not parse due time: {due}", err=True)
            typer.echo("Examples: 'tomorrow', 'next monday 3pm', 'in 2 hours', '2pm'", err=True)
            raise typer.Exit(1)
    else:
        # Default to today at 9am
        now = datetime.now(timezone.utc)
        due_dt = datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=9,
            tzinfo=timezone.utc,
        )

    # Parse priority
    if priority:
        priority_level = parse_priority(priority)
        if priority_level == PriorityLevel.MEDIUM and priority.lower() not in (
            "medium",
            "med",
            "m",
        ):
            # Only error if input wasn't valid and didn't default to MEDIUM
            valid_values = ", ".join([p.value for p in PriorityLevel])
            typer.echo(f"Invalid priority: {priority}. Valid values: {valid_values}")
            raise typer.Exit(1)
    else:
        priority_level = PriorityLevel.MEDIUM

    # Check for AI rephrasing
    ai_suggested_text = None
    if config.ai_rephrasing_enabled and not no_ai:
        license_manager = get_license_manager()
        if license_manager.has_license():
            try:
                license_obj = license_manager.get_license()
                if config.ai_backend_url and license_obj:
                    ai_manager = get_ai_manager(
                        backend_url=config.ai_backend_url,
                        license_token=license_obj.token,
                    )
                    if ai_manager:
                        ai_response = ai_manager.suggest_rephrasing(text)
                        ai_suggested_text = ai_response.suggested_text
                        # Optionally override priority and due time
                        if ai_response.priority:
                            priority_level = ai_response.priority
                        if ai_response.due_time_suggestion:
                            parsed_due = parse_datetime(ai_response.due_time_suggestion)
                            if parsed_due:
                                due_dt = parsed_due
                        typer.echo(f"AI suggestion: {ai_suggested_text}")
                        if ai_response.cost_estimate:
                            typer.echo(f"  Cost: ${ai_response.cost_estimate:.4f}")
                else:
                    typer.echo(
                        "AI backend not configured. Set ai_backend_url in settings.",
                        err=True,
                    )
            except PremiumRequired:
                pass
            except Exception as e:
                typer.echo(f"AI error: {e}", err=True)

    # Add reminder to database
    reminder = db.add_reminder(
        text=text,
        due_at=due_dt,
        priority=priority_level,
        project_context=project,
        ai_suggested_text=ai_suggested_text,
    )

    typer.echo(f"✓ Reminder added (ID: {reminder.id})")
    typer.echo(f"  Text: {reminder.text}")
    typer.echo(f"  Due: {reminder.due_at}")
    if ai_suggested_text:
        typer.echo(f"  Suggested: {ai_suggested_text}")


@app.command()
def list(
    all: bool = typer.Option(False, "--all", "-a", help="Show all reminders including done"),
    project: Optional[str] = typer.Option(
        None, "--project", "-c", help="Filter by project"
    ),
) -> None:
    """List reminders."""
    db = get_db()

    if all:
        reminders = db.list_all_reminders()
    else:
        reminders = db.list_active_reminders()

    if project:
        reminders = [r for r in reminders if r.project_context == project]

    if not reminders:
        typer.echo("No reminders found.")
        return

    # Categorize reminders by due date
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    def ensure_aware(dt):
        """Convert naive datetime to aware (UTC)."""
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt

    overdue = [r for r in reminders if ensure_aware(r.due_at) < now]
    due_today = [r for r in reminders if ensure_aware(r.due_at).date() == now.date()]
    upcoming = [r for r in reminders if ensure_aware(r.due_at) > now]

    # Show summary
    summary_parts = [f"{len(reminders)} total"]
    if overdue:
        summary_parts.append(f"{len(overdue)} overdue")
    if due_today:
        summary_parts.append(f"{len(due_today)} today")
    if upcoming:
        summary_parts.append(f"{len(upcoming)} upcoming")

    typer.echo(f"\n📋 Reminders: {', '.join(summary_parts)}")

    # Show overdue first (most important)
    if overdue:
        typer.echo("\n⚠️  Overdue:")
        for reminder in overdue:
            display_reminder(reminder, show_priority=True, show_ai_text=False)

    # Then due today
    if due_today:
        typer.echo("\n📅 Due today:")
        for reminder in due_today:
            display_reminder(reminder, show_priority=True, show_ai_text=False)

    # Then upcoming (limit to 10)
    if upcoming:
        typer.echo("\n📆 Upcoming:")
        for reminder in upcoming[:10]:
            display_reminder(reminder, show_priority=True, show_ai_text=False)
        if len(upcoming) > 10:
            typer.echo(f"  ... and {len(upcoming) - 10} more")


@app.command()
def done(reminder_id: int = typer.Argument(..., help="Reminder ID")) -> None:
    """Mark a reminder as done."""
    db = get_db()
    try:
        reminder = db.mark_done(reminder_id)

        if reminder:
            typer.echo(f"✓ Reminder {reminder_id} marked done")
        else:
            typer.echo(f"✗ Reminder {reminder_id} not found")
            raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def search(query: str = typer.Argument(..., help="Search query")) -> None:
    """Search reminders."""
    db = get_db()
    results = db.search_reminders(query)

    if not results:
        typer.echo(f"No reminders found matching: {query}")
        return

    typer.echo(f"\n🔍 Results for '{query}':")
    for reminder in results:
        display_reminder(reminder, show_priority=False, show_ai_text=False)


@app.command()
def settings(
    timezone: Optional[str] = typer.Option(None, "--timezone", help="Set timezone"),
    interval: Optional[int] = typer.Option(
        None, "--interval", help="Scheduler check interval in minutes"
    ),
    ai_enabled: Optional[bool] = typer.Option(
        None, "--ai/--no-ai", help="Enable/disable AI suggestions"
    ),
    sound_enabled: Optional[bool] = typer.Option(
        None, "--sound/--no-sound", help="Enable/disable notification sounds"
    ),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="OpenAI API key"),
    show: bool = typer.Option(False, "--show", help="Show current settings"),
) -> None:
    """Manage settings."""
    config = load_config()

    if show:
        typer.echo("\n⚙️  Current Settings:")
        typer.echo(f"  Timezone: {config.timezone}")
        typer.echo(f"  Scheduler interval: {config.scheduler_interval_minutes}m")
        typer.echo(f"  AI suggestions: {'enabled' if config.ai_rephrasing_enabled else 'disabled'}")
        typer.echo(f"  Notification sounds: {'enabled' if config.notification_sound_enabled else 'disabled'}")
        typer.echo(f"  Nudge intervals: {config.nudge_intervals_minutes}")
        return

    # Update settings
    if timezone:
        config.timezone = timezone
        typer.echo(f"✓ Timezone set to {timezone}")
    if interval:
        config.scheduler_interval_minutes = interval
        typer.echo(f"✓ Scheduler interval set to {interval}m")
    if ai_enabled is not None:
        config.ai_rephrasing_enabled = ai_enabled
        typer.echo(f"✓ AI suggestions {'enabled' if ai_enabled else 'disabled'}")
    if sound_enabled is not None:
        config.notification_sound_enabled = sound_enabled
        typer.echo(f"✓ Notification sounds {'enabled' if sound_enabled else 'disabled'}")
    if api_key:
        config.openai_api_key = api_key
        typer.echo("✓ OpenAI API key set")

    save_config(config)


@app.command()
def report() -> None:
    """Show analytics dashboard (premium feature)."""
    db = get_db()
    license_manager = get_license_manager()

    try:
        if not license_manager.has_license():
            typer.echo("This feature requires a premium license.")
            raise typer.Exit(1)
    except PremiumRequired:
        typer.echo("This feature requires a premium license.")
        raise typer.Exit(1)

    all_reminders = db.list_all_reminders()
    active = [r for r in all_reminders if not r.done_at]
    done = [r for r in all_reminders if r.done_at]

    typer.echo("\n📊 Analytics:")
    typer.echo(f"  Total reminders: {len(all_reminders)}")
    typer.echo(f"  Active: {len(active)}")
    typer.echo(f"  Completed: {len(done)}")


@app.command()
def upgrade() -> None:
    """Upgrade Remind CLI to the latest version."""
    import subprocess
    import os

    repo_dir = os.path.expanduser("~/remind-cli")

    if not os.path.exists(repo_dir):
        typer.echo("✗ Remind CLI not found at ~/remind-cli", err=True)
        raise typer.Exit(1)

    typer.echo("Upgrading Remind CLI...")

    try:
        # Pull latest changes
        subprocess.run(
            ["git", "-C", repo_dir, "pull"],
            check=True,
            capture_output=True,
        )
        typer.echo("✓ Downloaded latest version")

        # Sync dependencies
        subprocess.run(
            ["uv", "sync"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        typer.echo("✓ Updated dependencies")
        typer.echo("✓ Remind CLI upgraded successfully!")

    except subprocess.CalledProcessError as e:
        typer.echo(f"✗ Upgrade failed: {e.stderr.decode() if e.stderr else str(e)}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"✗ Error during upgrade: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def remove() -> None:
    """Uninstall Remind CLI from system."""
    import subprocess
    import os
    import shutil

    repo_dir = os.path.expanduser("~/remind-cli")
    bin_file = os.path.expanduser("~/.local/bin/remind")
    config_dir = os.path.expanduser("~/.remind")

    typer.echo("This will uninstall Remind CLI from your system.")
    typer.echo(f"  • Remove: {repo_dir}")
    typer.echo(f"  • Remove: {bin_file}")
    typer.echo(f"  • Keep: {config_dir} (your data)")

    if not typer.confirm("Continue?"):
        typer.echo("Cancelled.")
        return

    try:
        # Stop scheduler if running
        try:
            subprocess.run(
                ["systemctl", "--user", "stop", "remind-scheduler.service"],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass

        # Remove global command
        if os.path.exists(bin_file):
            os.remove(bin_file)
            typer.echo(f"✓ Removed {bin_file}")

        # Remove repository
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            typer.echo(f"✓ Removed {repo_dir}")

        typer.echo("✓ Remind CLI uninstalled successfully")
        typer.echo(f"💾 Your reminders are still saved in {config_dir}")

    except Exception as e:
        typer.echo(f"✗ Error during uninstall: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def scheduler(
    install: bool = typer.Option(False, "--install", help="Install as background service"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Uninstall background service"),
) -> None:
    """Run background scheduler or manage service."""
    if install:
        typer.echo("Installing scheduler as background service...")
        from remind.scheduler import Scheduler
        s = Scheduler()
        s.install_background_service()
        typer.echo("✓ Scheduler installed. It will start on next login/boot.")
        return

    if uninstall:
        typer.echo("Uninstall not yet implemented.")
        return

    # Run scheduler daemon
    typer.echo("Starting scheduler daemon (Ctrl+C to stop)...")
    from remind.scheduler import run_scheduler
    run_scheduler()


@app.command()
def doctor() -> None:
    """Diagnostic command: test all system components."""
    import subprocess

    typer.echo("\n🔍 Remind System Diagnostic\n")
    typer.echo("=" * 50)

    # Test 1: Database
    typer.echo("\n1️⃣  Testing database...")
    try:
        db = get_db()
        test_reminder = db.add_reminder(
            text="[TEST] Doctor diagnostic - can be deleted",
            due_at=datetime.now(timezone.utc),
            priority=PriorityLevel.LOW,
        )
        typer.echo(f"   ✓ Database OK (created reminder ID {test_reminder.id})")

        # Clean up test reminder
        db.mark_done(test_reminder.id)
        db.close()
    except Exception as e:
        typer.echo(f"   ✗ Database failed: {e}", err=True)
        raise typer.Exit(1)

    # Test 2: Notifications
    typer.echo("\n2️⃣  Testing notifications...")
    try:
        from remind.notifications import NotificationManager

        nm = NotificationManager()
        if not nm.is_supported():
            typer.echo("   ⚠️  Notifications not available (graceful degradation)")
        else:
            result = nm.notify_reminder_due("[TEST] Remind diagnostic notification")
            if result:
                typer.echo("   ✓ Notifications OK (check your system tray)")
            else:
                typer.echo("   ⚠️  Notifications may not work properly")
    except Exception as e:
        typer.echo(f"   ⚠️  Notifications warning: {e}")

    # Test 3: Scheduler
    typer.echo("\n3️⃣  Testing scheduler...")
    try:
        from remind.scheduler import Scheduler

        scheduler = Scheduler()
        if scheduler.notifications:
            typer.echo("   ✓ Scheduler OK (notifications available)")
        else:
            typer.echo("   ✓ Scheduler OK (notifications unavailable but scheduler works)")
    except Exception as e:
        typer.echo(f"   ✗ Scheduler failed: {e}", err=True)

    # Test 4: Background Service
    typer.echo("\n4️⃣  Checking background service...")
    try:
        import platform
        import os

        system = platform.system()
        if system == "Darwin":  # macOS
            plist_path = os.path.expanduser(
                "~/Library/LaunchAgents/com.remind.scheduler.plist"
            )
            if os.path.exists(plist_path):
                typer.echo("   ✓ Background service installed (macOS LaunchAgent)")
            else:
                typer.echo(
                    "   ⚠️  Background service NOT installed. Run: remind scheduler --install"
                )
        elif system == "Linux":
            service_path = os.path.expanduser(
                "~/.config/systemd/user/remind-scheduler.service"
            )
            if os.path.exists(service_path):
                # Check if running
                try:
                    result = subprocess.run(
                        ["systemctl", "--user", "is-active", "remind-scheduler.service"],
                        capture_output=True,
                        timeout=5,
                    )
                    if result.returncode == 0:
                        typer.echo("   ✓ Background service installed and RUNNING (systemd)")
                    else:
                        typer.echo(
                            "   ⚠️  Background service installed but NOT RUNNING. "
                            "Start it: systemctl --user start remind-scheduler.service"
                        )
                except Exception:
                    typer.echo(
                        "   ⚠️  Background service installed (systemd) but status unknown"
                    )
            else:
                typer.echo(
                    "   ⚠️  Background service NOT installed. Run: remind scheduler --install"
                )
        else:
            typer.echo(f"   ℹ️  Unknown platform: {system}")
    except Exception as e:
        typer.echo(f"   ⚠️  Could not check background service: {e}")

    # Test 5: Configuration
    typer.echo("\n5️⃣  Checking configuration...")
    try:
        config = load_config()
        typer.echo(f"   ✓ Configuration loaded")
        typer.echo(f"     - Scheduler interval: {config.scheduler_interval_minutes}m")
        typer.echo(
            f"     - Notifications: {'enabled' if config.notifications_enabled else 'disabled'}"
        )
        typer.echo(
            f"     - AI suggestions: {'enabled' if config.ai_rephrasing_enabled else 'disabled'}"
        )
    except Exception as e:
        typer.echo(f"   ✗ Configuration error: {e}", err=True)

    # Summary
    typer.echo("\n" + "=" * 50)
    typer.echo(
        "\n✓ System diagnostic complete!\n"
        "💡 Tips:\n"
        "   • To install the background scheduler: remind scheduler --install\n"
        "   • To test it's working: remind add 'test' --due 'now'\n"
        "   • To view settings: remind settings --show\n"
    )


if __name__ == "__main__":
    app()

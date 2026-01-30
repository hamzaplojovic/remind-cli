# Remind Development Guide

## Project Structure

```
remind/
├── remind/              # Main package
│   ├── __init__.py
│   ├── __main__.py      # Entry point
│   ├── cli.py           # CLI commands (Typer)
│   ├── db.py            # SQLite operations
│   ├── config.py        # Configuration management
│   ├── models.py        # Pydantic data models
│   ├── scheduler.py     # Background scheduler daemon
│   ├── notifications.py # Desktop notifications (notify-py)
│   ├── platform_utils.py       # Platform abstraction layer (macOS/Linux/Windows)
│   ├── platform_capabilities.py # System capability detection
│   ├── ai.py           # OpenAI integration (premium)
│   ├── premium.py      # License verification
│   └── plugins.py      # Plugin system (v1.1+)
├── tests/              # Pytest suite
├── .github/workflows/  # CI/CD
│   └── test.yml        # Matrix testing (macOS/Linux, Python 3.12-3.13)
├── build_tools/        # Build & distribution
│   ├── build.py        # PyInstaller wrapper
│   ├── install.sh      # Curl installer script
│   ├── homebrew_formula.rb
│   ├── systemd_service.service
│   └── macos_launchd.plist
├── README.md
├── pyproject.toml      # Python project config
└── CLAUDE.md          # This file
```

## Core Principles

1. **Module Isolation**: Each module has clear responsibility (db, cli, scheduler, etc.)
2. **Premium Gating**: Premium features raise `PremiumRequired` or check license before executing
3. **UTC Storage**: All times stored as UTC in database, converted to user timezone on display
4. **Soft Deletes**: Reminders marked done (not deleted) for analytics
5. **No Remote Backend**: License verification is local-only (read from `~/.remind/license.json`)
6. **Cross-Platform**: Graceful degradation on macOS, Linux, and Windows

## Platform Support & Requirements

### macOS (Primary)
- **Python**: 3.12+
- **Included by default**:
  - `afplay` for sound playback
  - `launchctl` for daemon services
  - Native notification center
- **Via pip**: `notify-py`
- **Status**: ✅ Fully supported
- **App data location**: `~/Library/Application Support/Remind`

### Linux (Primary)
- **Python**: 3.12+
- **Required packages**:
  - `libnotify-bin`: Desktop notifications (`sudo apt install libnotify-bin`)
  - `pulseaudio` or similar: Sound playback (usually pre-installed)
- **Via pip**: `notify-py[dbus]`
- **Scheduler**: systemd user services (all modern distros)
- **Status**: ✅ Fully supported
- **App data location**: `~/.local/share/remind` (XDG spec compliant)

### Windows (Experimental)
- **Python**: 3.12+
- **Status**: ❌ Not yet supported (planned for v1.1)
- **Limitations**:
  - No native daemon service support
  - Notifications and sound not implemented

### Cross-Platform Compatibility

The app uses **graceful degradation**:

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| Reminders (core) | ✅ | ✅ | ✅ |
| Desktop Notifications | ✅ | ✅ | ❌ |
| Sound Alerts | ✅ | ✅ (PulseAudio) | ❌ |
| Daemon Service | ✅ (launchd) | ✅ (systemd) | ❌ |
| Automatic Scheduling | ✅ | ✅ | Manual only |

**Graceful Degradation**: If a feature is unavailable, the app:
- Continues to function with console output instead
- Prints warnings but doesn't crash
- Allows users to run the app on unsupported systems

### Platform Detection

- `remind.platform_utils.py`: Provides platform-specific paths and configuration
- `remind.platform_capabilities.py`: Detects available features at runtime
- Tests use `skip_if_not_macos`, `skip_if_not_linux`, `skip_if_no_notifications`, etc.

### Running System Diagnostics

```bash
remind doctor
```

This command checks:
- Database connectivity
- Notification system availability
- Sound playback capability
- Scheduler daemon status
- Configuration validity

## Key Design Decisions

### Database
- **SQLite** at `~/.remind/reminders.db`
- **Soft deletes**: `done_at` column tracks completion
- **UTC timezone**: All `due_at` stored in UTC
- **Simple schema**: No complex relationships, optimized for queries

### CLI
- **Typer** for argument parsing
- **Entry point**: `remind.cli:app` from pyproject.toml
- **Commands**: add, list, done, search, settings, report, scheduler

### Scheduler
- **Python daemon**: Not systemd/launchd directly, can spawn them
- **1-minute intervals**: Configurable in config.toml
- **Event-driven notifications**: Check for due reminders every interval
- **Nudge escalation**: Premium feature, re-notify at intervals

### Premium
- **LicenseManager**: Singleton that reads `~/.remind/license.json`
- **@requires_premium** decorator: Raises PremiumRequired if no license
- **Local tokens**: No server validation needed
- **One-time permanent**: Tokens don't expire

### AI Integration
- **APIManager**: Wraps OpenAI client
- **Model**: gpt-5-nano (explicitly requested, adjust if not available)
- **Async support**: Ready for async/await (currently sync)
- **Error handling**: Graceful fallback if API fails

## Development Workflow

### Adding a Feature

1. **Decide module**: Where does the logic live?
   - User input? → `cli.py`
   - Data storage? → `db.py`
   - Background job? → `scheduler.py`
   - Premium? → `premium.py` or `ai.py`

2. **Add model if needed**: Update `models.py` with Pydantic model
3. **Implement logic**: Write function in appropriate module
4. **Add tests**: Add test in `tests/test_<module>.py`
5. **Test**: `pytest tests/`
6. **Verify imports**: Make sure circular dependencies don't exist

### Adding a CLI Command

1. Add function to `remind/cli.py` with `@app.command()` decorator
2. Use Typer for arguments and options
3. Call db/config/scheduler methods as needed
4. Test with `remind <command> --help` and manual runs

### Adding a Premium Feature

1. Put logic in `premium.py`, `ai.py`, or feature-specific module
2. Decorate with `@requires_premium` or call `license_manager.require_premium()`
3. Test without license (should raise `PremiumRequired`)
4. Test with license (should work)

## Testing Strategy

### Unit Tests
- Test individual functions in isolation
- Mock external dependencies (OpenAI, notifications)
- Use fixtures for test database

### Integration Tests
- Test CLI commands end-to-end
- Verify database operations
- Check notification triggering

### Run Tests
```bash
pytest tests/                    # Run all tests
pytest tests/test_db.py         # Run specific test file
pytest -k "test_add"            # Run tests matching name
pytest --cov=remind tests/      # Show coverage
```

## Building & Distribution

### Build Binary
```bash
python build_tools/build.py
# Output: dist/remind (macOS/Linux single file)
```

### Test Binary
```bash
dist/remind --help
dist/remind add "test"
dist/remind list
```

### Distribution Strategy

**v0.1.0 (MVP):**
- GitHub Releases: Upload binaries for macOS x86_64 & arm64, Linux x86_64
- Homebrew: Create `homebrew-remind` tap with formula

**v1.1+:**
- Linux package managers (deb, rpm, AUR)
- Auto-update mechanism
- Windows support (optional)

## Environment Variables

- `OPENAI_API_KEY`: OpenAI API key (if not in config.toml)
- `REMIND_TIMEZONE`: Override timezone
- `REMIND_SCHEDULER_INTERVAL_MINUTES`: Override scheduler interval

## Configuration Files

**`~/.remind/config.toml`:**
```toml
[remind]
timezone = "UTC"
scheduler_interval_minutes = 1
notifications_enabled = true
notification_sound_enabled = true
ai_rephrasing_enabled = true
openai_api_key = "sk-..."  # Optional
nudge_intervals_minutes = [5, 15, 60]
```

**`~/.remind/license.json`:**
```json
{
  "token": "token-string",
  "email": "user@example.com",
  "created_at": "2025-01-30T12:00:00"
}
```

## Common Tasks

### Debug Database
```python
from remind.db import Database
db = Database()
reminders = db.list_all_reminders()
for r in reminders:
    print(f"{r.id}: {r.text} -> {r.due_at}")
```

### Test Premium Feature
```python
from remind.premium import get_license_manager
manager = get_license_manager()
manager.create_license("test-token-123", email="test@example.com")
# Now @requires_premium will work
```

### Check Scheduler
```bash
# macOS
launchctl list | grep remind
ps aux | grep "remind scheduler"

# Linux
systemctl --user status remind-scheduler
journalctl --user -u remind-scheduler -f
```

## Dependencies

**Core:**
- typer: CLI framework
- pydantic: Data validation
- sqlalchemy: ORM
- dateparser: Natural language dates
- notify-py: Desktop notifications
- openai: OpenAI API

**Dev:**
- pytest: Testing
- ruff: Linting
- mypy: Type checking

**Build:**
- pyinstaller: Binary creation
- hatchling: Package building

## Common Errors & Fixes

### `Import remind error`
- Install dev dependencies: `pip install -e ".[dev]"`
- Ensure you're in virtual environment

### `notify-py not found`
- Install: `pip install notify-py`
- On Linux, requires libnotify: `sudo apt install libnotify-bin`

### OpenAI API errors
- Check API key is set correctly
- Verify gpt-5-nano model is available in your account
- Check rate limits

### Database locked
- Only one process should write at a time
- If stuck, delete old database: `rm ~/.remind/reminders.db`

## Performance Considerations

- **Database queries**: Use indexed searches (id, due_at)
- **Notification spam**: Respect user timezone + nudge intervals
- **OpenAI calls**: Cache responses if possible, track costs
- **Scheduler loop**: 1 minute interval is reasonable, don't go below 30s

## Security Notes

- **License tokens**: Treat as secrets, don't commit
- **API keys**: Encourage env var or encrypted config
- **Database**: SQLite is file-based, ensure proper permissions (~/.remind/)
- **No remote calls**: License verification is local-only

---

**Last updated**: 2025-01-30 | Version: 0.1.0

"""Pytest configuration and fixtures."""

import platform
from pathlib import Path

import pytest

from remind.db import Database


@pytest.fixture
def test_db():
    """Provide an in-memory test database."""
    db = Database(db_path=Path(":memory:"))
    yield db
    db.close()


# Platform-specific fixtures


@pytest.fixture
def skip_if_windows():
    """Skip test on Windows."""
    if platform.system() == "Windows":
        pytest.skip("Not supported on Windows")


@pytest.fixture
def skip_if_not_macos():
    """Skip test if not on macOS."""
    if platform.system() != "Darwin":
        pytest.skip("macOS only test")


@pytest.fixture
def skip_if_not_linux():
    """Skip test if not on Linux."""
    if platform.system() != "Linux":
        pytest.skip("Linux only test")


@pytest.fixture
def skip_if_no_notifications():
    """Skip test if notifications not available."""
    from remind.platform_capabilities import PlatformCapabilities

    if not PlatformCapabilities.test_notifications():
        pytest.skip("Notifications not available on this system")


@pytest.fixture
def skip_if_no_sound():
    """Skip test if sound playback not available."""
    from remind.platform_capabilities import PlatformCapabilities
    from remind.platform_utils import get_platform

    platform_info = get_platform()
    if not PlatformCapabilities.test_sound_player(platform_info.get_sound_player()):
        pytest.skip("Sound player not available on this system")


@pytest.fixture
def skip_if_no_systemd():
    """Skip test if systemd not available (Linux)."""
    from remind.platform_capabilities import PlatformCapabilities

    if not PlatformCapabilities.test_systemd():
        pytest.skip("systemd not available on this system")


@pytest.fixture
def skip_if_no_launchctl():
    """Skip test if launchctl not available (macOS)."""
    from remind.platform_capabilities import PlatformCapabilities

    if not PlatformCapabilities.test_launchctl():
        pytest.skip("launchctl not available on this system")

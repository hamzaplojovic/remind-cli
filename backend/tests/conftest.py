"""Pytest configuration for backend tests."""

import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set up environment variables for tests."""
    os.environ["REMIND_OPENAI_API_KEY"] = "sk-test-key"
    os.environ["REMIND_DATABASE_URL"] = "sqlite:///:memory:"

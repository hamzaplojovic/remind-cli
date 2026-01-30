"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest

from remind.db import Database


@pytest.fixture
def test_db():
    """Provide an in-memory test database."""
    db = Database(db_path=Path(":memory:"))
    yield db
    db.close()

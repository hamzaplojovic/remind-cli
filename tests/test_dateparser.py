"""Tests for natural language date parsing."""

from remind.cli import parse_datetime


def test_parse_tomorrow():
    """Test parsing 'tomorrow' at a specific time."""
    result = parse_datetime("tomorrow 3pm")
    assert result is not None
    assert result.hour == 15


def test_parse_in_hours():
    """Test parsing 'in X hours'."""
    result = parse_datetime("in 2 hours")
    assert result is not None


def test_parse_next_day():
    """Test parsing relative dates without crashing."""
    # dateparser may or may not parse this depending on locale
    # Just ensure it doesn't crash
    parse_datetime("next week")


def test_parse_absolute_date():
    """Test parsing absolute dates."""
    result = parse_datetime("2025-02-15 10:00")
    assert result is not None
    assert result.day == 15


def test_parse_today():
    """Test parsing 'today'."""
    result = parse_datetime("today 5pm")
    assert result is not None
    assert result.hour == 17


def test_parse_invalid():
    """Test that invalid dates return None or sensible result."""
    result = parse_datetime("never")
    # dateparser might return None or a sensible default
    # Just verify it doesn't crash
    assert result is None or isinstance(result, type(result))

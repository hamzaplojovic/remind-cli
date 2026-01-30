"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_health_check():
    """Test health check endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("backend.main.authenticate_token")
@patch("backend.main.check_rate_limit")
@patch("backend.main.get_db")
def test_suggest_reminder_invalid_token(mock_get_db, mock_rate_limit, mock_auth):
    """Test suggestion endpoint with invalid token."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.auth import AuthError

    mock_auth.side_effect = AuthError("Invalid license token")

    client = TestClient(app)
    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "invalid_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 401
    assert "Invalid license" in response.json()["detail"]


@patch("backend.main.log_usage")
@patch("backend.main.increment_rate_limit")
@patch("backend.main.check_ai_quota")
@patch("backend.main.suggest_reminder")
@patch("backend.main.check_rate_limit")
@patch("backend.main.authenticate_token")
@patch("backend.main.get_db")
def test_suggest_reminder_valid(
    mock_get_db,
    mock_auth,
    mock_rate_limit,
    mock_suggest,
    mock_quota,
    mock_increment,
    mock_log,
):
    """Test suggestion endpoint with valid token."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.models import PriorityLevel
    from unittest.mock import MagicMock

    # Create mock user
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.plan_tier = "pro"
    mock_auth.return_value = mock_user
    mock_rate_limit.return_value = 9
    mock_get_db.return_value = MagicMock()

    # Mock AI response
    mock_suggest.return_value = {
        "suggested_text": "Call mom",
        "priority": PriorityLevel.HIGH,
        "due_time_suggestion": "tomorrow 3pm",
        "cost_cents": 1,
        "input_tokens": 20,
        "output_tokens": 10,
    }

    client = TestClient(app)
    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "test_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["suggested_text"] == "Call mom"
    assert data["priority"] == "high"
    assert data["cost_cents"] == 1


@patch("backend.main.check_ai_quota")
@patch("backend.main.check_rate_limit")
@patch("backend.main.authenticate_token")
@patch("backend.main.get_db")
def test_suggest_reminder_quota_exceeded(mock_get_db, mock_auth, mock_rate_limit, mock_quota):
    """Test suggestion endpoint with exhausted quota."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.auth import QuotaError
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.id = 1
    mock_auth.return_value = mock_user
    mock_rate_limit.return_value = 9
    mock_quota.side_effect = QuotaError("Monthly AI quota exhausted")
    mock_get_db.return_value = MagicMock()

    client = TestClient(app)
    response = client.post(
        "/api/v1/suggest-reminder",
        json={
            "license_token": "test_token",
            "reminder_text": "call mom",
        },
    )
    assert response.status_code == 429
    assert "quota exhausted" in response.json()["detail"]


@patch("backend.main.authenticate_token")
@patch("backend.main.get_db")
def test_usage_stats_invalid_token(mock_get_db, mock_auth):
    """Test usage stats endpoint with invalid token."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from backend.auth import AuthError

    mock_auth.side_effect = AuthError("Invalid license token")
    mock_get_db.return_value = MagicMock()

    client = TestClient(app)
    response = client.get("/api/v1/usage-stats?license_token=invalid_token")
    assert response.status_code == 401
    assert "Invalid license" in response.json()["detail"]


@patch("backend.main.get_usage_stats")
@patch("backend.main.authenticate_token")
@patch("backend.main.get_db")
def test_usage_stats_valid(mock_get_db, mock_auth, mock_stats):
    """Test usage stats endpoint with valid token."""
    from fastapi.testclient import TestClient
    from backend.main import app
    from unittest.mock import MagicMock

    mock_user = MagicMock()
    mock_user.id = 1
    mock_auth.return_value = mock_user
    mock_get_db.return_value = MagicMock()
    mock_stats.return_value = {
        "user_id": 1,
        "plan_tier": "pro",
        "ai_quota_used": 0,
        "ai_quota_total": 1000,
        "ai_quota_remaining": 1000,
        "this_month_cost_cents": 0,
        "rate_limit_remaining": 10,
        "rate_limit_reset_at": "2025-01-30T12:05:00Z",
    }

    client = TestClient(app)
    response = client.get("/api/v1/usage-stats?license_token=test_token")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert data["plan_tier"] == "pro"
    assert data["ai_quota_total"] == 1000

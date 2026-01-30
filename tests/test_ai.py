"""Tests for AI module (backend API)."""

from unittest.mock import MagicMock, patch

from remind.ai import AIManager, get_ai_manager
from remind.models import AIResponse, PriorityLevel


def test_ai_manager_initialization():
    """Test AI manager can be initialized with backend URL."""
    manager = AIManager(backend_url="http://localhost:8000", license_token="test_token")
    assert manager is not None
    assert manager.backend_url == "http://localhost:8000"
    assert manager.license_token == "test_token"


@patch("remind.ai.httpx.Client")
def test_suggest_rephrasing_response_parsing(mock_client_class):
    """Test parsing backend API response."""
    # Mock httpx client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "suggested_text": "Call mom",
        "priority": "high",
        "due_time_suggestion": "tomorrow 3pm",
        "cost_cents": 1,
    }

    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value = mock_client

    manager = AIManager(backend_url="http://localhost:8000", license_token="test_token")

    # Bypass premium check
    with patch("remind.premium.get_license_manager") as mock_lic:
        mock_mgr = MagicMock()
        mock_mgr.has_license.return_value = True
        mock_lic.return_value = mock_mgr

        response = manager.suggest_rephrasing("call mom pls")

    assert isinstance(response, AIResponse)
    assert response.suggested_text == "Call mom"
    assert response.priority == PriorityLevel.HIGH
    assert response.due_time_suggestion == "tomorrow 3pm"
    assert response.cost_estimate == 0.01  # 1 cent


def test_get_ai_manager_without_params():
    """Test get_ai_manager returns None without params."""
    manager = get_ai_manager()
    assert manager is None


def test_get_ai_manager_with_params():
    """Test get_ai_manager returns manager with backend URL and token."""
    manager = get_ai_manager(
        backend_url="http://localhost:8000", license_token="test_token"
    )
    assert manager is not None
    assert isinstance(manager, AIManager)

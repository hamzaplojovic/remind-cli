"""Tests for AI suggestion module."""

from unittest.mock import patch, MagicMock
import pytest

from backend.ai import calculate_cost, suggest_reminder
from backend.models import PriorityLevel


def test_calculate_cost():
    """Test cost calculation for tokens."""
    # GPT-5-nano: $0.0000375 per 1K input, $0.00015 per 1K output
    # 100 input tokens: $0.00375 * 100 = $0.000375 = 0.375 cents
    # 50 output tokens: $0.0075 * 50 = $0.000375 = 0.375 cents
    # Total: 0.75 cents, rounded to 1 cent minimum
    cost = calculate_cost(100, 50)
    assert cost >= 1  # Minimum 1 cent


def test_calculate_cost_large_tokens():
    """Test cost calculation with large token counts."""
    cost = calculate_cost(10000, 5000)
    assert cost >= 1  # Should be at least 1 cent even for small costs


def test_suggest_reminder_invalid_response():
    """Test handling of invalid AI response."""
    with patch("backend.ai.openai.OpenAI") as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "invalid json"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5

        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(ValueError, match="parse AI response"):
            suggest_reminder("test reminder")


@patch("backend.ai.openai.OpenAI")
@patch("backend.ai.get_settings")
def test_suggest_reminder_success(mock_settings, mock_openai_class):
    """Test successful AI suggestion."""
    # Mock settings
    mock_settings_obj = MagicMock()
    mock_settings_obj.openai_api_key = "test_key"
    mock_settings_obj.openai_model = "gpt-5-nano"
    mock_settings.return_value = mock_settings_obj

    # Mock API response
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"suggested_text": "Call mom tomorrow", "priority": "high", "due_time_suggestion": "tomorrow 3pm"}'
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 20

    mock_client.chat.completions.create.return_value = mock_response

    result = suggest_reminder("call mom")

    assert result["suggested_text"] == "Call mom tomorrow"
    assert result["priority"] == PriorityLevel.HIGH
    assert result["due_time_suggestion"] == "tomorrow 3pm"
    assert result["cost_cents"] >= 1
    assert result["input_tokens"] == 50
    assert result["output_tokens"] == 20


@patch("backend.ai.openai.OpenAI")
@patch("backend.ai.get_settings")
def test_suggest_reminder_with_null_due_time(mock_settings, mock_openai_class):
    """Test AI suggestion with null due time."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.openai_api_key = "test_key"
    mock_settings_obj.openai_model = "gpt-5-nano"
    mock_settings.return_value = mock_settings_obj

    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices[0].message.content = '{"suggested_text": "Buy milk", "priority": "medium", "due_time_suggestion": null}'
    mock_response.usage.prompt_tokens = 40
    mock_response.usage.completion_tokens = 15

    mock_client.chat.completions.create.return_value = mock_response

    result = suggest_reminder("buy milk")

    assert result["suggested_text"] == "Buy milk"
    assert result["priority"] == PriorityLevel.MEDIUM
    assert result["due_time_suggestion"] is None

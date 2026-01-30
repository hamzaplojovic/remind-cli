"""Tests for Paddle payment integration."""

import hmac
import json
from unittest.mock import patch


def test_verify_paddle_webhook_valid():
    """Test Paddle webhook signature verification."""
    from app.paddle import verify_paddle_webhook

    secret = "test_secret"
    body = b'{"test": "data"}'
    signature = hmac.new(secret.encode(), body, "sha256").hexdigest()

    with patch("app.paddle.get_settings") as mock_settings:
        mock_settings.return_value.paddle_webhook_secret = secret
        assert verify_paddle_webhook(body, signature) is True


def test_verify_paddle_webhook_invalid():
    """Test Paddle webhook verification fails with bad signature."""
    from app.paddle import verify_paddle_webhook

    secret = "test_secret"
    body = b'{"test": "data"}'
    bad_signature = "invalid_signature"

    with patch("app.paddle.get_settings") as mock_settings:
        mock_settings.return_value.paddle_webhook_secret = secret
        assert verify_paddle_webhook(body, bad_signature) is False


def test_get_plan_tier_from_paddle_product():
    """Test mapping Paddle product IDs to plan tiers."""
    from app.paddle import get_plan_tier_from_paddle_product

    # No mapping by default
    assert get_plan_tier_from_paddle_product("unknown_product") is None


def test_handle_subscription_created():
    """Test handling subscription.created event."""
    from app.paddle import handle_subscription_created

    event_data = {
        "data": {
            "attributes": {
                "customer_email": "user@example.com",
                "product_id": "pro_product_123",
            }
        }
    }

    with patch("app.paddle.get_plan_tier_from_paddle_product") as mock_tier:
        mock_tier.return_value = "pro"
        result = handle_subscription_created(event_data)

    assert result == ("user@example.com", "pro")


def test_handle_subscription_created_missing_email():
    """Test subscription event with missing email."""
    from app.paddle import handle_subscription_created

    event_data = {
        "data": {
            "attributes": {
                "product_id": "pro_product_123",
            }
        }
    }

    result = handle_subscription_created(event_data)
    assert result is None


def test_handle_transaction_completed():
    """Test handling transaction.completed event."""
    from app.paddle import handle_transaction_completed

    event_data = {
        "data": {
            "attributes": {
                "customer_email": "user@example.com",
                "product_id": "team_product_456",
            }
        }
    }

    with patch("app.paddle.get_plan_tier_from_paddle_product") as mock_tier:
        mock_tier.return_value = "team"
        result = handle_transaction_completed(event_data)

    assert result == ("user@example.com", "team")


def test_create_license_token():
    """Test license token generation."""
    from app.paddle import create_license_token

    token = create_license_token("pro", "user@example.com")

    assert token.startswith("remind_pro_")
    assert len(token) == len("remind_pro_") + 24  # 24 char hex suffix


def test_create_license_token_format():
    """Test that tokens are consistent format."""
    from app.paddle import create_license_token

    token1 = create_license_token("indie", "user@example.com")
    token2 = create_license_token("indie", "user@example.com")

    # Tokens should be different (random)
    assert token1 != token2
    assert token1.startswith("remind_indie_")
    assert token2.startswith("remind_indie_")


def test_webhook_bad_signature():
    """Test webhook rejects bad signature."""
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)

    body = json.dumps({"test": "data"}).encode()

    with patch("backend.main.verify_paddle_webhook") as mock_verify:
        mock_verify.return_value = False
        response = client.post(
            "/webhooks/paddle",
            content=body,
            headers={"X-Paddle-Signature": "bad_signature"},
        )

    assert response.status_code == 401

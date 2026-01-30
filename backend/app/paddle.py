"""Paddle payment integration for license issuing."""

import hmac
import json
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import UserModel


# Paddle plan tier mapping (product IDs to plan tiers)
PADDLE_PRODUCT_MAPPING = {
    # Set these in environment or update after creating products in Paddle
    # Format: "paddle_product_id": "plan_tier"
}


def verify_paddle_webhook(raw_body: bytes, signature: str) -> bool:
    """Verify Paddle webhook signature.

    Paddle sends X-Paddle-Signature header with SHA256 HMAC of the body.
    """
    settings = get_settings()
    if not settings.paddle_webhook_secret:
        return False

    expected = hmac.new(
        settings.paddle_webhook_secret.encode(),
        raw_body,
        "sha256"
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def get_plan_tier_from_paddle_product(product_id: str) -> Optional[str]:
    """Map Paddle product ID to plan tier.

    Return None if product is not recognized (e.g., free tier).
    """
    # Check environment mapping first
    paddle_map = PADDLE_PRODUCT_MAPPING
    if product_id in paddle_map:
        return paddle_map[product_id]

    # Fallback: return None (free tier)
    return None


def handle_subscription_created(event_data: dict) -> Optional[tuple[str, str]]:
    """Handle Paddle subscription.created webhook.

    Returns (email, license_token) tuple if successful, None otherwise.
    """
    try:
        subscription = event_data.get("data", {}).get("attributes", {})
        customer_email = subscription.get("customer_email")
        product_id = subscription.get("product_id")

        if not customer_email or not product_id:
            return None

        plan_tier = get_plan_tier_from_paddle_product(product_id)
        if not plan_tier:
            # Free tier or unrecognized product
            return None

        # This would be called by the webhook handler which passes db session
        # We return the data and let main.py handle DB insertion
        return (customer_email, plan_tier)

    except (KeyError, TypeError, ValueError):
        return None


def handle_transaction_completed(event_data: dict) -> Optional[tuple[str, str]]:
    """Handle Paddle transaction.completed webhook (for one-time purchases).

    Returns (email, license_token) tuple if successful, None otherwise.
    """
    try:
        transaction = event_data.get("data", {}).get("attributes", {})
        customer_email = transaction.get("customer_email")
        product_id = transaction.get("product_id")

        if not customer_email or not product_id:
            return None

        plan_tier = get_plan_tier_from_paddle_product(product_id)
        if not plan_tier:
            return None

        return (customer_email, plan_tier)

    except (KeyError, TypeError, ValueError):
        return None


def create_license_token(
    plan_tier: str,
    email: str,
    expires_at: Optional[datetime] = None,
) -> str:
    """Generate a license token for a Paddle purchase.

    Token format: remind_{tier}_{random_hex}
    """
    import secrets
    import hashlib

    random_suffix = secrets.token_hex(12)  # 24 char hex
    token = f"remind_{plan_tier}_{random_suffix}"

    return token


def generate_paddle_products_config() -> dict:
    """Generate the environment variable setup needed for Paddle products.

    Call this after creating products in Paddle dashboard to get the mapping.
    """
    return {
        "REMIND_PADDLE_PRODUCT_INDIE": "paddle_product_id_here",
        "REMIND_PADDLE_PRODUCT_PRO": "paddle_product_id_here",
        "REMIND_PADDLE_PRODUCT_TEAM": "paddle_product_id_here",
    }

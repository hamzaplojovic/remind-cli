"""AI-powered features for Remind via backend API."""

import httpx

from remind.models import AIResponse
from remind.premium import requires_premium
from remind.utils import parse_priority


class AIManager:
    """Manages AI-powered features via backend API."""

    def __init__(self, backend_url: str, license_token: str):
        """Initialize AI manager with backend URL and license token."""
        self.backend_url = backend_url.rstrip("/")
        self.license_token = license_token
        self.client = httpx.Client(timeout=30.0)

    @requires_premium
    def suggest_rephrasing(self, text: str) -> AIResponse:
        """
        Get AI suggestions for reminder text via backend API.

        Args:
            text: Original reminder text

        Returns:
            AIResponse with suggestions
        """
        try:
            response = self.client.post(
                f"{self.backend_url}/api/v1/suggest-reminder",
                json={"license_token": self.license_token, "reminder_text": text},
            )

            if response.status_code == 401:
                raise ValueError("Invalid or expired license token")
            elif response.status_code == 429:
                raise ValueError(response.json().get("detail", "Rate limited or quota exceeded"))
            elif response.status_code != 200:
                raise ValueError(f"Backend error: {response.status_code} - {response.text}")

            data = response.json()

            # Parse backend response
            priority_str = data.get("priority", "medium")
            priority = parse_priority(priority_str)

            cost_cents = data.get("cost_cents", 0)
            cost_estimate = cost_cents / 100.0  # Convert cents to dollars

            return AIResponse(
                suggested_text=data.get("suggested_text", text),
                priority=priority,
                due_time_suggestion=data.get("due_time_suggestion"),
                cost_estimate=cost_estimate,
            )

        except httpx.HTTPError as e:
            raise RuntimeError(f"Backend API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Error calling backend API: {e}")

    def close(self):
        """Close the HTTP client."""
        self.client.close()


def get_ai_manager(
    backend_url: str | None = None, license_token: str | None = None
) -> AIManager | None:
    """Get AI manager instance configured for backend API."""
    if not backend_url or not license_token:
        return None
    try:
        return AIManager(backend_url, license_token)
    except Exception:
        return None

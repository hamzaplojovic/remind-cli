"""AI integration with OpenAI."""

import json
from typing import TypedDict

import openai
from app.config import get_settings
from app.models import PriorityLevel


class AIResponse(TypedDict):
    """AI suggestion response."""

    suggested_text: str
    priority: PriorityLevel
    due_time_suggestion: str | None
    cost_cents: int
    input_tokens: int
    output_tokens: int


def calculate_cost(input_tokens: int, output_tokens: int) -> int:
    """Calculate cost in cents for GPT-5-nano.

    GPT-5-nano pricing (as of 2025):
    - Input: $0.0000375 per 1K tokens
    - Output: $0.00015 per 1K tokens
    """
    input_cost = (input_tokens / 1000) * 0.0000375
    output_cost = (output_tokens / 1000) * 0.00015
    total_cents = int((input_cost + output_cost) * 100)
    return max(1, total_cents)  # Minimum 1 cent per request


def suggest_reminder(reminder_text: str) -> AIResponse:
    """Get AI suggestion for reminder text.

    Uses OpenAI GPT-5-nano to suggest:
    - Improved/cleaner reminder text
    - Priority level (low/medium/high)
    - Due time suggestion if detectable
    """
    settings = get_settings()
    client = openai.OpenAI(api_key=settings.openai_api_key)

    prompt = f"""You are a helpful reminder assistant. The user has entered a reminder: "{reminder_text}"

Your task:
1. Rephrase it to be clear and concise
2. Determine priority (low, medium, high) based on urgency/importance
3. If a time is mentioned, extract due_time_suggestion, otherwise null

Respond ONLY with valid JSON (no markdown, no backticks):
{{
  "suggested_text": "Clear rephrased reminder",
  "priority": "low|medium|high",
  "due_time_suggestion": "time or null"
}}"""

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    # Parse response
    try:
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from AI")
        data = json.loads(content.strip())
    except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
        raise ValueError(f"Failed to parse AI response: {e}")

    # Extract token usage
    if not response.usage:
        raise ValueError("No usage data in response")
    input_tokens = response.usage.prompt_tokens or 0
    output_tokens = response.usage.completion_tokens or 0
    cost_cents = calculate_cost(input_tokens, output_tokens)

    return AIResponse(
        suggested_text=data.get("suggested_text", reminder_text),
        priority=PriorityLevel(data.get("priority", "medium")),
        due_time_suggestion=data.get("due_time_suggestion"),
        cost_cents=cost_cents,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

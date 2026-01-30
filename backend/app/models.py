"""Pydantic models for API requests and responses."""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class PlanTier(str, Enum):
    """Available pricing plans."""

    FREE = "free"
    INDIE = "indie"
    PRO = "pro"
    TEAM = "team"


# Plan configuration: quota and cost
PLAN_CONFIGS = {
    PlanTier.FREE: {"monthly_quota": 5, "cost_per_suggestion_cents": 0},
    PlanTier.INDIE: {"monthly_quota": 100, "cost_per_suggestion_cents": 0},
    PlanTier.PRO: {"monthly_quota": 1000, "cost_per_suggestion_cents": 0},
    PlanTier.TEAM: {"monthly_quota": 5000, "cost_per_suggestion_cents": 0},
}


class SuggestReminderRequest(BaseModel):
    """Request to suggest a reminder text."""

    model_config = ConfigDict(str_strip_whitespace=True)

    license_token: str
    reminder_text: str


class PriorityLevel(str, Enum):
    """Reminder priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SuggestReminderResponse(BaseModel):
    """Response with suggested reminder."""

    model_config = ConfigDict(str_strip_whitespace=True)

    suggested_text: str
    priority: PriorityLevel
    due_time_suggestion: str | None = None
    cost_cents: int


class UsageStats(BaseModel):
    """User usage statistics for billing."""

    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: int
    plan_tier: PlanTier
    ai_quota_used: int
    ai_quota_total: int
    ai_quota_remaining: int
    this_month_cost_cents: int
    rate_limit_remaining: int
    rate_limit_reset_at: str


class ErrorResponse(BaseModel):
    """Error response."""

    model_config = ConfigDict(str_strip_whitespace=True)

    detail: str

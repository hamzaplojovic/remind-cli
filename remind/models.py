"""Data models for Remind."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PriorityLevel(str, Enum):
    """Priority levels for reminders."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReminderBase(BaseModel):
    """Base reminder model."""

    text: str = Field(..., min_length=1, max_length=1000)
    due_at: datetime
    priority: PriorityLevel = PriorityLevel.MEDIUM
    project_context: str | None = None
    ai_suggested_text: str | None = None


class Reminder(ReminderBase):
    """Reminder with database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    done_at: datetime | None = None


class AIResponse(BaseModel):
    """AI rephrasing response from OpenAI."""

    suggested_text: str = Field(..., min_length=1)
    priority: PriorityLevel
    due_time_suggestion: str | None = None
    cost_estimate: float | None = None


class License(BaseModel):
    """License token model."""

    token: str = Field(..., min_length=10)
    created_at: datetime
    email: str | None = None


class Config(BaseModel):
    """User configuration."""

    model_config = ConfigDict(validate_assignment=True)

    timezone: str = "UTC"
    scheduler_interval_minutes: int = Field(default=1, ge=1, le=60)
    notifications_enabled: bool = True
    notification_sound_enabled: bool = True
    ai_rephrasing_enabled: bool = True
    ai_backend_url: str | None = None  # Backend API URL for AI suggestions
    openai_api_key: str | None = None  # OpenAI API key (for local usage)
    nudge_intervals_minutes: list[int] = Field(default_factory=lambda: [5, 15, 60])

"""Authentication and authorization logic."""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.database import UserModel, RateLimitModel, UsageLogModel
from app.models import PlanTier, PLAN_CONFIGS


class AuthError(HTTPException):
    """Authentication error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class QuotaError(HTTPException):
    """Quota exceeded error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


def authenticate_token(db: Session, token: str) -> UserModel:
    """Validate license token and return user.

    Raises AuthError if token is invalid or inactive.
    """
    user = db.query(UserModel).filter(UserModel.token == token).first()

    if not user:
        raise AuthError("Invalid license token")

    if not user.active:
        raise AuthError("License is inactive")

    if user.expires_at:
        # Ensure timezone-aware comparison
        expires = user.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise AuthError("License has expired")

    return user


def check_rate_limit(db: Session, user_id: int) -> int:
    """Check rate limit for user.

    Returns remaining requests in this window.
    Raises QuotaError if rate limit exceeded.
    """
    from app.config import get_settings
    settings = get_settings()

    rate_limit = db.query(RateLimitModel).filter(RateLimitModel.user_id == user_id).first()
    now = datetime.now(timezone.utc)

    # If no rate limit record or window has passed, reset it
    should_reset = not rate_limit
    if rate_limit:
        reset_at = rate_limit.reset_at
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        should_reset = now > reset_at

    if should_reset:
        if not rate_limit:
            rate_limit = RateLimitModel(
                user_id=user_id,
                request_count=0,
                reset_at=now + timedelta(seconds=settings.rate_limit_window_seconds)
            )
            db.add(rate_limit)
        else:
            rate_limit.request_count = 0
            rate_limit.reset_at = now + timedelta(seconds=settings.rate_limit_window_seconds)
        db.commit()

    # Check if limit exceeded
    if rate_limit.request_count >= settings.rate_limit_requests:
        raise QuotaError(
            f"Rate limit exceeded. Maximum {settings.rate_limit_requests} requests per "
            f"{settings.rate_limit_window_seconds} seconds"
        )

    remaining = settings.rate_limit_requests - rate_limit.request_count - 1
    return remaining


def get_monthly_quota_used(db: Session, user_id: int) -> int:
    """Get AI suggestions used this month."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count = db.query(UsageLogModel).filter(
        UsageLogModel.user_id == user_id,
        UsageLogModel.feature == "ai_suggestion",
        UsageLogModel.timestamp >= month_start
    ).count()

    return count


def check_ai_quota(db: Session, user: UserModel) -> None:
    """Check if user has remaining AI suggestion quota.

    Raises QuotaError if quota exceeded.
    """
    plan_config = PLAN_CONFIGS[PlanTier(user.plan_tier)]
    monthly_quota = plan_config["monthly_quota"]

    used = get_monthly_quota_used(db, user.id)

    if used >= monthly_quota:
        raise QuotaError(f"Monthly AI quota exhausted. Used {used}/{monthly_quota}")


def log_usage(db: Session, user_id: int, input_tokens: int, output_tokens: int, cost_cents: int) -> None:
    """Log feature usage for billing."""
    log = UsageLogModel(
        user_id=user_id,
        feature="ai_suggestion",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_cents=cost_cents,
    )
    db.add(log)
    db.commit()


def increment_rate_limit(db: Session, user_id: int) -> None:
    """Increment rate limit counter."""
    rate_limit = db.query(RateLimitModel).filter(RateLimitModel.user_id == user_id).first()
    if rate_limit:
        rate_limit.request_count += 1
        db.commit()


def get_usage_stats(db: Session, user: UserModel) -> dict:
    """Calculate usage statistics for user."""
    plan_tier = PlanTier(user.plan_tier)
    plan_config = PLAN_CONFIGS[plan_tier]

    # Monthly quota stats
    ai_quota_used = get_monthly_quota_used(db, user.id)
    ai_quota_total = plan_config["monthly_quota"]
    ai_quota_remaining = max(0, ai_quota_total - ai_quota_used)

    # Cost this month
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_cost = db.query(UsageLogModel).filter(
        UsageLogModel.user_id == user.id,
        UsageLogModel.timestamp >= month_start
    ).with_entities(UsageLogModel.cost_cents).all()

    this_month_cost_cents = sum(row[0] for row in total_cost)

    # Rate limit stats
    rate_limit = db.query(RateLimitModel).filter(RateLimitModel.user_id == user.id).first()
    if rate_limit:
        from app.config import get_settings
        settings = get_settings()
        rate_limit_remaining = max(0, settings.rate_limit_requests - rate_limit.request_count)
        rate_limit_reset_at = rate_limit.reset_at.isoformat()
    else:
        from app.config import get_settings
        settings = get_settings()
        rate_limit_remaining = settings.rate_limit_requests
        rate_limit_reset_at = (datetime.now(timezone.utc) + timedelta(seconds=settings.rate_limit_window_seconds)).isoformat()

    return {
        "user_id": user.id,
        "plan_tier": plan_tier.value,
        "ai_quota_used": ai_quota_used,
        "ai_quota_total": ai_quota_total,
        "ai_quota_remaining": ai_quota_remaining,
        "this_month_cost_cents": this_month_cost_cents,
        "rate_limit_remaining": rate_limit_remaining,
        "rate_limit_reset_at": rate_limit_reset_at,
    }

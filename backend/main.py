"""FastAPI backend server for Remind."""

from app.ai import suggest_reminder
from app.auth import (
    authenticate_token,
    check_ai_quota,
    check_rate_limit,
    get_usage_stats,
    increment_rate_limit,
    log_usage,
)
from app.database import UserModel, get_db, init_db
from app.email import send_license_email
from app.models import (
    SuggestReminderRequest,
    SuggestReminderResponse,
    UsageStats,
)
from app.paddle import (
    create_license_token,
    handle_subscription_created,
    handle_transaction_completed,
    verify_paddle_webhook,
)
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

app = FastAPI(title="Remind Backend", version="0.1.0")


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/webhooks/paddle")
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook handler for Paddle payment events.

    Handles:
    - subscription.created: New subscription purchase
    - transaction.completed: One-time purchase

    Generates license token and sends to customer email.
    """

    raw_body = await request.body()
    signature = request.headers.get("X-Paddle-Signature", "")

    # Verify webhook signature
    if not verify_paddle_webhook(raw_body, signature):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)

    # Parse JSON
    try:
        import json

        event_data = json.loads(raw_body)
    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    event_type = event_data.get("event_type")

    # Handle subscription purchases
    if event_type == "subscription.created":
        result = handle_subscription_created(event_data)
    elif event_type == "transaction.completed":
        result = handle_transaction_completed(event_data)
    else:
        return {"ok": True}  # Ignore other events

    if not result:
        return {"ok": True}

    email, plan_tier = result

    # Generate license token
    token = create_license_token(plan_tier, email)

    # Save to database
    user = UserModel(
        token=token,
        email=email,
        plan_tier=plan_tier,
        active=True,
    )
    db.add(user)
    db.commit()

    # Send email with license token
    send_license_email(email, token, plan_tier)

    return {"ok": True, "token": token}


@app.post("/api/v1/suggest-reminder", response_model=SuggestReminderResponse)
def api_suggest_reminder(
    request: SuggestReminderRequest,
    db: Session = Depends(get_db),
):
    """Suggest improved reminder text using AI.

    Request:
    ```json
    {
      "license_token": "remind_pro_xyz789",
      "reminder_text": "call mom tomorrow"
    }
    ```

    Response:
    ```json
    {
      "suggested_text": "Call mom tomorrow",
      "priority": "high",
      "due_time_suggestion": "tomorrow 3pm",
      "cost_cents": 1
    }
    ```

    Errors:
    - 401: Invalid or expired license
    - 429: Rate limit or quota exceeded
    """
    # Authenticate
    user = authenticate_token(db, request.license_token)

    # Check rate limit
    check_rate_limit(db, user.id)

    # Check AI quota
    check_ai_quota(db, user.id)

    # Increment rate limit
    increment_rate_limit(db, user.id)

    # Get AI suggestion
    ai_response = suggest_reminder(request.reminder_text)

    # Log usage
    log_usage(
        db,
        user.id,
        ai_response["input_tokens"],
        ai_response["output_tokens"],
        ai_response["cost_cents"],
    )

    return SuggestReminderResponse(
        suggested_text=ai_response["suggested_text"],
        priority=ai_response["priority"],
        due_time_suggestion=ai_response["due_time_suggestion"],
        cost_cents=ai_response["cost_cents"],
    )


@app.get("/api/v1/usage-stats", response_model=UsageStats)
def api_usage_stats(
    license_token: str,
    db: Session = Depends(get_db),
):
    """Get usage statistics for the user.

    Query parameters:
    - license_token: User's license token

    Response:
    ```json
    {
      "user_id": 42,
      "plan_tier": "pro",
      "ai_quota_used": 450,
      "ai_quota_total": 1000,
      "ai_quota_remaining": 550,
      "this_month_cost_cents": 400,
      "rate_limit_remaining": 7,
      "rate_limit_reset_at": "2025-01-30T12:05:00Z"
    }
    ```

    Errors:
    - 401: Invalid or expired license
    """
    user = authenticate_token(db, license_token)
    stats = get_usage_stats(db, user)
    return UsageStats(**stats)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper JSON response."""
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings

    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )

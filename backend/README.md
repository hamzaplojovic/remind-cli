# Remind Backend API

FastAPI-based backend server for the Remind CLI. Handles AI suggestions, usage tracking, and billing.

## Quick Start

### Prerequisites
- Python 3.13+
- OpenAI API key

### Installation

```bash
# From the main project root, install with backend dependencies
uv sync --all-extras

# Set up environment
cd backend
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running Locally

```bash
# From the backend directory
python -m backend
```

Server will start on `http://0.0.0.0:8000`

### Running Tests

```bash
# From the main project root
python -m pytest backend/tests/ -v
```

## Architecture

### Database Models

- **Users**: License token management and plan tiers
- **UsageLogs**: Feature usage tracking for billing
- **RateLimits**: Request rate limiting per user

### Endpoints

#### `POST /api/v1/suggest-reminder`

Suggests improved reminder text using OpenAI.

**Request:**
```json
{
  "license_token": "remind_pro_xyz789",
  "reminder_text": "call mom tomorrow"
}
```

**Response (200):**
```json
{
  "suggested_text": "Call mom tomorrow",
  "priority": "high",
  "due_time_suggestion": "tomorrow 3pm",
  "cost_cents": 1
}
```

**Errors:**
- `401`: Invalid or expired license
- `429`: Rate limit or quota exceeded

#### `GET /api/v1/usage-stats`

Get usage statistics for a user.

**Query Parameters:**
- `license_token`: User's license token

**Response (200):**
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

## Configuration

Environment variables (set in `.env`):

```
REMIND_OPENAI_API_KEY=sk-...          # Required: Your OpenAI API key
REMIND_OPENAI_MODEL=gpt-5-nano        # Default: gpt-5-nano
REMIND_DATABASE_URL=sqlite:///./backend.db  # Default: SQLite
REMIND_HOST=0.0.0.0                   # Default: 0.0.0.0
REMIND_PORT=8000                      # Default: 8000
REMIND_DEBUG=false                    # Default: false
REMIND_RATE_LIMIT_REQUESTS=10         # Default: 10 (per window)
REMIND_RATE_LIMIT_WINDOW_SECONDS=60   # Default: 60
```

## Pricing

Usage is tracked per plan tier:

- **FREE**: 5 AI suggestions/month
- **INDIE**: 100 AI suggestions/month
- **PRO**: 1000 AI suggestions/month
- **TEAM**: 5000 AI suggestions/month

## Deployment

### Heroku

```bash
git push heroku main
```

### Railway

Connect your GitHub repo to Railway and it will auto-deploy.

### Docker

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[backend]"
CMD ["python", "-m", "backend"]
```

```bash
docker build -t remind-backend .
docker run -e REMIND_OPENAI_API_KEY=sk-... remind-backend
```

### nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name api.remind.dev;

    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Testing

Run the full backend test suite:

```bash
python -m pytest backend/tests/ -v
```

Test categories:
- `test_auth.py`: Authentication, rate limiting, quotas (9 tests)
- `test_ai.py`: AI suggestion generation (5 tests)
- `test_api.py`: HTTP endpoints (6 tests)

## Development

### Code Structure

```
backend/
  __init__.py       # Package entry point
  __main__.py       # CLI entry point
  main.py           # FastAPI app and endpoints
  config.py         # Settings management
  database.py       # SQLAlchemy models
  models.py         # Pydantic schemas
  auth.py           # Authentication and authorization
  ai.py             # OpenAI integration
  tests/            # Test suite
  .env.example      # Environment template
  .env              # Local environment (git-ignored)
```

### Adding New Endpoints

1. Define request/response models in `models.py`
2. Add logic to `auth.py`, `ai.py`, or new module
3. Add endpoint to `main.py`
4. Write tests in `backend/tests/`

## Security

- API keys are never stored in binaries or git
- License tokens are validated on every request
- Rate limiting prevents brute force and abuse
- Usage quotas enforced per plan tier
- All communication should use HTTPS in production

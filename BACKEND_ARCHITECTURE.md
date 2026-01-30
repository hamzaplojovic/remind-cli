# Remind: Complete Architecture with Backend API

## Overview

Remind is now a **client-server architecture** where:
- **CLI** (client): Runs locally on user's machine, calls backend API for AI features
- **Backend API** (server): You self-host, manages OpenAI calls, billing, usage tracking
- **License tokens** include plan tier and usage quotas
- **No API keys in binaries** - backend uses your secret OpenAI key

## Pricing Tiers

```
FREE: $0/month
  - 5 AI suggestions/month
  - Core features: add, list, search, done

INDIE: $5/month
  - 100 AI suggestions/month
  - + nudges/escalations

PRO: $15/month
  - 1000 AI suggestions/month
  - + context tagging by Git repo
  - + analytics dashboard

TEAM: $50/month
  - 5000 AI suggestions/month
  - + all premium features
```

## System Architecture

```
┌──────────────────┐
│   CLI Client     │
│  (remind binary) │
│   ~/.remind/     │
│                  │
│  - Add reminder  │
│  - List reminders│
│  - Search       │
│  - Settings     │
│  - Call /api    │
└────────┬─────────┘
         │ HTTPS
         │ POST /api/v1/suggest-reminder
         │ {license_token, reminder_text}
         │
┌────────▼─────────────────────────────────┐
│         Backend API (FastAPI)             │
│        (You self-host this)               │
│                                           │
│  - Authenticate by license_token         │
│  - Check rate limits (10 req/min)        │
│  - Check AI quota (by plan)              │
│  - Call OpenAI with YOUR API KEY         │
│  - Log usage to database                 │
│  - Calculate cost (GPT-5-nano)           │
│  - Return suggestion + cost              │
│  - Track for billing                     │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
    ┌─────────────┐   ┌─────────────┐
    │  OpenAI API │   │  SQLite DB  │
    │ (your key)  │   │  (metrics)  │
    └─────────────┘   └─────────────┘
```

## CLI Configuration

User sets in `~/.remind/config.toml`:

```toml
[remind]
ai_backend_url = "https://your-api.example.com"
ai_rephrasing_enabled = true
```

## License Token Format

User receives token after payment (FREE/INDIE/PRO/TEAM):

```json
{
  "token": "remind_free_abc123xyz789",
  "email": "user@example.com",
  "created_at": "2025-01-30T12:00:00Z"
}
```

Stored in `~/.remind/license.json` (local - not sent anywhere else).

CLI passes token to backend for every AI request.

## Backend API Endpoints

### 1. Suggest Reminder

```
POST /api/v1/suggest-reminder

Request:
{
  "license_token": "remind_pro_xyz789",
  "reminder_text": "call mom before 3pm"
}

Response (200):
{
  "suggested_text": "Call mom before 3pm",
  "priority": "high",
  "due_time_suggestion": "today 3pm",
  "cost_cents": 1  // in cents
}

Response (401):
{"detail": "Invalid or expired license"}

Response (429):
{"detail": "Monthly AI quota exhausted. Used 1000/1000"}
```

### 2. Usage Stats

```
GET /api/v1/usage-stats?license_token=remind_pro_xyz789

Response:
{
  "user_id": 42,
  "plan_tier": "pro",
  "ai_quota_used": 450,
  "ai_quota_total": 1000,
  "ai_quota_remaining": 550,
  "this_month_cost_cents": 400,  // $4.00
  "rate_limit_remaining": 7,
  "rate_limit_reset_at": "2025-01-30T12:05:00Z"
}
```

## Backend Database Schema

### Users Table
```
- id (pk)
- token (unique)
- plan_tier (free/indie/pro/team)
- created_at
- expires_at (optional)
- active (bool)
```

### Usage Logs Table
```
- id (pk)
- user_id (fk)
- feature ("ai_suggestion", "nudge")
- timestamp
- input_tokens
- output_tokens
- cost_cents
- metadata (JSON)
```

### Rate Limits Table
```
- id (pk)
- user_id (unique)
- request_count
- reset_at
```

## Flow: User Adds Reminder with AI

1. User: `remind add "call mom tomorrow"`
2. CLI reads config → backend_url, license token
3. CLI calls `POST /api/v1/suggest-reminder`:
   - Send license token + reminder text
4. Backend:
   - ✓ Validate token & plan
   - ✓ Check rate limit (10/min)
   - ✓ Check quota (Pro has 1000/month)
   - ✓ Call OpenAI with YOUR key
   - ✓ Log to usage_logs table
   - ✓ Calculate cost (GPT-5-nano ≈ $0.0001/suggestion)
   - ✓ Return suggestions + cost
5. CLI receives:
   - Suggested text: "Call mom tomorrow"
   - Priority: "high"
   - Due time: "tomorrow 9am"
   - Cost: $0.0001 (charged against Pro tier)
6. CLI stores reminder locally in SQLite

## Deployment: How to Run Backend

### Prerequisites
- Python 3.13+
- OpenAI API key

### Setup

```bash
# Clone backend code
cd /remind-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Create .env
cp .env.example .env
# Edit .env with your OpenAI API key
REMIND_OPENAI_API_KEY=sk-...

# Initialize database
python -c "from remind_backend.database import init_db; init_db()"

# Run server
python -m remind_backend.main
```

Runs on `http://0.0.0.0:8000` by default.

### Production Deployment

Deploy on:
- Heroku: `git push heroku main`
- Railway: Connect GitHub repo
- Render: Build from `Dockerfile`
- Your own server: `gunicorn` + `nginx`

Example nginx config:
```
server {
    listen 443 ssl;
    server_name api.remind.dev;
    ssl_certificate /path/to/cert;
    ssl_certificate_key /path/to/key;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

## Security & Privacy

- ✅ **API keys never in binaries** - backend holds OpenAI key
- ✅ **Usage tracked locally** - dashboard shows user's own usage
- ✅ **Rate limiting** - 10 requests/minute per user
- ✅ **License tokens** - opaque, no JWT secrets needed
- ✅ **HTTPS only** - backend should use SSL/TLS
- ✅ **Quotas enforced** - prevents abuse

## Billing Model

Backend tracks usage in real-time:

```
- Each AI suggestion logs: input_tokens, output_tokens, cost_cents
- Monthly costs calculated from usage_logs table
- Users can see `/api/v1/usage-stats` to monitor spend
- You charge based on plan tier, not actual API cost
- You profit on difference between your rate and OpenAI's

Example:
- GPT-5-nano actual cost: ~$0.0001 per suggestion
- Pro tier charge: $15/month = 1000 suggestions
- Your margin: $15 - $0.10 (cost) = $14.90/user-month
```

## What's Included in MVP

✅ **CLI (v0.1.0)**
- 47 tests passing
- All commands working
- Backend API integration ready
- Config supports `ai_backend_url`

✅ **Backend API (v0.1.0)**
- FastAPI server
- Authentication by license token
- Rate limiting
- Quota enforcement
- Usage logging
- Cost calculation
- SQLite database

🚧 **To Build (v1.1+)**
- Web dashboard for users to manage tokens/billing
- Payment integration (Stripe/Paddle)
- Analytics export
- Admin panel
- User self-service signup
- Webhook notifications
- API docs/swagger UI
- Caching layer (Redis)

## Example Workflow

### 1. User Signs Up (Your Website)
```
User pays $15 for Pro tier
You generate license token: "remind_pro_abc123xyz789"
You email them the token & backend URL
```

### 2. User Configures CLI
```bash
remind settings --backend-url https://api.remind.dev
# Saves to ~/.remind/config.toml
```

### 3. User Adds Reminder with AI
```bash
remind add "call mom tmrw 3pm" --ai

# CLI calls: POST https://api.remind.dev/api/v1/suggest-reminder
# Response: "Call mom tomorrow 3pm" (high priority)
# Cost logged: 1 cent
```

### 4. User Checks Usage
```bash
remind settings --show-usage

# Output:
# Plan: Pro
# AI Quota: 450/1000 used
# This month cost: $0.45
# Rate limit: 7/10 requests remaining
```

## Next Steps

1. **Deploy backend** - Heroku, Railway, or self-hosted
2. **Create web dashboard** - Let users manage tokens
3. **Add Stripe integration** - Collect payments
4. **Market to devs** - "Pay-as-you-go AI reminders"
5. **Analytics** - Track usage by plan tier

---

**You now have:**
- ✅ Cross-platform CLI (macOS/Linux)
- ✅ Backend infrastructure with billing
- ✅ Secure API key management
- ✅ Real-time usage tracking
- ✅ Rate limiting & quotas
- ✅ No API keys in binaries

**Users get:**
- ✅ Free tier (5 AI suggestions/month)
- ✅ Paid tiers ($5, $15, $50/month)
- ✅ Local storage (privacy)
- ✅ Transparent costs
- ✅ Premium features on subscription

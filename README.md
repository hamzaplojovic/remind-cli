# Remind

🎯 **AI-powered CLI reminder and notification engine** for macOS and Linux with backend-powered AI suggestions and real-time billing.

## Features

### Core (Free)
- ⚡ **Instant capture**: `remind add "buy milk tomorrow 3pm"`
- 🔍 **Smart search**: Find reminders instantly
- ✓ **Mark complete**: Quick completion tracking
- 📋 **List & organize**: View all reminders
- 🎯 **Natural language**: Parse dates like "tomorrow", "in 2 hours"
- 🔔 **Native notifications**: Desktop alerts when reminders are due
- 💾 **Local storage**: SQLite database in `~/.remind/`

### Premium (Paid Plans)
- 🤖 **AI rephrasing**: Suggestions powered by GPT-5-nano
- 📊 **Smart nudges**: Escalating notifications until done
- 📈 **Analytics**: Weekly statistics
- 🏷️ **Context tagging**: Auto-organize by Git repo
- 🔌 **Plugin system**: Slack, calendar, email integration

## Pricing

```
FREE:  $0/mo  — 5 AI suggestions
INDIE: $5/mo  — 100 AI suggestions + nudges
PRO:   $15/mo — 1000 AI suggestions + analytics + context tagging
TEAM:  $50/mo — 5000 AI suggestions + all features
```

## Quick Start

```bash
# Add a reminder
remind add "Call mom tomorrow 3pm"

# List reminders
remind list

# Search
remind search "call"

# Mark done
remind done 1

# Settings
remind settings --show
```

## Installation

### macOS
```bash
brew install remind
```

### Linux & Manual
```bash
curl -fsSL https://install.remind.dev | bash
```

### From Source
```bash
git clone https://github.com/hamzaplojovic/remember.git
cd remember
python -m venv venv
source venv/bin/activate
pip install -e .
remind --help
```

## Architecture

**Remind uses a client-server architecture:**

- **CLI** (local): Stores reminders, sends AI requests to backend
- **Backend API** (self-hosted): Handles OpenAI calls with your API key, tracks usage, enforces quotas
- **License tokens** (local): Verify premium features without remote calls
- **SQLite** (local): All reminder data stored locally

See [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md) for complete technical details.

## Configuration

Edit `~/.remind/config.toml`:

```toml
[remind]
timezone = "US/Eastern"
scheduler_interval_minutes = 1
notifications_enabled = true
notification_sound_enabled = true
ai_rephrasing_enabled = true
ai_backend_url = "https://api.remind.dev"  # Your backend
nudge_intervals_minutes = [5, 15, 60]
```

## Premium Features

### AI Rephrasing
```bash
remind add "need 2 call mom b4 3pm" --ai
# AI suggests: "Call mom before 3pm"
# Priority: high
```

### Smart Nudges
Reminders escalate with sounds until you mark them done.

### Analytics
```bash
remind report
# Shows: completed, snoozed, cost this month
```

## License & Support

- 📖 [Full Documentation](https://github.com/hamzaplojovic/remember/wiki)
- 🐛 [Report Issues](https://github.com/hamzaplojovic/remember/issues)
- 💬 [Discussions](https://github.com/hamzaplojovic/remember/discussions)
- 💳 [Pricing & Plans](https://remind.dev)

MIT License. Built for developers.

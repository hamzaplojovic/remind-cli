#!/bin/bash
set -e

echo "🚀 Installing Remind Backend..."

# Detect OS and install Python 3.13 + uv if needed
if ! command -v python3.13 &> /dev/null; then
    echo "Installing Python 3.13..."
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y python3.13 python3.13-venv
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y python3.13
    elif [ "$(uname)" == "Darwin" ]; then
        brew install python@3.13
    fi
fi

if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Clone or update repo
if [ -d "remind-backend" ]; then
    cd remind-backend && git pull
else
    git clone https://github.com/hamzaplojovic/remind-backend.git
    cd remind-backend
fi

# Install dependencies
echo "Installing dependencies..."
uv sync

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
REMIND_OPENAI_API_KEY=
REMIND_PADDLE_API_KEY=
REMIND_PADDLE_WEBHOOK_SECRET=
REMIND_PADDLE_PRODUCT_INDIE=pro_01kg7eg0gjpd1dx72vx2pnmwrn
REMIND_PADDLE_PRODUCT_PRO=pro_01kg7ems0v9ewf5wsa047hph9e
REMIND_PADDLE_PRODUCT_TEAM=pro_01kg7enkqk4cdzcwrxy3xmwmem
REMIND_SMTP_USER=
REMIND_SMTP_PASSWORD=
REMIND_SMTP_FROM_EMAIL=
REMIND_OPENAI_MODEL=gpt-5-nano
REMIND_DATABASE_URL=sqlite:///./backend.db
REMIND_HOST=0.0.0.0
REMIND_PORT=8000
REMIND_DEBUG=false
REMIND_RATE_LIMIT_REQUESTS=10
REMIND_RATE_LIMIT_WINDOW_SECONDS=60
REMIND_SMTP_HOST=smtp.gmail.com
REMIND_SMTP_PORT=587
EOF
    echo "✅ Created .env file - please fill in your API keys"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start the server:"
echo "   uv run python main.py"
echo ""
echo "3. Server will run at http://localhost:8000"
echo ""
echo "📚 See .env.example for detailed configuration options"

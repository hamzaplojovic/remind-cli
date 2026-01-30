#!/bin/bash
set -e

echo "🚀 Installing Remind CLI..."

# Detect OS and install Python 3.13 + uv if needed
if ! command -v python3.13 &> /dev/null; then
    echo "📦 Installing Python 3.13..."
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y python3.13 python3.13-venv
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y python3.13
    elif [ "$(uname)" == "Darwin" ]; then
        brew install python@3.13
    else
        echo "❌ Unsupported OS. Please install Python 3.13 manually."
        exit 1
    fi
fi

if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone or update repo
REPO_DIR="${HOME}/remind-cli"
if [ -d "$REPO_DIR" ]; then
    echo "📥 Updating existing installation..."
    cd "$REPO_DIR"
    git pull
else
    echo "📥 Cloning repository..."
    git clone https://github.com/hamzaplojovic/remind-cli.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Install dependencies
echo "⚙️  Installing dependencies..."
uv sync

# Create config directory and file
CONFIG_DIR="${HOME}/.remind"
CONFIG_FILE="${CONFIG_DIR}/config.toml"

mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "📝 Creating config file..."
    cat > "$CONFIG_FILE" << 'EOF'
[remind]
timezone = "US/Eastern"
scheduler_interval_minutes = 1
notifications_enabled = true
notification_sound_enabled = true
ai_rephrasing_enabled = true
ai_backend_url = "https://remind-backend-production.up.railway.app"
nudge_intervals_minutes = [5, 15, 60]
EOF
    echo "✅ Created config at ~/.remind/config.toml"
fi

# Create symlink or alias for global access
echo "🔗 Setting up global command..."
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/remind" << 'EOF'
#!/bin/bash
cd "$HOME/remind-cli"
uv run remind "$@"
EOF
chmod +x "${BIN_DIR}/remind"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Quick start:"
echo "1. Add your first reminder:"
echo "   remind add 'call mom tomorrow'"
echo ""
echo "2. List reminders:"
echo "   remind list"
echo ""
echo "3. Edit config (optional):"
echo "   nano ~/.remind/config.toml"
echo ""
echo "💡 Make sure ~/.local/bin is in your PATH:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "Or add to your shell config (.bashrc/.zshrc):"
echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"

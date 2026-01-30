#!/bin/bash
# Installation script for Remind
# Usage: curl -fsSL https://install.remind.dev | bash

set -e

VERSION=${1:-"latest"}
OS=$(uname -s)
ARCH=$(uname -m)

# Map uname architectures to common names
case "$ARCH" in
  x86_64)
    ARCH="x86_64"
    ;;
  arm64|aarch64)
    ARCH="arm64"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

# Build the binary URL
BINARY_URL="https://github.com/yourusername/remind/releases/download/v${VERSION}/remind-${OS}-${ARCH}"

# Create install directory
INSTALL_DIR="${HOME}/.local/bin"
mkdir -p "$INSTALL_DIR"

# Download binary
echo "Downloading Remind ${VERSION} for ${OS}..."
curl -fL -o "${INSTALL_DIR}/remind" "$BINARY_URL"
chmod +x "${INSTALL_DIR}/remind"

# Add to PATH if not already there
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
  echo ""
  echo "Add the following line to your ~/.bashrc or ~/.zshrc:"
  echo "export PATH=\"\$PATH:${INSTALL_DIR}\""
fi

echo "✓ Remind installed successfully!"
echo ""
echo "Run 'remind --help' to get started."

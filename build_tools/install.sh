#!/bin/bash
# Remind CLI - Production-Grade Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/hamzaplojovic/remind-cli/master/build_tools/install.sh | bash
# Or: bash install.sh [VERSION]

set -e

# Configuration
REPO="hamzaplojovic/remind-cli"
INSTALL_DIR="${HOME}/.local/bin"
VERSION="${1:-latest}"
GITHUB_API="https://api.github.com/repos/${REPO}/releases"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
log_info() {
    echo -e "${BLUE}→${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
}

# Detect OS and architecture
detect_platform() {
    local os=$(uname -s)
    local arch=$(uname -m)

    case "$os" in
        Darwin)
            OS_NAME="macos"
            case "$arch" in
                arm64)
                    ARCH="arm64"
                    BINARY_NAME="remind-macos-arm64"
                    ;;
                x86_64)
                    ARCH="x86_64"
                    BINARY_NAME="remind-macos-x86_64"
                    ;;
                *)
                    log_error "Unsupported macOS architecture: $arch"
                    exit 1
                    ;;
            esac
            ;;
        Linux)
            OS_NAME="linux"
            case "$arch" in
                x86_64)
                    ARCH="x86_64"
                    BINARY_NAME="remind-linux-x86_64"
                    ;;
                aarch64)
                    ARCH="arm64"
                    BINARY_NAME="remind-linux-arm64"
                    ;;
                *)
                    log_error "Unsupported Linux architecture: $arch"
                    exit 1
                    ;;
            esac
            ;;
        *)
            log_error "Unsupported OS: $os (only macOS and Linux supported)"
            exit 1
            ;;
    esac

    log_info "Detected: ${OS_NAME} (${ARCH})"
}

# Get release version and download URLs
get_release_info() {
    log_info "Fetching release information..."

    local url
    if [ "$VERSION" = "latest" ]; then
        url="${GITHUB_API}/latest"
    else
        url="${GITHUB_API}/tags/${VERSION}"
    fi

    local response
    if ! response=$(curl -s -f "$url" 2>/dev/null); then
        log_error "Failed to fetch release info from GitHub"
        log_error "URL: $url"
        exit 1
    fi

    # Extract version
    RELEASE_VERSION=$(echo "$response" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4 | head -1)

    if [ -z "$RELEASE_VERSION" ]; then
        log_error "Could not find release version"
        exit 1
    fi

    DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${RELEASE_VERSION}/${BINARY_NAME}"
    CHECKSUMS_URL="https://github.com/${REPO}/releases/download/${RELEASE_VERSION}/SHA256SUMS"

    log_success "Version: ${RELEASE_VERSION}"
}

# Download file with error handling
download_file() {
    local url=$1
    local output=$2
    local description=$3

    log_info "Downloading ${description}..."

    if ! curl -fSL --progress-bar -o "$output" "$url"; then
        log_error "Failed to download from $url"
        rm -f "$output"
        return 1
    fi

    log_success "Downloaded successfully"
    return 0
}

# Verify SHA256 checksum
verify_checksum() {
    local binary=$1
    local checksums_file=$2

    log_info "Verifying checksum..."

    # Download checksums
    if ! curl -s -f -o "$checksums_file" "$CHECKSUMS_URL"; then
        log_warn "Could not download SHA256SUMS (continuing without verification)"
        return 0
    fi

    # Extract checksum for our binary
    local expected=$(grep "$BINARY_NAME" "$checksums_file" 2>/dev/null | awk '{print $1}')

    if [ -z "$expected" ]; then
        log_warn "Checksum not found in SHA256SUMS (skipping verification)"
        return 0
    fi

    # Calculate actual checksum
    local actual
    if command -v sha256sum &> /dev/null; then
        actual=$(sha256sum "$binary" 2>/dev/null | awk '{print $1}')
    elif command -v shasum &> /dev/null; then
        actual=$(shasum -a 256 "$binary" 2>/dev/null | awk '{print $1}')
    else
        log_warn "sha256sum not available (skipping verification)"
        return 0
    fi

    if [ "$expected" != "$actual" ]; then
        log_error "Checksum mismatch!"
        log_error "Expected: $expected"
        log_error "Actual:   $actual"
        return 1
    fi

    log_success "Checksum verified"
    return 0
}

# Prepare installation directory
prepare_install_dir() {
    if [ ! -d "$INSTALL_DIR" ]; then
        log_info "Creating installation directory: $INSTALL_DIR"
        mkdir -p "$INSTALL_DIR"
    fi
}

# Install the binary
install_binary() {
    local binary=$1
    local install_path="${INSTALL_DIR}/remind"

    log_info "Installing remind to ${install_path}..."

    cp "$binary" "$install_path"
    chmod +x "$install_path"

    log_success "Installation complete"
}

# Check if install directory is in PATH
check_path() {
    if [[ ":$PATH:" == *":${INSTALL_DIR}:"* ]]; then
        log_success "remind is in your PATH"
        return 0
    else
        log_warn "Installation directory not in PATH"
        return 1
    fi
}

# Update shell configuration
update_shell_config() {
    local shell_config=""
    local shell_name=""

    if [ -n "$ZSH_VERSION" ]; then
        shell_config="$HOME/.zshrc"
        shell_name="zsh"
    elif [ -n "$BASH_VERSION" ]; then
        shell_config="$HOME/.bashrc"
        shell_name="bash"
    else
        # Try to detect based on $SHELL
        if [[ "$SHELL" == *"zsh"* ]]; then
            shell_config="$HOME/.zshrc"
            shell_name="zsh"
        else
            shell_config="$HOME/.bashrc"
            shell_name="bash"
        fi
    fi

    if [ -z "$shell_config" ]; then
        return 1
    fi

    local export_line="export PATH=\"\${PATH}:${INSTALL_DIR}\""

    if grep -q "$INSTALL_DIR" "$shell_config" 2>/dev/null; then
        log_success "PATH already configured in $shell_name"
        return 0
    fi

    echo "" >> "$shell_config"
    echo "# Remind CLI" >> "$shell_config"
    echo "$export_line" >> "$shell_config"

    log_success "Updated $shell_config"
    return 0
}

# Main installation flow
main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Remind CLI Installer"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Detect platform
    detect_platform

    # Get release info
    get_release_info

    # Create temporary directory
    local temp_dir
    temp_dir=$(mktemp -d) || {
        log_error "Failed to create temporary directory"
        exit 1
    }
    trap "rm -rf $temp_dir" EXIT

    # Download binary
    local binary_file="${temp_dir}/${BINARY_NAME}"
    if ! download_file "$DOWNLOAD_URL" "$binary_file" "Remind CLI"; then
        log_error "Installation failed"
        exit 1
    fi

    # Verify checksum
    local checksums_file="${temp_dir}/SHA256SUMS"
    if ! verify_checksum "$binary_file" "$checksums_file"; then
        log_error "Checksum verification failed - aborting installation"
        exit 1
    fi

    # Prepare installation
    prepare_install_dir

    # Install binary
    install_binary "$binary_file"

    # Check and update PATH
    echo ""
    if ! check_path; then
        log_info "Adding ${INSTALL_DIR} to PATH..."
        if update_shell_config; then
            log_info "Please reload your shell: source ~/.bashrc (or ~/.zshrc)"
        else
            log_warn "Could not auto-update shell config"
            log_info "Manually add this line to your ~/.bashrc or ~/.zshrc:"
            echo "  export PATH=\"\${PATH}:${INSTALL_DIR}\""
        fi
    fi

    # Print success message
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_success "Remind is ready to use!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    log_info "Try it out:"
    echo "  remind --help"
    echo "  remind add \"Example reminder\""
    echo ""
}

# Run installation
main "$@"

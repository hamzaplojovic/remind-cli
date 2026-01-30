#!/bin/bash
# Build Debian/Ubuntu package for Remind
# Usage: ./build_deb.sh [VERSION]

set -e

VERSION="${1:-0.1.0}"
REPO_NAME="remind"
ARCH="amd64"
OUTPUT_DIR="dist"

# Create build directory structure
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

echo "Building Debian package for Remind ${VERSION}..."

# Create directory structure for deb package
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/local/bin"
mkdir -p "${BUILD_DIR}/usr/share/doc/remind"

# Copy binary
if [ ! -f "dist/remind" ]; then
    echo "Error: dist/remind not found. Run 'python build_tools/build.py' first."
    exit 1
fi

cp "dist/remind" "${BUILD_DIR}/usr/local/bin/remind"
chmod 755 "${BUILD_DIR}/usr/local/bin/remind"

# Create DEBIAN/control file
cat > "${BUILD_DIR}/DEBIAN/control" << EOF
Package: ${REPO_NAME}
Version: ${VERSION}
Architecture: ${ARCH}
Maintainer: Remind Contributors <support@remind.dev>
Description: AI-powered CLI reminder and notification engine
 Remind is a cross-platform CLI tool for managing reminders with desktop
 notifications and AI-powered suggestions (premium feature).
 .
 Features:
  * Instant reminder capture with natural language dates
  * Desktop notifications when reminders are due
  * Local SQLite database storage
  * Premium AI rephrasing and smart nudges
  * Analytics and reporting
Section: utilities
Priority: optional
Depends: libnotify-bin
Homepage: https://github.com/hamzaplojovic/remember
EOF

# Create DEBIAN/postinst script
cat > "${BUILD_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    configure)
        # Create symlink in /usr/bin if it doesn't exist
        if [ ! -L /usr/bin/remind ] && [ ! -f /usr/bin/remind ]; then
            ln -s /usr/local/bin/remind /usr/bin/remind 2>/dev/null || true
        fi
        echo "Remind installed successfully!"
        echo "Run 'remind --help' to get started"
        ;;
    abort-upgrade|abort-remove|abort-deconfigure)
        ;;
    *)
        echo "postinst called with unknown argument \`$1'" >&2
        exit 1
        ;;
esac

exit 0
EOF

chmod 755 "${BUILD_DIR}/DEBIAN/postinst"

# Create DEBIAN/prerm script
cat > "${BUILD_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

case "$1" in
    remove|deconfigure)
        # Remove symlink if it exists
        [ -L /usr/bin/remind ] && rm -f /usr/bin/remind 2>/dev/null || true
        ;;
    upgrade|failed-upgrade)
        ;;
    *)
        echo "prerm called with unknown argument \`$1'" >&2
        exit 1
        ;;
esac

exit 0
EOF

chmod 755 "${BUILD_DIR}/DEBIAN/prerm"

# Create changelog
cat > "${BUILD_DIR}/usr/share/doc/remind/changelog.gz" << 'EOF'
remind (0.1.0) unstable; urgency=medium
  * Initial release
  * MVP: CLI reminders with desktop notifications
  * Premium: AI-powered suggestions and smart nudges
EOF

# Build the deb package
mkdir -p "${OUTPUT_DIR}"
DEB_FILE="${OUTPUT_DIR}/remind_${VERSION}_${ARCH}.deb"

dpkg-deb --build "${BUILD_DIR}" "${DEB_FILE}"

if [ -f "${DEB_FILE}" ]; then
    echo "✓ Package created: ${DEB_FILE}"
    ls -lh "${DEB_FILE}"
else
    echo "✗ Failed to create package"
    exit 1
fi

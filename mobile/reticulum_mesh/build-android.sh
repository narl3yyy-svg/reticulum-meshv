#!/usr/bin/env bash
set -e

echo "=== Building Reticulum Mesh for Android ==="

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Ensure Python 3.13 is available (needed for cryptography Android wheels on Chaquopy)
if ! python3.13 --version &>/dev/null; then
    if command -v uv &>/dev/null; then
        echo ">>> Installing Python 3.13 via uv"
        uv python install 3.13
        PYTHON_BIN="$(uv python find 3.13)"
    else
        echo "ERROR: Python 3.13 not found. Install it (e.g. 'uv python install 3.13' or 'apt install python3.13')"
        exit 1
    fi
else
    PYTHON_BIN="$(command -v python3.13)"
fi

echo ">>> Using Python: $($PYTHON_BIN --version)"

# Create/find a build venv with briefcase
BUILD_VENV="$PROJECT_DIR/build-venv"
if [ ! -f "$BUILD_VENV/bin/briefcase" ]; then
    echo ">>> Creating build venv"
    "$PYTHON_BIN" -m venv "$BUILD_VENV"
    "$BUILD_VENV/bin/pip" install -U briefcase
fi

source "$BUILD_VENV/bin/activate"

# Clean old build
echo ">>> Removing old Android build artifacts"
rm -rf "$PROJECT_DIR/build/reticulum_mesh/android"

# Generate Android project (uses Python 3.13, which has cryptography wheels on Chaquopy)
echo ">>> briefcase create android"
briefcase create android

# Build APK
echo ">>> briefcase build android"
briefcase build android

# Install & run on connected device
echo ">>> briefcase run android"
briefcase run android -d "@beePhone"

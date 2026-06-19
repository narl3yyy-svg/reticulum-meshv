#!/usr/bin/env bash
set -e

echo "=== Building Reticulum Mesh for Android ==="

cd "$(dirname "$0")"

# Step 1: Generate Android project
echo ">>> briefcase create android"
briefcase create android

# Step 2: Patch Python version to 3.12 (3.14 has no cryptography wheels for Android)
GRADLE_FILE="build/reticulum_mesh/android/gradle/app/build.gradle"
if grep -q 'version "3.14"' "$GRADLE_FILE"; then
    echo ">>> Patching Python version: 3.14 -> 3.12"
    sed -i 's/version "3.14"/version "3.12"/' "$GRADLE_FILE"
else
    echo ">>> Python version already patched or not found"
fi

# Step 3: Build
echo ">>> briefcase build android"
briefcase build android

# Step 4: Run
echo ">>> briefcase run android"
briefcase run android -d "@beePhone"

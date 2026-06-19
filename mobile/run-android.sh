#!/bin/bash

# One-command script to run Reticulum Mesh on Android

set -e

echo "=== Reticulum Mesh Android Runner ==="

# Go to project root
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "No .venv found. Please create one and install briefcase first."
    exit 1
fi

# Go to mobile project
cd mobile/reticulum_mesh

echo "Building and running on Android..."
briefcase run android

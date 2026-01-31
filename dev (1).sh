#!/bin/bash
# Start The-Dictator development server
# Usage: ./scripts/dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found."
    echo "Run: python -m venv .venv && source .venv/bin/activate && pip install -e ."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check for config
if [ ! -f "config/settings.toml" ]; then
    echo "Warning: config/settings.toml not found."
    echo "Creating from example..."
    mkdir -p config
    cp config.example.toml config/settings.toml
fi

# Start backend with auto-reload
echo "Starting The-Dictator backend on http://127.0.0.1:8765"
echo "Frontend: Open frontend/index.html in Chrome"
echo "Press Ctrl+C to stop"
echo ""

uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload

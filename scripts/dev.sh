#!/bin/bash
# Start The-Dictator development server
# Usage: ./scripts/dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Check for config
if [ ! -f "config/settings.toml" ]; then
    echo "Warning: config/settings.toml not found."
    echo "Creating from example..."
    mkdir -p config
    if [ -f "config/settings.example.toml" ]; then
        cp config/settings.example.toml config/settings.toml
    fi
fi

if [ ! -f "config/button_map.toml" ]; then
    echo "Warning: config/button_map.toml not found."
    echo "Creating from example..."
    if [ -f "config/button_map.example.toml" ]; then
        cp config/button_map.example.toml config/button_map.toml
    fi
fi

# Make sure scripts are executable
chmod +x scripts/*.sh

# Start backend with auto-reload
echo "Starting The-Dictator backend on http://127.0.0.1:8765"
echo "Frontend: Open frontend/index.html in your browser"
echo "Press Ctrl+C to stop"
echo ""

# Run backend
# We use python -m backend.main to run the module, which invokes uvicorn
python3 -m backend.main

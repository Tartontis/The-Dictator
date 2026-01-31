#!/bin/bash
# Download faster-whisper model
# Usage: ./scripts/download_model.sh <model_name>
# Models: tiny, base, small, medium, large-v3

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_DIR/models"

# Default model
MODEL="${1:-small}"

# Validate model name
case "$MODEL" in
    tiny|base|small|medium|large-v3|large-v2|large)
        ;;
    *)
        echo "Error: Invalid model name '$MODEL'"
        echo "Valid models: tiny, base, small, medium, large-v3"
        exit 1
        ;;
esac

echo "Downloading faster-whisper model: $MODEL"
echo "Target directory: $MODELS_DIR"
echo ""

# Activate virtual environment if exists
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
fi

# Download using Python (faster-whisper handles caching)
python3 << EOF
from faster_whisper import WhisperModel
import os

model_name = "$MODEL"
models_dir = "$MODELS_DIR"

print(f"Loading model '{model_name}' (this will download if not cached)...")
print("Note: Models are cached in ~/.cache/huggingface by default")
print("")

# This triggers the download
model = WhisperModel(model_name, device="cpu", compute_type="int8")

print("")
print(f"✓ Model '{model_name}' is ready!")
print("")
print("Model sizes (approximate):")
print("  tiny:     ~75 MB")
print("  base:     ~150 MB")
print("  small:    ~500 MB")
print("  medium:   ~1.5 GB")
print("  large-v3: ~3 GB")
EOF

echo ""
echo "Done! You can now start The-Dictator with:"
echo "  ./scripts/dev.sh"

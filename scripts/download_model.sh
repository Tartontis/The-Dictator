#!/bin/bash
# Download Whisper model using python script
# Usage: ./scripts/download_model.sh [size]

SIZE=${1:-small}

echo "Downloading Whisper model: $SIZE"

# We can use a simple python one-liner to download via faster-whisper
# This will download to the default cache directory
python3 -c "from faster_whisper import download_model; print(f'Downloaded to: {download_model(\"$SIZE\")}')"

echo "Done."

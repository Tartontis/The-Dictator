#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.output.gui import VoxPadApp  # noqa: E402

def main():
    app = VoxPadApp()
    app.run()

if __name__ == "__main__":
    main()

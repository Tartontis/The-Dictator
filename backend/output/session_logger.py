from datetime import datetime
from pathlib import Path

from backend.config import Settings


class SessionLogger:
    def __init__(self, settings: Settings):
        self.directory = settings.session.directory
        self.date_format = settings.session.date_format
        self.include_timestamps = settings.session.include_timestamps

        # Ensure directory exists
        self.directory.mkdir(parents=True, exist_ok=True)

    def get_session_file(self) -> Path:
        filename = datetime.now().strftime(self.date_format) + ".md"
        return self.directory / filename

    def append(self, text: str) -> Path:
        filepath = self.get_session_file()
        timestamp = datetime.now().strftime("%H:%M:%S") if self.include_timestamps else ""

        # If file doesn't exist, start with a header
        if not filepath.exists():
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Session Log: {datetime.now().strftime('%Y-%m-%d')}\n")

        entry = f"\n### {timestamp}\n{text}\n" if timestamp else f"\n{text}\n"

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(entry)

        return filepath

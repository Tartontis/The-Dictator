import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .models import Settings

CONFIG_PATH = Path("config/settings.toml")
DEFAULT_CONFIG_PATH = Path("config/settings.example.toml")

def load_settings() -> Settings:
    config_file = CONFIG_PATH
    if not config_file.exists():
        # Fallback to example config if actual config doesn't exist
        # This allows the app to run out of the box
        if DEFAULT_CONFIG_PATH.exists():
            config_file = DEFAULT_CONFIG_PATH
        else:
            raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH} or {DEFAULT_CONFIG_PATH}")

    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)

    return Settings(**config_data)

import sys
from pathlib import Path
from typing import Dict, Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .models import Settings

CONFIG_PATH = Path("config/settings.toml")
DEFAULT_CONFIG_PATH = Path("config/settings.example.toml")

BUTTON_MAP_PATH = Path("config/button_map.toml")
DEFAULT_BUTTON_MAP_PATH = Path("config/button_map.example.toml")

def load_settings() -> Settings:
    config_file = CONFIG_PATH
    if not config_file.exists():
        if DEFAULT_CONFIG_PATH.exists():
            config_file = DEFAULT_CONFIG_PATH
        else:
            raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH} or {DEFAULT_CONFIG_PATH}")

    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)

    return Settings(**config_data)

def load_button_map() -> Dict[str, Any]:
    config_file = BUTTON_MAP_PATH
    if not config_file.exists():
        if DEFAULT_BUTTON_MAP_PATH.exists():
            config_file = DEFAULT_BUTTON_MAP_PATH
        else:
             # Return empty default if neither exists, though we expect example to exist
            return {"midi": {}, "keyboard": {}}

    with open(config_file, "rb") as f:
        return tomllib.load(f)

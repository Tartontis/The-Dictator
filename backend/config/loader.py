from functools import lru_cache
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from .models import Settings

CONFIG_PATH = Path("config/settings.toml")
DEFAULT_CONFIG_PATHS = [
    Path("config/settings.example.toml"),
    Path("config.example.toml"),
]

@lru_cache(maxsize=1)
def load_settings() -> Settings:
    config_file = CONFIG_PATH
    if not config_file.exists():
        # Fallback to example config if actual config doesn't exist
        # This allows the app to run out of the box
        for candidate in DEFAULT_CONFIG_PATHS:
            if candidate.exists():
                config_file = candidate
                break
        else:
            searched = ", ".join(str(path) for path in [CONFIG_PATH, *DEFAULT_CONFIG_PATHS])
            raise FileNotFoundError(f"Configuration file not found at {searched}")

    with open(config_file, "rb") as f:
        config_data = tomllib.load(f)

    return Settings(**config_data)

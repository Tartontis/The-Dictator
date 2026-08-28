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
    # Try the primary config path followed by fallbacks
    # This allows the app to run out of the box with example configs
    candidates = [CONFIG_PATH, *DEFAULT_CONFIG_PATHS]

    for candidate in candidates:
        try:
            with open(candidate, "rb") as f:
                config_data = tomllib.load(f)
            return Settings(**config_data)
        except FileNotFoundError:
            continue

    searched = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Configuration file not found at {searched}")

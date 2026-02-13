"""
Tests for configuration loading.
"""
from pathlib import Path


def test_example_config_exists(config_dir: Path):
    """Verify the example config file exists."""
    example_config = config_dir / "settings.example.toml"
    assert example_config.exists(), f"Example config not found at {example_config}"


def test_example_button_map_exists(config_dir: Path):
    """Verify the example button map file exists."""
    example_map = config_dir / "button_map.example.toml"
    assert example_map.exists(), f"Example button map not found at {example_map}"


def test_config_loader_import():
    """Verify config loader can be imported."""
    from backend.config import load_settings
    assert callable(load_settings)


def test_config_models_import():
    """Verify config models can be imported."""
    from backend.config.models import LLMConfig, ServerConfig, Settings
    assert Settings is not None
    assert ServerConfig is not None
    assert LLMConfig is not None

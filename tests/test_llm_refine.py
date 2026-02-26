"""
Tests for LLM refinement functionality.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.config.models import (
    AnthropicConfig,
    AudioConfig,
    ClusterConfig,
    LLMConfig,
    ServerConfig,
    SessionConfig,
    Settings,
    TemplatesConfig,
    TranscriptionConfig,
    VadConfig,
)
from backend.engine.llm import LLMEngine


# Mock environment variables to avoid real API keys
@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test-key")

@pytest.fixture
def mock_settings(tmp_path):
    """Create a minimal settings object for testing."""
    # Create a dummy template directory
    templates_dir = tmp_path / "prompts"
    templates_dir.mkdir()
    (templates_dir / "test_template.j2").write_text("Refine this: {{ text }}")

    # Create LLM config
    llm = LLMConfig(
        default_provider="anthropic",
        anthropic=AnthropicConfig(
            model="claude-sonnet-4-20250514",
            max_tokens=100
        )
    )

    templates = TemplatesConfig(
        directory=templates_dir,
        default="test_template"
    )

    return Settings(
        server=ServerConfig(),
        audio=AudioConfig(),
        transcription=TranscriptionConfig(),
        vad=VadConfig(),
        session=SessionConfig(),
        llm=llm,
        cluster=ClusterConfig(),
        templates=templates
    )

@pytest.mark.asyncio
async def test_refine_text_anthropic(mock_env_vars, mock_settings):
    """Test refining text with Anthropic provider."""

    # Mock the AsyncAnthropic client
    with patch("backend.engine.llm.AsyncAnthropic") as MockAnthropic:
        # Create mock client instance
        mock_client = AsyncMock()
        MockAnthropic.return_value = mock_client

        # Mock the response from messages.create
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Refined text response"
        mock_response.content = [mock_content]

        mock_client.messages.create.return_value = mock_response

        # Initialize engine
        engine = LLMEngine(mock_settings)

        # Call refine_text
        text = "original text"
        template = "test_template"
        refined = await engine.refine_text(text, template, provider="anthropic")

        # Assertions
        assert refined == "Refined text response"

        # Verify client initialization
        MockAnthropic.assert_called_once_with(api_key="sk-ant-test-key")

        # Verify API call arguments
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        assert call_args["model"] == "claude-sonnet-4-20250514"
        assert call_args["max_tokens"] == 100
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["role"] == "user"
        # The prompt is rendered from the template: "Refine this: {{ text }}"
        assert "Refine this: original text" in call_args["messages"][0]["content"]

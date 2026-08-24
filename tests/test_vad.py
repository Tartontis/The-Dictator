"""
Tests for VAD integration in Transcriber.
"""
from unittest.mock import MagicMock, patch

import pytest

from backend.config.models import (
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
from backend.engine.transcriber import Transcriber


@pytest.fixture
def mock_settings():
    """Create a settings object with VAD enabled."""
    return Settings(
        server=ServerConfig(),
        audio=AudioConfig(),
        transcription=TranscriptionConfig(model="tiny", device="cpu"),
        vad=VadConfig(
            enabled=True,
            threshold=0.6,
            min_speech_duration=0.3,
            min_silence_duration=1.5
        ),
        session=SessionConfig(),
        llm=LLMConfig(),
        cluster=ClusterConfig(),
        templates=TemplatesConfig()
    )

def test_transcriber_uses_vad(mock_settings):
    """Test that transcribe passes VAD parameters to the model."""
    with patch("backend.engine.transcriber.WhisperModel") as MockModel:
        # Setup mock model instance
        mock_instance = MagicMock()
        MockModel.return_value = mock_instance

        # Mock transcribe return value
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99

        mock_instance.transcribe.return_value = ([mock_segment], mock_info)

        # Initialize transcriber
        transcriber = Transcriber(mock_settings)

        # Call transcribe
        transcriber.transcribe("test.wav")

        # Verify WhisperModel was initialized correctly
        MockModel.assert_called_with("tiny", device="cpu", compute_type="int8")

        # Verify transcribe was called with VAD params
        mock_instance.transcribe.assert_called_once()
        call_args = mock_instance.transcribe.call_args
        _, kwargs = call_args

        assert kwargs["vad_filter"] is True
        assert kwargs["vad_parameters"]["threshold"] == 0.6
        assert kwargs["vad_parameters"]["min_speech_duration_ms"] == 300
        assert kwargs["vad_parameters"]["min_silence_duration_ms"] == 1500

def test_transcriber_disables_vad(mock_settings):
    """Test that transcribe disables VAD when configured."""
    mock_settings.vad.enabled = False

    with patch("backend.engine.transcriber.WhisperModel") as MockModel:
        mock_instance = MagicMock()
        MockModel.return_value = mock_instance

        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_info = MagicMock()
        mock_info.language = "en"
        mock_info.language_probability = 0.99

        mock_instance.transcribe.return_value = ([mock_segment], mock_info)

        transcriber = Transcriber(mock_settings)
        transcriber.transcribe("test.wav")

        # Verify transcribe was called without VAD params (or with False/None)
        mock_instance.transcribe.assert_called_once()
        _, kwargs = mock_instance.transcribe.call_args

        assert kwargs["vad_filter"] is False
        assert kwargs["vad_parameters"] is None

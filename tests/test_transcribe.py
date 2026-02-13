import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import io
import sys
from pathlib import Path

# We need to mock faster_whisper before importing backend.engine
# because backend.engine imports it at module level (or inside load_model)

def test_transcribe_endpoint_uses_memory_file():
    # Setup the mock instance
    mock_instance = MagicMock()

    # specific mock for transcribe method
    # It returns segments and info
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_info = MagicMock()
    mock_info.language = "en"
    mock_info.language_probability = 0.99

    # transcribe returns (generator of segments, info)
    mock_instance.transcribe.return_value = ([mock_segment], mock_info)

    # Mock the class constructor
    MockModel = MagicMock(return_value=mock_instance)

    # Patch WhisperModel in backend.engine.transcriber module
    with patch("backend.engine.transcriber.WhisperModel", MockModel):

        from backend.main import app
        from backend.engine import Transcriber
        from backend.config import Settings

        # Mock settings
        # We need to create a valid Settings object or mock it
        # Since Transcriber accesses attributes like settings.transcription.model
        settings = MagicMock()
        settings.transcription.model = "tiny"
        settings.transcription.device = "cpu"
        settings.transcription.compute_type = "int8"
        settings.transcription.language = "en"

        transcriber = Transcriber(settings)

        # We can override the dependency
        from backend.api.routes import get_transcriber
        app.dependency_overrides[get_transcriber] = lambda: transcriber

        client = TestClient(app)

        # Create a dummy file
        file_content = b"fake audio data"

        # Use a file-like object for upload
        files = {"file": ("test.wav", io.BytesIO(file_content), "audio/wav")}

        response = client.post("/api/transcribe", files=files)

        if response.status_code != 200:
            print(response.json())

        assert response.status_code == 200
        assert response.json() == {"text": "Hello world"}

        # Verify that transcribe was called with a file-like object, not a string path
        # arguments to transcribe: (audio, language=..., beam_size=...)
        # transcriber.model is our mock_instance

        assert mock_instance.transcribe.called
        call_args = mock_instance.transcribe.call_args
        assert call_args is not None

        # The first argument to model.transcribe
        audio_arg = call_args[0][0]

        # It should be a file-like object (specifically SpooledTemporaryFile or BytesIO wrapper from FastAPI)
        # We can check if it has a read method
        assert hasattr(audio_arg, "read")
        # It should NOT be a string
        assert not isinstance(audio_arg, str)

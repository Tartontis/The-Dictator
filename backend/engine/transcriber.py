import logging
from pathlib import Path
from typing import Union, BinaryIO
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from backend.config import Settings

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, settings: Settings):
        self.settings = settings.transcription
        self.model = None

    def load_model(self):
        if WhisperModel is None:
            raise ImportError("faster-whisper is not installed. Please install it with 'pip install faster-whisper'")

        if self.model is None:
            logger.info(f"Loading Whisper model: {self.settings.model} on {self.settings.device}")
            # Initialize the model
            # Note: download_root can be configured if needed, defaults to cache
            self.model = WhisperModel(
                self.settings.model,
                device=self.settings.device,
                compute_type=self.settings.compute_type
            )
            logger.info("Model loaded")

    def transcribe(self, audio_path: Union[str, Path, BinaryIO]) -> str:
        self.load_model()

        logger.info(f"Transcribing audio file: {audio_path}")

        # language=None means auto-detect if set to "auto" in config,
        # but faster-whisper expects None for auto, or a code string.
        lang = self.settings.language
        if lang == "auto":
            lang = None

        # faster-whisper accepts str (path) or file-like object.
        # If it's a Path object, convert to str.
        audio_input = str(audio_path) if isinstance(audio_path, Path) else audio_path

        segments, info = self.model.transcribe(
            audio_input,
            language=lang,
            beam_size=5
        )

        logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")

        text = " ".join([segment.text for segment in segments])
        return text.strip()

import logging
from pathlib import Path
from typing import BinaryIO

from backend.config.models import Settings

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

logger = logging.getLogger(__name__)

class Transcriber:
    def __init__(self, settings: Settings):
        self.settings = settings.transcription
        self.vad_settings = settings.vad
        self.model = None

    def load_model(self):
        if WhisperModel is None:
            raise ImportError("faster-whisper is not installed. Please install it with 'pip install faster-whisper'")

        if self.model is None:
            logger.info(f"Loading Whisper model: {self.settings.model} on {self.settings.device}")
            # Initialize the model
            self.model = WhisperModel(
                self.settings.model,
                device=self.settings.device,
                compute_type=self.settings.compute_type
            )
            logger.info("Model loaded")

    def transcribe(self, audio_path: str | Path | BinaryIO) -> str:
        self.load_model()

        logger.info(f"Transcribing audio file: {audio_path}")

        lang = self.settings.language
        if lang == "auto":
            lang = None

        audio_input = str(audio_path) if isinstance(audio_path, Path) else audio_path

        vad_filter = self.vad_settings.enabled
        vad_parameters = None
        if vad_filter:
            vad_parameters = {
                "threshold": self.vad_settings.threshold,
                "min_speech_duration_ms": int(self.vad_settings.min_speech_duration * 1000),
                "min_silence_duration_ms": int(self.vad_settings.min_silence_duration * 1000),
            }

        segments, info = self.model.transcribe(
            audio_input,
            language=lang,
            beam_size=5,
            vad_filter=vad_filter,
            vad_parameters=vad_parameters
        )

        logger.info(f"Detected language '{info.language}' with probability {info.language_probability}")

        text = " ".join(segment.text for segment in segments)
        return text.strip()

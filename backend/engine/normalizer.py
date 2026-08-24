import shutil
import subprocess
import logging
from pathlib import Path
from backend.config import Settings

logger = logging.getLogger(__name__)

class Normalizer:
    def __init__(self, settings: Settings):
        self.enabled = settings.audio.normalize
        self.ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        return shutil.which("ffmpeg") is not None

    def normalize(self, input_path: Path) -> Path:
        """
        Normalize audio using ffmpeg-loudnorm or similar filter.
        Returns the path to the normalized file (could be same as input if skipped).
        """
        if not self.enabled:
            return input_path

        if not self.ffmpeg_available:
            logger.warning("Normalization enabled but ffmpeg not found. Skipping.")
            return input_path

        output_path = input_path.with_suffix(".norm.wav")

        logger.info(f"Normalizing audio: {input_path}")

        # Simple peak normalization to -1dB
        # Or use loudnorm for EBU R128
        # Let's use simple loudnorm as it's robust for speech
        cmd = [
            "ffmpeg",
            "-y", # Overwrite
            "-i", str(input_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar", "16000", # Ensure 16kHz
            "-ac", "1",     # Ensure mono
            str(output_path)
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            logger.info(f"Normalization complete: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg normalization failed: {e.stderr.decode()}")
            # Fallback to original
            return input_path

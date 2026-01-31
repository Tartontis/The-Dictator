import shutil
import tempfile
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from backend.config import load_settings, Settings
from backend.engine import Transcriber
from backend.output import SessionLogger

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instances
_transcriber = None
_session_logger = None

def get_settings():
    return load_settings()

def get_transcriber(settings: Settings = Depends(get_settings)):
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber(settings)
    return _transcriber

def get_session_logger(settings: Settings = Depends(get_settings)):
    global _session_logger
    if _session_logger is None:
        _session_logger = SessionLogger(settings)
    return _session_logger

class AppendRequest(BaseModel):
    text: str

class TranscribeResponse(BaseModel):
    text: str

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    return settings

@router.post("/transcribe")
def transcribe_audio(
    file: UploadFile = File(...),
    transcriber: Transcriber = Depends(get_transcriber)
) -> TranscribeResponse:
    logger.info(f"Received audio upload: {file.filename}")

    # Save upload to temp file
    # Ensure we keep the extension so ffmpeg/whisper knows format
    suffix = Path(file.filename).suffix
    if not suffix:
        suffix = ".wav" # Default to wav if unknown

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        text = transcriber.transcribe(tmp_path)
        return TranscribeResponse(text=text)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up
        if tmp_path.exists():
            tmp_path.unlink()

@router.post("/session/append")
def append_session(
    request: AppendRequest,
    session_logger: SessionLogger = Depends(get_session_logger)
):
    try:
        path = session_logger.append(request.text)
        return {"status": "success", "file": str(path)}
    except Exception as e:
        logger.error(f"Failed to append to session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

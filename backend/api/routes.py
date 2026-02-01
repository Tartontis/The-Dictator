import shutil
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from backend.config import load_settings, load_button_map, Settings
from backend.engine import Transcriber, LLMEngine, Normalizer
from backend.output import SessionLogger

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instances
_transcriber = None
_session_logger = None
_llm_engine = None
_normalizer = None

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

def get_llm_engine(settings: Settings = Depends(get_settings)):
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine(settings)
    return _llm_engine

def get_normalizer(settings: Settings = Depends(get_settings)):
    global _normalizer
    if _normalizer is None:
        _normalizer = Normalizer(settings)
    return _normalizer

class AppendRequest(BaseModel):
    text: str

class RefineRequest(BaseModel):
    text: str
    template: str
    provider: Optional[str] = None

class TranscribeResponse(BaseModel):
    text: str

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    return settings

@router.get("/button_map")
def get_button_map():
    return load_button_map()

@router.post("/transcribe")
def transcribe_audio(
    file: UploadFile = File(...),
    transcriber: Transcriber = Depends(get_transcriber),
    normalizer: Normalizer = Depends(get_normalizer)
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

    # Track files to clean up
    files_to_clean = [tmp_path]

    try:
        # Normalize
        norm_path = normalizer.normalize(tmp_path)
        if norm_path != tmp_path:
            files_to_clean.append(norm_path)

        text = transcriber.transcribe(norm_path)
        return TranscribeResponse(text=text)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up
        for p in files_to_clean:
            if p.exists():
                p.unlink()

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

@router.post("/refine")
async def refine_text(
    request: RefineRequest,
    llm_engine: LLMEngine = Depends(get_llm_engine)
):
    try:
        refined_text = await llm_engine.refine_text(
            text=request.text,
            template_name=request.template,
            provider=request.provider
        )
        return {"text": refined_text}
    except Exception as e:
        logger.error(f"Refinement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

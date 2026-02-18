import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.config import Settings, load_settings
from backend.engine import LLMEngine, Transcriber
from backend.output import SessionLogger

router = APIRouter()
logger = logging.getLogger(__name__)

# Singleton instances
_transcriber = None
_session_logger = None
_llm_engine = None

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

class AppendRequest(BaseModel):
    text: str

class RefineRequest(BaseModel):
    text: str
    template: str
    provider: str | None = None

class TranscribeResponse(BaseModel):
    text: str

@router.get("/health")
def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "version": "0.1.0",
        "transcription_model": settings.transcription.model,
        "session_directory": str(settings.session.directory),
    }

@router.get("/config")
def get_config(settings: Settings = Depends(get_settings)):
    return settings

@router.post("/transcribe")
def transcribe_audio(
    file: UploadFile = File(...),
    transcriber: Transcriber = Depends(get_transcriber)
) -> TranscribeResponse:
    logger.info(f"Received audio upload: {file.filename}")

    try:
        text = transcriber.transcribe(file.file)
        return TranscribeResponse(text=text)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
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
        raise HTTPException(status_code=500, detail=str(e)) from e

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
        raise HTTPException(status_code=500, detail=str(e)) from e

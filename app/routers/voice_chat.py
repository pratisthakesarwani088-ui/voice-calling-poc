"""Voice-chat endpoint: full Sarvam STT -> Gemini -> ElevenLabs TTS pipeline."""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.routers.speech_to_text import ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE_BYTES
from app.services.pipeline_service import PipelineError, run_voice_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-chat"])


@router.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)) -> Response:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only WAV and MP3 audio files are supported",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(audio_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds maximum size of 20MB")

    try:
        reply_audio, _reply_text = await run_voice_pipeline(audio_bytes, file.filename, file.content_type)
        return Response(content=reply_audio, media_type="audio/mpeg")
    except PipelineError as exc:
        logger.error("Voice-chat pipeline failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

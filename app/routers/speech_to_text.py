"""Speech-to-text endpoint backed by the Sarvam API."""
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.services.sarvam_service import SarvamServiceError, transcribe_audio

logger = logging.getLogger(__name__)

router = APIRouter(tags=["speech-to-text"])

ALLOWED_CONTENT_TYPES = {"audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class TranscriptionResponse(BaseModel):
    text: str


@router.post("/speech-to-text", response_model=TranscriptionResponse)
async def speech_to_text(file: UploadFile = File(...)) -> TranscriptionResponse:
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
        transcript = await transcribe_audio(audio_bytes, file.filename, file.content_type)
        return TranscriptionResponse(text=transcript)
    except SarvamServiceError as exc:
        logger.error("Speech-to-text request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to transcribe audio via Sarvam") from exc

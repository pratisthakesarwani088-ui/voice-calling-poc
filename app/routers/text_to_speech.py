"""Text-to-speech endpoint backed by the ElevenLabs API."""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.elevenlabs_service import ElevenLabsServiceError, synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(tags=["text-to-speech"])


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1)


@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest) -> Response:
    try:
        audio_bytes = await synthesize_speech(request.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except ElevenLabsServiceError as exc:
        logger.error("Text-to-speech request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to synthesize speech via ElevenLabs") from exc

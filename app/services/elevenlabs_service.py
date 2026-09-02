"""Reusable service for calling the ElevenLabs Text-to-Speech API."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_TTS_URL_TEMPLATE = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# Maps a short format name to the ElevenLabs `output_format` query value.
# "mp3" (default) preserves existing /text-to-speech behavior.
# "ulaw_8000" returns raw 8kHz mu-law audio, ready for Twilio Media Streams.
_OUTPUT_FORMATS = {
    "mp3": "mp3_44100_128",
    "ulaw_8000": "ulaw_8000",
}
_ACCEPT_HEADERS = {
    "mp3": "audio/mpeg",
    "ulaw_8000": "audio/basic",
}


class ElevenLabsServiceError(Exception):
    """Raised when the ElevenLabs API call fails or returns an unusable response."""


async def synthesize_speech(text: str, output_format: str = "mp3") -> bytes:
    """Send text to ElevenLabs TTS and return the generated audio bytes.

    output_format: "mp3" (default, used by /text-to-speech and /voice-chat)
    or "ulaw_8000" (raw 8kHz mu-law, used by the Twilio media stream).
    """
    if not settings.ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY is not configured")
        raise ElevenLabsServiceError("ElevenLabs API key is not configured")
    if not settings.ELEVENLABS_VOICE_ID:
        logger.error("ELEVENLABS_VOICE_ID is not configured")
        raise ElevenLabsServiceError("ElevenLabs voice ID is not configured")
    if output_format not in _OUTPUT_FORMATS:
        raise ElevenLabsServiceError(f"Unsupported output_format: {output_format}")

    url = ELEVENLABS_TTS_URL_TEMPLATE.format(voice_id=settings.ELEVENLABS_VOICE_ID)
    params = {"output_format": _OUTPUT_FORMATS[output_format]}
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Accept": _ACCEPT_HEADERS[output_format],
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, params=params, json=payload)
    except httpx.RequestError as exc:
        logger.exception("Network error calling ElevenLabs API")
        raise ElevenLabsServiceError("Failed to reach ElevenLabs API") from exc

    if resp.status_code != 200:
        logger.error("ElevenLabs API returned %s: %s", resp.status_code, resp.text)
        raise ElevenLabsServiceError(f"ElevenLabs API error (status {resp.status_code})")

    if not resp.content:
        logger.error("ElevenLabs API returned empty audio content")
        raise ElevenLabsServiceError("Unexpected empty response from ElevenLabs API")

    return resp.content

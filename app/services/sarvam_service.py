"""Reusable service for calling the Sarvam Speech-to-Text and Text-to-Speech APIs."""
import base64
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# Maps a short format name to Sarvam's output_audio_codec value.
# "mp3" (default) preserves existing /text-to-speech behavior.
# "ulaw_8000" returns 8kHz mu-law audio, ready for Twilio Media Streams.
_OUTPUT_CODECS = {
    "mp3": "mp3",
    "ulaw_8000": "mulaw",
}


class SarvamServiceError(Exception):
    """Raised when a Sarvam API call fails or returns an unusable response."""


async def transcribe_audio(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Send audio bytes to Sarvam STT and return the transcribed text."""
    if not settings.SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY is not configured")
        raise SarvamServiceError("Sarvam API key is not configured")

    headers = {"api-subscription-key": settings.SARVAM_API_KEY}
    files = {"file": (filename, file_bytes, content_type)}
    data = {"model": "saaras:v3"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
    except httpx.RequestError as exc:
        logger.exception("Network error calling Sarvam STT API")
        raise SarvamServiceError("Failed to reach Sarvam API") from exc

    if resp.status_code != 200:
        logger.error("Sarvam STT API returned %s: %s", resp.status_code, resp.text)
        raise SarvamServiceError(f"Sarvam API error (status {resp.status_code})")

    try:
        result = resp.json()
        return result["transcript"]
    except (KeyError, ValueError) as exc:
        logger.exception("Unexpected Sarvam STT response shape")
        raise SarvamServiceError("Unexpected response from Sarvam API") from exc


async def synthesize_speech(text: str, output_format: str = "mp3") -> bytes:
    """Send text to Sarvam TTS (Bulbul v3) and return the generated audio bytes.

    output_format: "mp3" (default, used by /text-to-speech and /voice-chat)
    or "ulaw_8000" (raw 8kHz mu-law, used by the Twilio media stream).
    """
    if not settings.SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY is not configured")
        raise SarvamServiceError("Sarvam API key is not configured")
    if output_format not in _OUTPUT_CODECS:
        raise SarvamServiceError(f"Unsupported output_format: {output_format}")

    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "target_language_code": settings.SARVAM_TTS_LANGUAGE,
        "speaker": settings.SARVAM_TTS_SPEAKER,
        "model": "bulbul:v3",
        "output_audio_codec": _OUTPUT_CODECS[output_format],
    }
    if output_format == "ulaw_8000":
        payload["speech_sample_rate"] = 8000

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(SARVAM_TTS_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        logger.exception("Network error calling Sarvam TTS API")
        raise SarvamServiceError("Failed to reach Sarvam API") from exc

    if resp.status_code != 200:
        logger.error("Sarvam TTS API returned %s: %s", resp.status_code, resp.text)
        raise SarvamServiceError(f"Sarvam API error (status {resp.status_code})")

    try:
        result = resp.json()
        audio_b64 = "".join(result["audios"])
        return base64.b64decode(audio_b64)
    except (KeyError, ValueError) as exc:
        logger.exception("Unexpected Sarvam TTS response shape")
        raise SarvamServiceError("Unexpected response from Sarvam API") from exc
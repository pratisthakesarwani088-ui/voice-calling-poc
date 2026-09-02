"""Reusable service for calling the Sarvam Speech-to-Text API."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"


class SarvamServiceError(Exception):
    """Raised when the Sarvam API call fails or returns an unusable response."""


async def transcribe_audio(file_bytes: bytes, filename: str, content_type: str) -> str:
    """Send audio bytes to Sarvam STT and return the transcribed text."""
    if not settings.SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY is not configured")
        raise SarvamServiceError("Sarvam API key is not configured")

    headers = {"api-subscription-key": settings.SARVAM_API_KEY}
    files = {"file": (filename, file_bytes, content_type)}
    data = {"model": "saarika:v2"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(SARVAM_STT_URL, headers=headers, files=files, data=data)
    except httpx.RequestError as exc:
        logger.exception("Network error calling Sarvam API")
        raise SarvamServiceError("Failed to reach Sarvam API") from exc

    if resp.status_code != 200:
        logger.error("Sarvam API returned %s: %s", resp.status_code, resp.text)
        raise SarvamServiceError(f"Sarvam API error (status {resp.status_code})")

    try:
        result = resp.json()
        return result["transcript"]
    except (KeyError, ValueError) as exc:
        logger.exception("Unexpected Sarvam API response shape")
        raise SarvamServiceError("Unexpected response from Sarvam API") from exc

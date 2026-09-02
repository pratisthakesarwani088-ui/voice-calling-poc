"""Reusable service for calling the Gemini API."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={api_key}"
)


class GeminiServiceError(Exception):
    """Raised when the Gemini API call fails or returns an unusable response."""


async def generate_response(message: str, model: str = "gemini-3.6-flash") -> str:
    """Send a single text message to Gemini and return the generated reply."""
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not configured")
        raise GeminiServiceError("Gemini API key is not configured")

    url = GEMINI_URL_TEMPLATE.format(model=model, api_key=settings.GEMINI_API_KEY)
    payload = {"contents": [{"parts": [{"text": message}]}]}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        logger.exception("Network error calling Gemini API")
        raise GeminiServiceError("Failed to reach Gemini API") from exc

    if resp.status_code != 200:
        logger.error("Gemini API returned %s: %s", resp.status_code, resp.text)
        raise GeminiServiceError(f"Gemini API error (status {resp.status_code})")

    try:
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError) as exc:
        logger.exception("Unexpected Gemini API response shape")
        raise GeminiServiceError("Unexpected response from Gemini API") from exc

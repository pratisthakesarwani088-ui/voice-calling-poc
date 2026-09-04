"""
Application configuration.
Loads settings from environment variables (.env file in local dev).
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()


def _clean_env(key: str, default: str = "") -> str:
    """Read an env var and strip whitespace + any non-ASCII characters.

    Pasted secrets sometimes carry invisible characters (smart quotes,
    non-breaking spaces, zero-width chars) that crash HTTP header encoding.
    This keeps a bad paste from taking down the whole request.
    """
    raw = os.getenv(key, default)
    return raw.strip().encode("ascii", "ignore").decode("ascii")


class Settings:
    APP_NAME: str = _clean_env("APP_NAME", "AI Voice Calling POC")
    ENV: str = _clean_env("ENV", "development")
    LOG_LEVEL: str = _clean_env("LOG_LEVEL", "INFO")
    HOST: str = _clean_env("HOST", "0.0.0.0")
    PORT: int = int(_clean_env("PORT", "8000"))
    GEMINI_API_KEY: str = _clean_env("GEMINI_API_KEY")
    SARVAM_API_KEY: str = _clean_env("SARVAM_API_KEY")
    SARVAM_TTS_LANGUAGE: str = _clean_env("SARVAM_TTS_LANGUAGE", "hi-IN")
    SARVAM_TTS_SPEAKER: str = _clean_env("SARVAM_TTS_SPEAKER", "shubh")
    TWILIO_ACCOUNT_SID: str = _clean_env("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = _clean_env("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = _clean_env("TWILIO_PHONE_NUMBER")
    PUBLIC_BASE_URL: str = _clean_env("PUBLIC_BASE_URL")


settings = Settings()


def configure_logging() -> None:
    """Set up basic application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
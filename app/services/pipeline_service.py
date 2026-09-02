"""
Orchestrates the voice pipeline: Sarvam STT -> Gemini -> ElevenLabs TTS.
Reuses existing service modules only; no provider logic is duplicated here.
"""
import logging

from app.services.elevenlabs_service import ElevenLabsServiceError, synthesize_speech
from app.services.gemini_service import GeminiServiceError, generate_response
from app.services.sarvam_service import SarvamServiceError, transcribe_audio

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Raised when any stage of the voice pipeline fails."""


async def run_voice_pipeline(
    audio_bytes: bytes,
    filename: str,
    content_type: str,
    system_prompt: str | None = None,
    output_format: str = "mp3",
) -> tuple[bytes, str]:
    """Transcribe audio, generate a reply, and synthesize it back to speech.

    system_prompt: optional call context (e.g. from prompts.py) prepended
    before the transcript when talking to Gemini. Used by the live call
    stream; /voice-chat leaves this unset and behaves as before.
    output_format: passed through to ElevenLabs ("mp3" default, or
    "ulaw_8000" for the Twilio media stream).
    Returns (reply_audio_bytes, reply_text).
    """
    try:
        transcript = await transcribe_audio(audio_bytes, filename, content_type)
    except SarvamServiceError as exc:
        logger.error("Pipeline failed at STT stage: %s", exc)
        raise PipelineError("Speech-to-text stage failed") from exc

    if not transcript.strip():
        logger.error("Pipeline received an empty transcript from Sarvam")
        raise PipelineError("Speech-to-text produced no transcribable text")

    message = f"{system_prompt}\n\nCustomer said: {transcript}" if system_prompt else transcript

    try:
        reply_text = await generate_response(message)
    except GeminiServiceError as exc:
        logger.error("Pipeline failed at LLM stage: %s", exc)
        raise PipelineError("Response generation stage failed") from exc

    try:
        reply_audio = await synthesize_speech(reply_text, output_format=output_format)
    except ElevenLabsServiceError as exc:
        logger.error("Pipeline failed at TTS stage: %s", exc)
        raise PipelineError("Text-to-speech stage failed") from exc

    return reply_audio, reply_text

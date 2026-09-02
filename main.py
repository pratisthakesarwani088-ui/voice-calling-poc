"""
AI Voice Calling POC backend — entry point.

Wires together the health check, Gemini chat, Sarvam STT, ElevenLabs TTS,
the combined voice pipeline, and Twilio outbound calling + live media
stream routers into a single FastAPI app.
"""
import logging

from fastapi import FastAPI

from app.config import configure_logging, settings
from app.routers import (
    chat,
    health,
    make_call,
    speech_to_text,
    text_to_speech,
    twilio_webhook,
    voice_chat,
    voice_pipeline_stream,
)
from app.utils.exception_handlers import register_exception_handlers

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(speech_to_text.router)
app.include_router(text_to_speech.router)
app.include_router(voice_chat.router)
app.include_router(make_call.router)
app.include_router(twilio_webhook.router)
app.include_router(voice_pipeline_stream.router)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("%s starting up in '%s' mode", settings.APP_NAME, settings.ENV)

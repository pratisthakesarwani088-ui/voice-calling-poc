"""
Audio format helpers for the Twilio Media Streams bridge.

Twilio sends/expects raw 8kHz mu-law audio. The existing services expect a
WAV/MP3 container (Sarvam) or produce one (ElevenLabs). These helpers only
handle format conversion; they do not call any provider API.
"""
import audioop
import io
import wave
from typing import Iterator

SAMPLE_RATE = 8000
SAMPLE_WIDTH = 2  # 16-bit linear PCM
TWILIO_FRAME_BYTES = 160  # 20ms of 8kHz mu-law audio


def mulaw_to_wav(mulaw_bytes: bytes) -> bytes:
    """Wrap raw 8kHz mu-law audio into a mono 16-bit PCM WAV container."""
    pcm_bytes = audioop.ulaw2lin(mulaw_bytes, SAMPLE_WIDTH)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm_bytes)
    return buffer.getvalue()


def pcm16_rms(mulaw_bytes: bytes) -> int:
    """Return the RMS energy of a mu-law chunk, for simple silence detection."""
    pcm_bytes = audioop.ulaw2lin(mulaw_bytes, SAMPLE_WIDTH)
    return audioop.rms(pcm_bytes, SAMPLE_WIDTH)


def chunk_audio(data: bytes, chunk_size: int = TWILIO_FRAME_BYTES) -> Iterator[bytes]:
    """Split raw audio bytes into fixed-size frames for streaming back to Twilio."""
    for i in range(0, len(data), chunk_size):
        yield data[i : i + chunk_size]

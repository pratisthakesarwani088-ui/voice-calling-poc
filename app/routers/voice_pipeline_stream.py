"""
Twilio Media Streams WebSocket endpoint.

Receives the customer's live call audio, runs it through the existing
Sarvam -> Gemini -> ElevenLabs pipeline (via pipeline_service, reused as-is
aside from the optional prompt/output-format extensions added for this
module), and streams the AI's spoken reply back to Twilio. The conversation
loop continues until Twilio sends a "stop" event (call ended) or the socket
disconnects.

Turn-taking uses simple energy-based silence detection: once enough speech
has been buffered and is followed by a short run of silence, the buffered
utterance is sent through the pipeline. This is a minimal approach suitable
for a POC; it processes one utterance at a time rather than allowing
barge-in.
"""
import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.prompts import build_call_prompt
from app.services.pipeline_service import PipelineError, run_voice_pipeline
from app.utils.audio_conversion import chunk_audio, mulaw_to_wav, pcm16_rms

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-call"])

# Turn-taking thresholds (20ms frames at 8kHz mu-law).
SILENCE_RMS_THRESHOLD = 500
SILENCE_FRAMES_TO_TRIGGER = 25  # ~500ms of trailing silence
MIN_SPEECH_FRAMES = 10  # ~200ms of speech required before triggering


class _CallState:
    def __init__(self) -> None:
        self.stream_sid: str | None = None
        self.system_prompt: str | None = None
        self.audio_buffer = bytearray()
        self.speech_frames = 0
        self.silence_frames = 0


async def _send_audio(websocket: WebSocket, stream_sid: str, audio_bytes: bytes) -> None:
    for frame in chunk_audio(audio_bytes):
        payload = base64.b64encode(frame).decode("ascii")
        await websocket.send_text(
            json.dumps({"event": "media", "streamSid": stream_sid, "media": {"payload": payload}})
        )


async def _process_utterance(websocket: WebSocket, state: _CallState) -> None:
    mulaw_bytes = bytes(state.audio_buffer)
    state.audio_buffer.clear()
    state.speech_frames = 0
    state.silence_frames = 0

    if not mulaw_bytes or not state.stream_sid:
        return

    try:
        wav_bytes = mulaw_to_wav(mulaw_bytes)
        reply_audio, reply_text = await run_voice_pipeline(
            wav_bytes,
            "utterance.wav",
            "audio/wav",
            system_prompt=state.system_prompt,
            output_format="ulaw_8000",
        )
        logger.info("Call reply generated: %s", reply_text)
        await _send_audio(websocket, state.stream_sid, reply_audio)
    except PipelineError as exc:
        logger.error("Pipeline failed during live call turn: %s", exc)
    except Exception:
        logger.exception("Unexpected error while processing a call utterance")


@router.websocket("/voice-pipeline-stream")
async def voice_pipeline_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    state = _CallState()

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                data = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Received non-JSON message on media stream; ignoring")
                continue

            event = data.get("event")

            if event == "start":
                start = data.get("start", {})
                state.stream_sid = start.get("streamSid")
                params = start.get("customParameters", {}) or {}
                state.system_prompt = build_call_prompt(
                    params.get("customer_name", "the customer"),
                    params.get("product_name", "our product"),
                    params.get("product_details", ""),
                )
                logger.info("Media stream started: sid=%s params=%s", state.stream_sid, params)

            elif event == "media":
                if not state.stream_sid:
                    continue
                payload_b64 = data.get("media", {}).get("payload")
                if not payload_b64:
                    continue
                try:
                    mulaw_chunk = base64.b64decode(payload_b64)
                except (ValueError, TypeError):
                    logger.warning("Received malformed audio payload; skipping frame")
                    continue
                is_speech = pcm16_rms(mulaw_chunk) > SILENCE_RMS_THRESHOLD

                if is_speech:
                    state.speech_frames += 1
                    state.silence_frames = 0
                    state.audio_buffer.extend(mulaw_chunk)
                elif state.speech_frames > 0:
                    state.silence_frames += 1
                    state.audio_buffer.extend(mulaw_chunk)

                if (
                    state.speech_frames >= MIN_SPEECH_FRAMES
                    and state.silence_frames >= SILENCE_FRAMES_TO_TRIGGER
                ):
                    await _process_utterance(websocket, state)

            elif event == "stop":
                logger.info("Media stream stopped: sid=%s", state.stream_sid)
                break

    except WebSocketDisconnect:
        logger.info("Media stream websocket disconnected: sid=%s", state.stream_sid)
    except Exception:
        logger.exception("Unexpected error on media stream: sid=%s", state.stream_sid)

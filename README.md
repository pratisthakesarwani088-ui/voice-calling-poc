# AI Voice Calling POC — Backend

A backend proof-of-concept for an AI-driven outbound voice calling system.
It wires together speech-to-text, an LLM, text-to-speech, and outbound
telephony into a single conversational voice pipeline, exposed both as
REST endpoints (for testing each stage independently) and as a live
Twilio call flow.

## Project flow

```
POST /make-call  (customer_name, phone_number, product_name, product_details)
        │
        ▼
  Twilio places an outbound call, pointed at our webhook (no inline TwiML)
        │
        ▼
  POST /twilio/voice-webhook   — Twilio fetches TwiML once the call connects
        │  returns <Connect><Stream> pointing at our WebSocket,
        │  forwarding customer/product context as stream parameters
        ▼
  WS /voice-pipeline-stream    — live call audio bridge
        │
        │   customer speaks
        ▼
   Sarvam STT  →  Gemini (with prompts.build_call_prompt context)  →  ElevenLabs TTS
        │
        ▼
   AI's spoken reply streamed back to Twilio, in real time,
   until the call ends
```

Each stage of that pipeline is also exposed standalone for testing:
`/speech-to-text`, `/chat`, `/text-to-speech`, and the combined
non-streaming `/voice-chat` (upload a recording, get a spoken reply back).

## Project structure

```
app/
  config.py                     # env-based settings + logging setup
  prompts.py                    # builds the AI call prompt from customer/product data
  routers/
    health.py                   # GET /health
    chat.py                     # POST /chat            (Gemini)
    speech_to_text.py           # POST /speech-to-text   (Sarvam)
    text_to_speech.py           # POST /text-to-speech   (ElevenLabs)
    voice_chat.py                # POST /voice-chat       (STT -> Gemini -> TTS, one-shot)
    make_call.py                 # POST /make-call        (places outbound Twilio call)
    twilio_webhook.py           # POST /twilio/voice-webhook (Twilio call-connect callback)
    voice_pipeline_stream.py    # WS   /voice-pipeline-stream (live call audio bridge)
  services/
    gemini_service.py           # Gemini API client
    sarvam_service.py           # Sarvam STT API client
    elevenlabs_service.py       # ElevenLabs TTS API client
    pipeline_service.py         # orchestrates STT -> Gemini -> TTS
    twilio_service.py           # places outbound calls via Twilio's REST API
  utils/
    exception_handlers.py       # global unhandled-exception handler
    audio_conversion.py         # mu-law/WAV conversion + framing for Twilio streams
main.py                         # FastAPI app entry point, router registration
requirements.txt
.env.example
```

## Setup

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your own credentials (see table below). `PUBLIC_BASE_URL`
must be a publicly reachable HTTPS URL (e.g. an ngrok tunnel in local dev) —
Twilio needs to be able to reach `/twilio/voice-webhook` and
`/voice-pipeline-stream` on it.

## Environment variables

| Variable                | Used by            | Notes                                      |
|--------------------------|---------------------|---------------------------------------------|
| `APP_NAME`               | app config          | optional, defaults to "AI Voice Calling POC" |
| `ENV`                    | app config          | optional, defaults to "development"          |
| `LOG_LEVEL`               | logging             | optional, defaults to "INFO"                 |
| `HOST` / `PORT`           | local run           | optional, defaults to 0.0.0.0:8000           |
| `GEMINI_API_KEY`          | Gemini (chat, pipeline) | required for `/chat`, `/voice-chat`, calls |
| `SARVAM_API_KEY`          | Sarvam STT          | required for `/speech-to-text`, `/voice-chat`, calls |
| `ELEVENLABS_API_KEY`      | ElevenLabs TTS      | required for `/text-to-speech`, `/voice-chat`, calls |
| `ELEVENLABS_VOICE_ID`     | ElevenLabs TTS      | the voice to synthesize with                 |
| `TWILIO_ACCOUNT_SID`      | Twilio              | required for `/make-call`                    |
| `TWILIO_AUTH_TOKEN`       | Twilio              | required for `/make-call`                    |
| `TWILIO_PHONE_NUMBER`     | Twilio              | the number calls are placed from (E.164)     |
| `PUBLIC_BASE_URL`         | Twilio webhook/stream | publicly reachable base URL of this service |

## Run

```bash
uvicorn main:app --reload
```

## API endpoints

| Method | Path                     | Description                                              |
|--------|---------------------------|------------------------------------------------------------|
| GET    | `/health`                 | Liveness check → `{"status": "ok"}`                       |
| POST   | `/chat`                   | `{"message": "..."}` → `{"response": "..."}` (Gemini)      |
| POST   | `/speech-to-text`          | Upload WAV/MP3 → `{"text": "..."}` (Sarvam)                |
| POST   | `/text-to-speech`          | `{"text": "..."}` → MP3 audio (ElevenLabs)                 |
| POST   | `/voice-chat`               | Upload WAV/MP3 → MP3 reply (Sarvam → Gemini → ElevenLabs)  |
| POST   | `/make-call`                 | Places an outbound call (see request body below)           |
| POST   | `/twilio/voice-webhook`    | Twilio-facing callback; returns TwiML (not called directly) |
| WS     | `/voice-pipeline-stream`   | Twilio Media Streams bridge (not called directly)           |

`/make-call` request body:
```json
{
  "customer_name": "Rahul",
  "phone_number": "+91XXXXXXXXXX",
  "product_name": "Home Loan",
  "product_details": "8.25% interest, Low EMI, Quick Approval"
}
```

Interactive API docs: `http://localhost:8000/docs`

## Notes

- No database is used; per-call context is passed through as Twilio stream/query
  parameters rather than persisted.
- The live call turn-taking uses simple energy-based silence detection
  (see `voice_pipeline_stream.py`); it processes one utterance at a time and
  does not support barge-in.

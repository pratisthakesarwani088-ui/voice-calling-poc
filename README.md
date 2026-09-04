# AI Voice Calling POC – Backend

A FastAPI backend for an AI-powered outbound voice calling system using **Twilio, Sarvam AI (STT + TTS), and Google Gemini**.

## Architecture

```text
Customer
   │
   ▼
Twilio Voice
   │
   ▼
Voice Webhook
   │
   ▼
Voice Stream
   │
   ▼
Sarvam Speech-to-Text (STT)
   │
   ▼
Google Gemini
   │
   ▼
Sarvam Text-to-Speech (TTS)
   │
   ▼
Twilio Voice
   │
   ▼
Customer
```

## Features

- AI-powered outbound voice calling
- Sarvam Speech-to-Text (STT)
- Google Gemini AI conversation
- Sarvam Text-to-Speech (TTS)
- Twilio Voice integration
- REST APIs for independent testing
- Real-time voice streaming pipeline

## Tech Stack

- **Backend:** FastAPI
- **Speech-to-Text:** Sarvam AI
- **LLM:** Google Gemini
- **Text-to-Speech:** Sarvam AI
- **Telephony:** Twilio Voice API
- **HTTP Client:** HTTPX
- **Deployment:** Render

## Environment Variables

- `GEMINI_API_KEY`
- `SARVAM_API_KEY`
- `SARVAM_TTS_LANGUAGE`
- `SARVAM_TTS_SPEAKER`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `PUBLIC_BASE_URL`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health Check |
| POST | `/chat` | Gemini AI Chat |
| POST | `/speech-to-text` | Sarvam STT |
| POST | `/text-to-speech` | Sarvam TTS |
| POST | `/voice-chat` | STT → Gemini → TTS |
| POST | `/make-call` | Outbound AI Call |
| POST | `/twilio/voice-webhook` | Twilio Webhook |
| WS | `/voice-pipeline-stream` | Live Voice Pipeline |

## Run

```bash
uvicorn main:app --reload
```

Swagger UI:

```text
http://localhost:8000/docs
```

## Notes

- No database is used.
- Customer context is passed through Twilio stream parameters.
- End-to-end pipeline: **Twilio → Sarvam STT → Gemini → Sarvam TTS → Twilio**.
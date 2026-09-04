# AI Voice Calling POC – Backend

A FastAPI-based backend for an AI-powered outbound voice calling system using **Twilio, Sarvam AI, and Gemini**.

## Architecture

```
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
Sarvam STT
   │
   ▼
Gemini LLM
   │
   ▼
Sarvam TTS
   │
   ▼
Twilio
   │
   ▼
Customer
```

## Features

- AI-powered outbound voice calling
- Speech-to-Text (Sarvam)
- AI conversation (Gemini)
- Text-to-Speech (Sarvam)
- Twilio Voice integration
- REST APIs for independent testing
- Live voice streaming pipeline

## Project Structure

```
app/
├── config.py
├── prompts.py
├── routers/
│   ├── health.py
│   ├── chat.py
│   ├── speech_to_text.py
│   ├── text_to_speech.py
│   ├── voice_chat.py
│   ├── make_call.py
│   ├── twilio_webhook.py
│   └── voice_pipeline_stream.py
├── services/
│   ├── gemini_service.py
│   ├── sarvam_service.py
│   ├── pipeline_service.py
│   └── twilio_service.py
└── utils/
    ├── audio_conversion.py
    └── exception_handlers.py

main.py
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

Configure the required API keys in `.env`.

## Run

```bash
uvicorn main:app --reload
```

## Environment Variables

- GEMINI_API_KEY
- SARVAM_API_KEY
- TWILIO_ACCOUNT_SID
- TWILIO_AUTH_TOKEN
- TWILIO_PHONE_NUMBER
- PUBLIC_BASE_URL

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health Check |
| POST | `/chat` | Gemini Chat |
| POST | `/speech-to-text` | Speech → Text |
| POST | `/text-to-speech` | Text → Speech |
| POST | `/voice-chat` | STT → Gemini → TTS |
| POST | `/make-call` | Outbound AI Call |
| POST | `/twilio/voice-webhook` | Twilio Webhook |
| WS | `/voice-pipeline-stream` | Live Voice Stream |

Swagger Docs:

```
http://localhost:8000/docs
```

## Tech Stack

- FastAPI
- Twilio Voice API
- Sarvam Speech-to-Text
- Sarvam Text-to-Speech
- Google Gemini
- HTTPX
- Render

## Notes

- No database is used.
- Customer context is passed through Twilio stream parameters.
- Live conversation uses streaming audio with STT → Gemini → TTS pipeline.
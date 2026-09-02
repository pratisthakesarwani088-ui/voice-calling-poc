"""Chat endpoint backed by the Gemini API."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.gemini_service import GeminiServiceError, generate_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = await generate_response(request.message)
        return ChatResponse(response=reply)
    except GeminiServiceError as exc:
        logger.error("Chat request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Failed to get a response from Gemini") from exc

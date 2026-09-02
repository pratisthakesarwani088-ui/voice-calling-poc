"""Outbound call trigger endpoint backed by Twilio.

The call is connected to the live voice pipeline via a webhook + media
stream (see twilio_webhook.py and voice_pipeline_stream.py).
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.services.twilio_service import TwilioServiceError, initiate_call

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-call"])

PHONE_REGEX = r"^\+[1-9]\d{6,14}$"


class MakeCallRequest(BaseModel):
    customer_name: str = Field(..., min_length=1)
    phone_number: str = Field(..., pattern=PHONE_REGEX)
    product_name: str = Field(..., min_length=1)
    product_details: str = Field(..., min_length=1)

    @field_validator("customer_name", "product_name", "product_details")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value


class MakeCallResponse(BaseModel):
    call_sid: str
    status: str


@router.post("/make-call", response_model=MakeCallResponse)
async def make_call(request: MakeCallRequest) -> MakeCallResponse:
    try:
        call_sid = await initiate_call(
            request.phone_number,
            request.customer_name,
            request.product_name,
            request.product_details,
        )
        return MakeCallResponse(call_sid=call_sid, status="initiated")
    except TwilioServiceError as exc:
        logger.error("Make-call request failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
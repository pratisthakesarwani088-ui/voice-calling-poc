"""
Reusable service for placing outbound Twilio calls.

The call is pointed at our own webhook URL (Twilio's `Url` param) rather than
inline TwiML. When the call connects, Twilio fetches TwiML from that webhook
(see twilio_webhook.py) which connects the call's media to the live voice
pipeline over /voice-pipeline-stream.
"""
import logging
from urllib.parse import urlencode

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TWILIO_CALLS_URL_TEMPLATE = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json"


class TwilioServiceError(Exception):
    """Raised when building the webhook URL or placing the call fails."""


def build_webhook_url(customer_name: str, product_name: str, product_details: str) -> str:
    """Build the callback URL Twilio will fetch TwiML from once the call connects."""
    if not settings.PUBLIC_BASE_URL:
        logger.error("PUBLIC_BASE_URL is not configured")
        raise TwilioServiceError("Public base URL is not configured")

    query = urlencode(
        {
            "customer_name": customer_name,
            "product_name": product_name,
            "product_details": product_details,
        }
    )
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/twilio/voice-webhook?{query}"


async def initiate_call(phone_number: str, customer_name: str, product_name: str, product_details: str) -> str:
    """Place an outbound call via Twilio, pointed at our voice-webhook, and return the call SID."""
    if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER):
        logger.error("Twilio credentials are not fully configured")
        raise TwilioServiceError("Twilio credentials are not configured")

    webhook_url = build_webhook_url(customer_name, product_name, product_details)
    url = TWILIO_CALLS_URL_TEMPLATE.format(account_sid=settings.TWILIO_ACCOUNT_SID)
    data = {
        "To": phone_number,
        "From": settings.TWILIO_PHONE_NUMBER,
        "Url": webhook_url,
        "Method": "POST",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                data=data,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            )
    except httpx.RequestError as exc:
        logger.exception("Network error calling Twilio API")
        raise TwilioServiceError("Failed to reach Twilio API") from exc

    if resp.status_code not in (200, 201):
        logger.error("Twilio API returned %s: %s", resp.status_code, resp.text)
        raise TwilioServiceError(f"Twilio API error (status {resp.status_code})")

    try:
        return resp.json()["sid"]
    except (KeyError, ValueError) as exc:
        logger.exception("Unexpected Twilio API response shape")
        raise TwilioServiceError("Unexpected response from Twilio API") from exc

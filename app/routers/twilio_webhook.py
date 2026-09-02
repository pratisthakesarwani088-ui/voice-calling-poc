"""
Twilio calls this webhook once an outbound call connects. It returns TwiML
that connects the call's media to the live voice pipeline
(/voice-pipeline-stream), forwarding the customer/product context along as
stream parameters.
"""
import logging
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from fastapi import APIRouter, Query, Response

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["voice-call"])


def _stream_url() -> str | None:
    if not settings.PUBLIC_BASE_URL:
        return None
    parsed = urlparse(settings.PUBLIC_BASE_URL)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    host = parsed.netloc or parsed.path
    return f"{scheme}://{host}/voice-pipeline-stream"


@router.post("/twilio/voice-webhook")
async def voice_webhook(
    customer_name: str = Query(...),
    product_name: str = Query(...),
    product_details: str = Query(...),
) -> Response:
    logger.info("Voice webhook triggered for customer '%s' (%s)", customer_name, product_name)

    stream_url = _stream_url()
    if not stream_url:
        logger.error("PUBLIC_BASE_URL is not configured; cannot connect call to voice pipeline")
        twiml = "<Response><Say>Sorry, the assistant is unavailable right now.</Say><Hangup/></Response>"
        return Response(content=twiml, media_type="application/xml")

    twiml = (
        "<Response>"
        "<Connect>"
        f'<Stream url="{escape(stream_url)}">'
        f'<Parameter name="customer_name" value="{escape(customer_name)}"/>'
        f'<Parameter name="product_name" value="{escape(product_name)}"/>'
        f'<Parameter name="product_details" value="{escape(product_details)}"/>'
        "</Stream>"
        "</Connect>"
        "</Response>"
    )
    return Response(content=twiml, media_type="application/xml")

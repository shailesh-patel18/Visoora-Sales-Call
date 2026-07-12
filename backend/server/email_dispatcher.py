"""
Email Dispatch Engine for Visoora.

Picks up approved email drafts from the job queue and sends them via SendGrid.
Tracks the SendGrid message_id for future reply/bounce webhook handling.
"""
import os
import structlog
from typing import Dict, Any
from server.worker import register_job_handler

logger = structlog.get_logger("visoora_email_dispatcher")

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")


async def send_email_via_sendgrid(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Sends a single email via the SendGrid v3 API.
    Returns the response status code and message_id headers.
    """
    if not SENDGRID_API_KEY:
        raise RuntimeError(
            "SENDGRID_API_KEY is not configured. Cannot dispatch emails."
        )

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content

    message = Mail(
        from_email=Email(from_email),
        to_emails=To(to_email),
        subject=subject,
        plain_text_content=Content("text/plain", body),
    )

    # Add custom tracking headers for Visoora
    message.header = {
        "X-Visoora-Tenant": tenant_id,
    }

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)

    # Extract the message ID from SendGrid's response headers
    message_id = ""
    if hasattr(response, "headers"):
        message_id = response.headers.get("X-Message-Id", "")

    logger.info(
        "email_sent_sendgrid",
        to_email=to_email,
        subject=subject,
        status_code=response.status_code,
        message_id=message_id,
        tenant_id=tenant_id,
    )

    return {
        "status_code": response.status_code,
        "message_id": message_id,
    }


async def email_dispatch_handler(payload: dict, **kwargs) -> dict:
    """
    Background job handler registered with the Visoora worker system.
    
    Expected payload:
        - tenant_id: str
        - draft_id: str (optional, for v2 draft tracking)
        - to_email: str
        - subject: str
        - body: str
        - from_email: str (optional, falls back to SENDGRID_FROM_EMAIL)
    """
    tenant_id = payload.get("tenant_id")
    draft_id = payload.get("draft_id")
    to_email = payload.get("to_email")
    subject = payload.get("subject")
    body = payload.get("body")
    from_email = payload.get("from_email") or SENDGRID_FROM_EMAIL

    if not tenant_id:
        raise ValueError("Missing required parameter: 'tenant_id'")
    if not to_email:
        raise ValueError("Missing required parameter: 'to_email'")
    if not subject or not body:
        raise ValueError("Missing required parameters: 'subject' and 'body'")

    logger.info(
        "email_dispatch_job_start",
        tenant_id=tenant_id,
        draft_id=draft_id,
        to_email=to_email,
    )

    try:
        result = await send_email_via_sendgrid(
            to_email=to_email,
            from_email=from_email,
            subject=subject,
            body=body,
            tenant_id=tenant_id,
        )

        # Update draft status to 'sent' if we have a draft_id
        if draft_id:
            try:
                from v2.domain.crm.repository import draft_repository
                from v2.domain.crm.models import DraftStatus

                draft = await draft_repository.get(draft_id)
                if draft:
                    draft.status = DraftStatus.SENT
                    draft.metadata = draft.metadata if hasattr(draft, 'metadata') else {}
                    await draft_repository.save(draft)
                    logger.info("draft_status_updated", draft_id=draft_id, status="sent")
            except Exception as draft_err:
                logger.warn("draft_status_update_failed", draft_id=draft_id, error=str(draft_err))

        return {
            "status": "sent",
            "message_id": result.get("message_id", ""),
            "draft_id": draft_id,
        }

    except Exception as send_err:
        logger.error(
            "email_dispatch_failed",
            tenant_id=tenant_id,
            draft_id=draft_id,
            to_email=to_email,
            error=str(send_err),
        )

        # Mark draft as send_failed
        if draft_id:
            try:
                from v2.domain.crm.repository import draft_repository
                from v2.domain.crm.models import DraftStatus

                draft = await draft_repository.get(draft_id)
                if draft:
                    draft.status = DraftStatus.SEND_FAILED
                    await draft_repository.save(draft)
            except Exception:
                pass

        raise send_err


# Register with the Visoora background worker system
register_job_handler("email_dispatch", email_dispatch_handler)

import resend
from typing import Dict, Any
from .base_notification import NotificationProvider
from security.config import settings
import structlog

logger = structlog.get_logger("visoora_resend")

class ResendProvider(NotificationProvider):
    def __init__(self):
        resend.api_key = settings.resend_api_key
        import os
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "notifications@visoora.com")
        
    async def notify(self, user_id: str, recipient: str, template: str, data: Dict[str, Any]) -> bool:
        """
        Sends an email using Resend.
        In a real application, we would map 'template' to a specific React Email template or HTML string.
        """
        subject = data.get("subject", "Visoora Notification")
        html_content = data.get("html", "<p>You have a new notification from Visoora.</p>")
        
        try:
            r = resend.Emails.send({
                "from": self.from_email,
                "to": recipient,
                "subject": subject,
                "html": html_content
            })
            logger.info("resend_email_sent", user_id=user_id, recipient=recipient, resend_id=r.get("id"))
            return True
        except Exception as e:
            error_msg = str(e)
            if "validation_error" in error_msg.lower() or "not authorized" in error_msg.lower() or "domain" in error_msg.lower():
                logger.error(
                    "resend_email_domain_verification_error",
                    error=error_msg,
                    user_id=user_id,
                    recipient=recipient,
                    hint="Ensure your RESEND_FROM_EMAIL domain is verified in the Resend dashboard, or use onboarding@resend.dev to send to your verified email address."
                )
            else:
                logger.error("resend_email_failed", error=error_msg, user_id=user_id, recipient=recipient)
            return False

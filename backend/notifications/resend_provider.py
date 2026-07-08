import resend
from typing import Dict, Any
from .base_notification import NotificationProvider
from security.config import settings
import structlog

logger = structlog.get_logger("visoora_resend")

class ResendProvider(NotificationProvider):
    def __init__(self):
        resend.api_key = settings.resend_api_key
        self.from_email = "notifications@visoora.com" # Should be configured via env
        
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
            logger.error("resend_email_failed", error=str(e), user_id=user_id, recipient=recipient)
            return False

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class NotificationProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_body: str):
        pass

class ResendProvider(NotificationProvider):
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        # Normally we'd import resend here
        
    def send_email(self, to_email: str, subject: str, html_body: str):
        if not self.api_key:
            logger.info(f"--- MOCK RESEND EMAIL ---")
            logger.info(f"To: {to_email}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {html_body[:200]}...")
            logger.info(f"-------------------------")
            return
            
        try:
            import resend
            resend.api_key = self.api_key
            r = resend.Emails.send({
                "from": "Acme <onboarding@resend.dev>",
                "to": to_email,
                "subject": subject,
                "html": html_body
            })
            logger.info(f"Sent email via Resend to {to_email}")
        except Exception as e:
            logger.error(f"Resend error: {e}")

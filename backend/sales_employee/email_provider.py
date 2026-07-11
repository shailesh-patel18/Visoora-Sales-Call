import abc
import os
import uuid
import math
import time
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, Optional, List
import httpx
import structlog

logger = structlog.get_logger("visoora_email_provider")

class EmailProviderInterface(abc.ABC):
    @abc.abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Sends an email using the provider configuration.
        Returns a dict with 'message_id' and 'status' (sent, failed).
        """
        pass

class GmailOAuthProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        # Gmail OAuth API endpoint. Real integration would use the access token.
        token = connection_config.get("access_token", "mock_access_token")
        
        # Simulating API request to Google Mail API.
        # Check if the token is expired/revoked to raise exception for retries
        if "invalid" in token or "expired" in token:
            raise RuntimeError("Gmail credentials invalid or expired (401 Unauthorized)")
            
        msg_id = f"<{uuid.uuid4()}@gmail.com>"
        logger.info("gmail_oauth_send_mock", to=to_email, from_addr=from_email, msg_id=msg_id, headers=extra_headers)
        
        return {
            "provider": "gmail",
            "message_id": msg_id,
            "status": "sent",
            "details": {"mocked": True}
        }

class OutlookOAuthProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        token = connection_config.get("access_token", "mock_access_token")
        if "invalid" in token or "expired" in token:
            raise RuntimeError("Outlook credentials invalid or expired (401 Unauthorized)")
            
        msg_id = f"<{uuid.uuid4()}@outlook.com>"
        logger.info("outlook_oauth_send_mock", to=to_email, from_addr=from_email, msg_id=msg_id, headers=extra_headers)
        return {
            "provider": "outlook",
            "message_id": msg_id,
            "status": "sent",
            "details": {"mocked": True}
        }

class SMTPProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        host = connection_config.get("host")
        port = int(connection_config.get("port", 587))
        username = connection_config.get("username", from_email)
        password = connection_config.get("password", "")
        use_ssl = connection_config.get("use_ssl", False)
        
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        
        new_msg_id = f"<{uuid.uuid4()}@{from_email.split('@')[-1]}>"
        msg["Message-ID"] = new_msg_id
        
        if prev_msg_id:
            msg["In-Reply-To"] = prev_msg_id
            msg["References"] = prev_msg_id
            
        # Append unsubscribe and custom headers
        for k, v in (extra_headers or {}).items():
            msg[k] = v
            
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # Test mode mock check to prevent running network code in unit tests
        if os.getenv("APP_ENV") in ("development", "test") or host == "mock_smtp":
            # Simulate failure if credentials indicate so
            if "invalid" in password or "expired" in password:
                raise RuntimeError("SMTP connection failed: 535 Authentication Failed")
            logger.info("smtp_send_mock", host=host, port=port, to=to_email, msg_id=new_msg_id, headers=extra_headers)
            return {"provider": "smtp", "message_id": new_msg_id, "status": "sent", "details": {"mocked": True}}
            
        # Run blocking network socket logic inside an asyncio thread pool executor
        def _sync_smtp_send():
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=10.0)
            else:
                server = smtplib.SMTP(host, port, timeout=10.0)
                server.starttls()
                
            server.login(username, password)
            server.sendmail(from_email, [to_email], msg.as_string())
            server.quit()
            
        try:
            await asyncio.to_thread(_sync_smtp_send)
            logger.info("smtp_send_success", to=to_email, msg_id=new_msg_id)
            return {"provider": "smtp", "message_id": new_msg_id, "status": "sent"}
        except Exception as exc:
            logger.error("smtp_send_failed", error=str(exc))
            raise RuntimeError(f"SMTP sending failed: {exc}")

class SendGridProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        api_key = connection_config.get("api_key", os.getenv("SENDGRID_API_KEY", ""))
        
        headers = {}
        if prev_msg_id:
            headers["In-Reply-To"] = prev_msg_id
            headers["References"] = prev_msg_id
        if extra_headers:
            headers.update(extra_headers)

        if os.getenv("APP_ENV") in ("development", "test") or api_key == "mock":
            if "invalid" in api_key or "expired" in api_key:
                raise RuntimeError("SendGrid authentication failed (Invalid API Key)")
            new_msg_id = f"sg_mock_{uuid.uuid4()}"
            logger.info("sendgrid_send_mock", to=to_email, from_addr=from_email, msg_id=new_msg_id, headers=headers)
            return {"provider": "sendgrid", "message_id": new_msg_id, "status": "sent", "details": {"mocked": True}}

        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            }
            if headers:
                payload["headers"] = headers
                
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code >= 300:
                raise RuntimeError(f"SendGrid send failed with {response.status_code}: {response.text[:300]}")
            return {
                "provider": "sendgrid",
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id", f"sg_{uuid.uuid4()}"),
                "status": "sent"
            }

class ResendProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        api_key = connection_config.get("api_key", "")
        
        headers = {}
        if prev_msg_id:
            headers["In-Reply-To"] = prev_msg_id
            headers["References"] = prev_msg_id
        if extra_headers:
            headers.update(extra_headers)

        if os.getenv("APP_ENV") in ("development", "test") or api_key == "mock":
            if "invalid" in api_key or "expired" in api_key:
                raise RuntimeError("Resend authentication failed (Invalid API Key)")
            new_msg_id = f"re_mock_{uuid.uuid4()}"
            logger.info("resend_send_mock", to=to_email, from_addr=from_email, msg_id=new_msg_id, headers=headers)
            return {"provider": "resend", "message_id": new_msg_id, "status": "sent", "details": {"mocked": True}}

        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "text": body,
            }
            if headers:
                payload["headers"] = headers
                
            response = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code >= 300:
                raise RuntimeError(f"Resend send failed with {response.status_code}: {response.text[:300]}")
            data = response.json()
            return {
                "provider": "resend",
                "message_id": data.get("id", f"re_{uuid.uuid4()}"),
                "status": "sent"
            }

class SESProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        msg_id = f"ses_mock_{uuid.uuid4()}"
        logger.info("ses_send_mock", to=to_email, from_addr=from_email, msg_id=msg_id, headers=extra_headers)
        return {
            "provider": "ses",
            "message_id": msg_id,
            "status": "sent",
            "details": {"mocked": True}
        }

class PostmarkProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        api_key = connection_config.get("api_key", "")
        
        headers = []
        if prev_msg_id:
            headers.append({"Name": "In-Reply-To", "Value": prev_msg_id})
            headers.append({"Name": "References", "Value": prev_msg_id})
        for k, v in (extra_headers or {}).items():
            headers.append({"Name": k, "Value": v})

        if os.getenv("APP_ENV") in ("development", "test") or api_key == "mock":
            if "invalid" in api_key or "expired" in api_key:
                raise RuntimeError("Postmark authentication failed (Invalid API Key)")
            new_msg_id = f"pm_mock_{uuid.uuid4()}"
            logger.info("postmark_send_mock", to=to_email, from_addr=from_email, msg_id=new_msg_id, headers=headers)
            return {"provider": "postmark", "message_id": new_msg_id, "status": "sent", "details": {"mocked": True}}

        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "From": from_email,
                "To": to_email,
                "Subject": subject,
                "TextBody": body,
            }
            if headers:
                payload["Headers"] = headers
                
            response = await client.post(
                "https://api.postmarkapp.com/email",
                headers={"X-Postmark-Server-Token": api_key, "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code >= 300:
                raise RuntimeError(f"Postmark send failed with {response.status_code}: {response.text[:300]}")
            data = response.json()
            return {
                "provider": "postmark",
                "message_id": data.get("MessageID", f"pm_{uuid.uuid4()}"),
                "status": "sent"
            }

class NylasProvider(EmailProviderInterface):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: str,
        connection_config: Dict[str, Any],
        prev_msg_id: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        api_key = connection_config.get("api_key", os.getenv("NYLAS_API_KEY", ""))
        grant_id = connection_config.get("grant_id", "")
        
        if os.getenv("APP_ENV") in ("development", "test") or api_key == "mock":
            if "invalid" in api_key or "expired" in api_key:
                raise RuntimeError("Nylas authentication failed (Invalid API Key)")
            new_msg_id = f"nylas_mock_{uuid.uuid4()}"
            logger.info("nylas_send_mock", to=to_email, from_addr=from_email, grant_id=grant_id, msg_id=new_msg_id)
            return {"provider": "nylas", "message_id": new_msg_id, "status": "sent", "details": {"mocked": True}}

        if not grant_id:
            raise ValueError("NylasProvider requires a 'grant_id' in the connection_config.")

        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "subject": subject,
                "body": body,
                "to": [{"email": to_email}],
                "reply_to": [{"email": from_email}]
            }
            if prev_msg_id:
                payload["reply_to_message_id"] = prev_msg_id
                
            response = await client.post(
                f"https://api.us.nylas.com/v3/grants/{grant_id}/messages/send",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            if response.status_code >= 300:
                raise RuntimeError(f"Nylas send failed with {response.status_code}: {response.text[:300]}")
            data = response.json()
            return {
                "provider": "nylas",
                "message_id": data.get("data", {}).get("id", f"ny_{uuid.uuid4()}"),
                "status": "sent"
            }

# Mapping registry of email providers
PROVIDERS: Dict[str, EmailProviderInterface] = {
    "gmail": GmailOAuthProvider(),
    "outlook": OutlookOAuthProvider(),
    "smtp": SMTPProvider(),
    "sendgrid": SendGridProvider(),
    "resend": ResendProvider(),
    "ses": SESProvider(),
    "postmark": PostmarkProvider(),
    "nylas": NylasProvider()
}

async def send_via_mailbox(
    mailbox: Dict[str, Any],
    to_email: str,
    subject: str,
    body: str,
    prev_msg_id: Optional[str] = None,
    extra_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Router method to fetch the correct EmailProviderInterface and dispatch the email.
    """
    provider_name = mailbox.get("provider", "smtp").lower()
    provider = PROVIDERS.get(provider_name)
    if not provider:
        raise ValueError(f"Unsupported email provider: {provider_name}")
        
    from_email = mailbox.get("email")
    
    # Decrypt config logic before passing
    from security.encryption import decrypt_value
    import json
    
    encrypted_config = mailbox.get("connection_config", "")
    try:
        connection_config = json.loads(decrypt_value(encrypted_config))
    except Exception:
        try:
            connection_config = json.loads(encrypted_config)
        except Exception:
            connection_config = {}
            
    return await provider.send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        from_email=from_email,
        connection_config=connection_config,
        prev_msg_id=prev_msg_id,
        extra_headers=extra_headers
    )

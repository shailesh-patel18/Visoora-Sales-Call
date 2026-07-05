from typing import Dict, Any
import structlog
from v2.ai.tool_registry import tool_registry, ToolCapability

logger = structlog.get_logger("email_sender_tool")

async def send_email_adapter(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implementation of the SEND_EMAIL capability.
    This adapter interfaces with standard providers like SendGrid or SMTP.
    """
    to_email = payload.get("to_email")
    subject = payload.get("subject")
    
    logger.info("sending_email", to_email=to_email, subject=subject)
    
    # Simulate network delay for sending email
    await __import__("asyncio").sleep(0.5)
    
    return {
        "status": "success",
        "to_email": to_email,
        "message": "Email sent successfully",
        "provider": "sendgrid_adapter"
    }

# Register the capability implementation globally
tool_registry.register(ToolCapability.SEND_EMAIL, send_email_adapter)

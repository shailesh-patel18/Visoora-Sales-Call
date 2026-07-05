import os
import logging
from .provider import ResendProvider

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self, provider):
        self.provider = provider
        
    async def handle_user_registered(self, payload):
        logger.info(f"NotificationService processing UserRegistered: {payload}")
        email = payload.get("email")
        if email:
            # Here we'd load a Jinja template
            html = f"<h1>Welcome to Visoora</h1><p>Train your AI sales team.</p><a href='https://app.visoora.com'>Continue Setup</a>"
            self.provider.send_email(email, "Welcome to Visoora", html)
            
    async def handle_approval_required(self, payload):
        logger.info(f"NotificationService processing ApprovalRequired: {payload}")
        email = payload.get("email", "ceo@visoora.com") # Mock default
        mission_name = payload.get("mission_name", "Mission")
        count = payload.get("count", 1)
        html = f"<h1>{count} AI-generated emails are waiting for your approval</h1><a href='https://app.visoora.com/inbox'>Review Approvals</a>"
        self.provider.send_email(email, f"Action Required: Approve {mission_name} drafts", html)
        
    async def handle_meeting_booked(self, payload):
        logger.info(f"NotificationService processing MeetingBooked: {payload}")
        email = payload.get("email", "ceo@visoora.com")
        company = payload.get("company", "Unknown")
        person = payload.get("person", "Unknown")
        value = payload.get("value", "$0")
        
        html = f"<h1>🎉 Your AI booked another meeting</h1><p>Company: {company}</p><p>Person: {person}</p><p>Expected Deal: {value}</p><a href='https://calendar.google.com'>Open Calendar</a>"
        self.provider.send_email(email, f"Meeting Booked with {company}", html)

# Global Instance
provider = ResendProvider(api_key=os.getenv("RESEND_API_KEY"))
notification_service = NotificationService(provider)

def setup_notifications():
    """Register NotificationService with the EventBus"""
    from server.events.bus import bus
    bus.subscribe("UserRegistered", notification_service.handle_user_registered)
    bus.subscribe("ApprovalRequired", notification_service.handle_approval_required)
    bus.subscribe("MeetingBooked", notification_service.handle_meeting_booked)
    logger.info("NotificationService subscribed to EventBus")

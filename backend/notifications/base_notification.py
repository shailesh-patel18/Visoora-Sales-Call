from abc import ABC, abstractmethod
from typing import Dict, Any

class NotificationProvider(ABC):
    """
    Abstract Base Class for all notification mechanisms (Email, SMS, In-App).
    Ensures a consistent interface for the Celery workers to alert users.
    """
    
    @abstractmethod
    async def notify(self, user_id: str, recipient: str, template: str, data: Dict[str, Any]) -> bool:
        """
        Send a notification to a specific user/recipient.
        
        Args:
            user_id: The Visoora internal user_id.
            recipient: The email address, phone number, etc.
            template: The template identifier (e.g. 'draft_approved', 'mission_completed').
            data: Contextual data to inject into the template.
            
        Returns:
            bool: True if sent successfully, False otherwise.
        """
        pass

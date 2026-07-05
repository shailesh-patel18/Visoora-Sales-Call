from abc import ABC, abstractmethod
from typing import List, Dict, Any

class IAgentMemory(ABC):
    """
    Hexagonal Port for Agent Memory.
    Agents use this to retrieve past context and store new observations.
    """
    
    @abstractmethod
    def add_message(self, role: str, content: str):
        pass
        
    @abstractmethod
    def add_observation(self, key: str, value: Any):
        pass
        
    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        pass
        
    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        pass

class ConversationMemory(IAgentMemory):
    """
    Standard short-term memory adapter for an agent session.
    """
    def __init__(self):
        self._messages: List[Dict[str, str]] = []
        self._context: Dict[str, Any] = {}
        
    def add_message(self, role: str, content: str):
        self._messages.append({"role": role, "content": content})
        
    def add_observation(self, key: str, value: Any):
        self._context[key] = value
        
    def get_messages(self) -> List[Dict[str, str]]:
        return self._messages
        
    def get_context(self) -> Dict[str, Any]:
        return self._context

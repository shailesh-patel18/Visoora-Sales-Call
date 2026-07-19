from abc import ABC, abstractmethod
from typing import List, Dict, Any

class Capability(ABC):
    """
    Base capability interface.
    """
    pass

class EmailFinderCapability(Capability):
    """
    Capability to find email addresses.
    """
    @abstractmethod
    async def find_emails(self, name: str, company_domain: str) -> List[str]:
        pass

class CompanyDiscoveryCapability(Capability):
    """
    Capability to research and discover company information.
    """
    @abstractmethod
    async def research_company(self, company_name: str) -> Dict[str, Any]:
        pass

class PeopleDiscoveryCapability(Capability):
    """
    Capability to search and discover people (leads).
    """
    @abstractmethod
    async def find_leads(self, icp_segment: str, limit: int = 5) -> List[Dict[str, Any]]:
        pass

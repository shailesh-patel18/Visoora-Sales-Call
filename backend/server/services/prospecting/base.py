import abc
from typing import List, Dict, Any

class BaseProspectProvider(abc.ABC):
    """
    Abstract base class for all prospect sourcing providers.
    """
    
    @abc.abstractmethod
    async def search_prospects(self, tenant_id: str, business_brain: Dict[str, Any], max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for prospects based on the tenant's business brain configuration.
        Should return a list of standard Visoora contact dictionaries.
        """
        pass

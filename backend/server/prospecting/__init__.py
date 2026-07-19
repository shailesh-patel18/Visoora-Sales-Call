from .provider import ProspectProvider
from .capability import Capability, EmailFinderCapability, CompanyDiscoveryCapability, PeopleDiscoveryCapability
from .registry import global_capability_registry
from .scoring import ProviderScorer
from .apollo_provider import ApolloProvider
from .hunter_provider import HunterProvider
from .firecrawl_provider import FirecrawlProvider
from .linkedin_provider import LinkedInProvider
from .mock_provider import MockProvider

__all__ = [
    "ProspectProvider",
    "Capability",
    "EmailFinderCapability",
    "CompanyDiscoveryCapability",
    "PeopleDiscoveryCapability",
    "global_capability_registry",
    "ProviderScorer",
    "ApolloProvider",
    "HunterProvider",
    "FirecrawlProvider",
    "LinkedInProvider",
    "MockProvider"
]

import os
apollo_key = os.getenv("APOLLO_API_KEY", "")
hunter_key = os.getenv("HUNTER_API_KEY", "")
firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
linkedin_key = os.getenv("LINKEDIN_API_KEY", "")

# Initialize and register providers
MockProvider()
if apollo_key:
    ApolloProvider(api_key=apollo_key)
if hunter_key:
    HunterProvider(api_key=hunter_key)
if firecrawl_key:
    FirecrawlProvider(api_key=firecrawl_key)
if linkedin_key:
    LinkedInProvider(api_key=linkedin_key)

import os
import structlog
from .base import BaseProspectProvider
from .db import DBProspectProvider
from .apollo import ApolloProspectProvider

logger = structlog.get_logger("prospecting_factory")

def get_prospect_provider() -> BaseProspectProvider:
    """
    Returns the appropriate prospect provider based on environment configuration.
    Falls back to DBProspectProvider if APOLLO_API_KEY is not set.
    """
    apollo_key = os.getenv("APOLLO_API_KEY")
    
    if apollo_key and apollo_key.strip():
        logger.info("prospect_provider_initialized", provider="apollo")
        return ApolloProspectProvider(api_key=apollo_key.strip())
    else:
        logger.info("prospect_provider_initialized", provider="db_fallback")
        return DBProspectProvider()

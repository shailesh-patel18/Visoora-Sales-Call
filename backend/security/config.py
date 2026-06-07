import os
from typing import Set
from pydantic import BaseModel, Field

class SecuritySettings(BaseModel):
    """
    Settings definition for all security-related integrations including
    Supabase JWKS, Twilio webhooks, Redis rate limiting, and general M2M.
    """
    # Supabase Auth
    supabase_url: str = Field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_jwks_url: str = Field(default_factory=lambda: os.getenv(
        "SUPABASE_JWKS_URL", 
        f"{os.getenv('SUPABASE_URL', '').rstrip('/')}/auth/v1/jwks" if os.getenv("SUPABASE_URL") else ""
    ))
    
    # Twilio webhook signature verification
    twilio_auth_token: str = Field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", "your_twilio_auth_token_here"))
    
    # Redis config for tenant rate-limiter
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    
    # Machine-to-Machine keys
    api_key_header_name: str = "X-API-Key"
    system_api_keys: Set[str] = Field(default_factory=lambda: {
        k.strip() for k in os.getenv("SYSTEM_API_KEYS", "").split(",") if k.strip()
    })

# Instantiate singleton settings
settings = SecuritySettings()

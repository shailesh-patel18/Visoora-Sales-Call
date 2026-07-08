import os
from typing import List, Set
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables early so they are available when settings are instantiated
load_dotenv()


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
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", ""))

    # Runtime and deployment
    sentry_dsn: str = Field(default_factory=lambda: os.getenv("SENTRY_DSN", ""))
    anthropic_api_key: str = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    resend_api_key: str = Field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    app_env: str = Field(default_factory=lambda: os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower())
    server_public_domain: str = Field(default_factory=lambda: os.getenv("SERVER_PUBLIC_DOMAIN", ""))
    allowed_origins: List[str] = Field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ])
    max_active_calls_per_node: int = Field(default_factory=lambda: int(os.getenv("MAX_ACTIVE_CALLS_PER_NODE", "50")))
    max_transcript_turns_per_call: int = Field(default_factory=lambda: int(os.getenv("MAX_TRANSCRIPT_TURNS_PER_CALL", "300")))
    
    # Machine-to-Machine keys
    api_key_header_name: str = "X-API-Key"
    system_api_keys: Set[str] = Field(default_factory=lambda: {
        k.strip() for k in os.getenv("SYSTEM_API_KEYS", "").split(",") if k.strip()
    })

    def is_production(self) -> bool:
        return self.app_env in {"production", "prod"}

    def validate_for_startup(self) -> None:
        """
        Fail fast only for production deployments. Local and CI environments keep
        mock credentials enabled so tests and demos do not need paid services.
        """
        if not self.is_production():
            return

        errors = []
        if not self.server_public_domain:
            errors.append("SERVER_PUBLIC_DOMAIN is required in production.")
        if self.twilio_auth_token in {"", "your_twilio_auth_token_here", "mock"}:
            errors.append("TWILIO_AUTH_TOKEN must be configured in production.")
        if not os.getenv("TWILIO_ACCOUNT_SID") or os.getenv("TWILIO_ACCOUNT_SID") == "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX":
            errors.append("TWILIO_ACCOUNT_SID must be configured in production.")
        if not os.getenv("TWILIO_TRIAL_NUMBER"):
            errors.append("TWILIO_TRIAL_NUMBER must be configured in production.")
        if not self.redis_url:
            errors.append("REDIS_URL is required in production for rate limiting and session routing.")
        if not self.supabase_url:
            errors.append("SUPABASE_URL is required in production for authenticated dashboard access.")
        if not self.system_api_keys:
            errors.append("SYSTEM_API_KEYS should include at least one M2M key for production operations.")

        if errors:
            raise RuntimeError("Production startup validation failed: " + " ".join(errors))

# Instantiate singleton settings
settings = SecuritySettings()

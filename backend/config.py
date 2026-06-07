import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    twilio_account_sid: str = "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    twilio_auth_token: str = "your_twilio_auth_token_here"
    twilio_trial_number: str = "+15017122661"
    local_webrtc_mode: bool = True
    
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

TWILIO_ACCOUNT_SID = settings.twilio_account_sid
TWILIO_AUTH_TOKEN = settings.twilio_auth_token
TWILIO_TRIAL_NUMBER = settings.twilio_trial_number
LOCAL_WEBRTC_MODE = settings.local_webrtc_mode

import hmac
import hashlib
import base64
from fastapi import Request, Depends
from twilio.request_validator import RequestValidator
from security.config import settings
from security.errors import AuthenticationException
from security.logging import logger

async def verify_twilio_signature(request: Request) -> bool:
    """
    Enforces incoming request authenticity checks by validating the X-Twilio-Signature.
    Resolves reverse proxy/tunnel (ngrok, localtunnel) protocol and host mismatches.
    Supports standard HMAC-SHA1 (Twilio default) and explicit HMAC-SHA256 validation.
    """
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        logger.error("twilio_auth_missing_header", message="X-Twilio-Signature header is missing.")
        raise AuthenticationException("Forbidden: Missing Twilio signature.")
        
    # Resolve absolute URL dynamically to handle proxy tunnels
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    
    # Twilio signature uses the exact URL that Twilio called (which includes any query params)
    query_string = f"?{request.url.query}" if request.url.query else ""
    absolute_url = f"{proto}://{host}{request.url.path}{query_string}"
    
    # Load POST form parameters
    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}
    
    token = settings.twilio_auth_token
    
    # Local/Mock Validation bypass for test accounts
    if token == "your_twilio_auth_token_here" or token == "mock":
        logger.info("twilio_auth_mock", message="Twilio Auth Token unconfigured. Signature verification mocked.")
        return True

    # 1. Attempt standard HMAC-SHA256 validation (User specification)
    try:
        # Sort and concatenate all POST parameters alphabetically
        sorted_params = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        data = absolute_url + sorted_params
        
        # Calculate HMAC-SHA256
        computed_sha256 = hmac.new(
            token.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256
        ).digest()
        expected_sha256 = base64.b64encode(computed_sha256).decode("utf-8")
        
        if hmac.compare_digest(expected_sha256, signature):
            logger.info("twilio_auth_sha256_success", message="Twilio signature verified via HMAC-SHA256.")
            return True
    except Exception as e:
        logger.error("twilio_auth_sha256_failed", message="HMAC-SHA256 signature verification errored.", error=str(e))

    # 2. Fallback to Twilio library standard HMAC-SHA1 validator
    try:
        validator = RequestValidator(token)
        # Twilio request validation helper
        if validator.validate(absolute_url, params, signature):
            logger.info("twilio_auth_sha1_success", message="Twilio signature verified via HMAC-SHA1.")
            return True
    except Exception as e:
        logger.error("twilio_auth_sha1_failed", message="HMAC-SHA1 standard verification failed.", error=str(e))
        
    logger.error("twilio_auth_signature_mismatch", message="Twilio signature signature validation failed mismatch.", url=absolute_url)
    raise AuthenticationException("Forbidden: Invalid Twilio signature.")

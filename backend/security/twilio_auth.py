import os
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

    Validation order:
      1. HMAC-SHA256 via `X-Twilio-Signature-256` header (advanced Twilio accounts)
      2. HMAC-SHA1  via `X-Twilio-Signature` header  (standard Twilio HMAC-SHA1)

    Mock bypass: ONLY active when `TWILIO_AUTH_TOKEN` is the placeholder value AND
    `APP_ENV` is 'test'. This prevents the bypass from leaking into development or
    production environments — a critical security hardening from the executive audit.
    """
    token = settings.twilio_auth_token

    # ─────────────────────────────────────────────────────────────────────────
    # MOCK BYPASS — strictly test-only
    # Scope is intentionally narrow: only the literal placeholder token value
    # AND APP_ENV=test are both required. Setting APP_ENV=development will NOT
    # trigger this bypass, preventing accidental test-mode exposure in staging.
    # ─────────────────────────────────────────────────────────────────────────
    is_placeholder_token = token in ("your_twilio_auth_token_here", "mock", "")
    app_env = os.getenv("APP_ENV", "production").lower()
    if is_placeholder_token and app_env == "test":
        logger.info("twilio_auth_mock", message="Twilio signature verification bypassed (APP_ENV=test + placeholder token).")
        return True
    if is_placeholder_token and app_env != "test":
        logger.error(
            "twilio_auth_unconfigured_token",
            message=(
                f"SECURITY ALERT: TWILIO_AUTH_TOKEN is unconfigured placeholder but APP_ENV='{app_env}'. "
                "Signature verification will proceed and will fail. "
                "Set a real TWILIO_AUTH_TOKEN for this environment."
            )
        )
        # Fall through to full verification (will raise AuthenticationException)

    # Resolve absolute URL dynamically to handle proxy tunnels
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"

    # Twilio signature uses the exact URL that Twilio called (including any query params)
    query_string = f"?{request.url.query}" if request.url.query else ""
    absolute_url = f"{proto}://{host}{request.url.path}{query_string}"

    # Load POST form parameters
    form_data = await request.form()
    params = {k: v for k, v in form_data.items()}

    # ─────────────────────────────────────────────────────────────────────────
    # PATH 1: HMAC-SHA256 (X-Twilio-Signature-256 header — advanced accounts)
    # Twilio sends this as a SEPARATE header from the standard SHA1 signature.
    # ─────────────────────────────────────────────────────────────────────────
    sha256_signature = request.headers.get("X-Twilio-Signature-256")
    if sha256_signature:
        try:
            sorted_params = "".join(f"{k}{v}" for k, v in sorted(params.items()))
            data = absolute_url + sorted_params
            computed = hmac.new(
                token.encode("utf-8"),
                data.encode("utf-8"),
                hashlib.sha256
            ).digest()
            expected = base64.b64encode(computed).decode("utf-8")
            if hmac.compare_digest(expected, sha256_signature):
                logger.info("twilio_auth_sha256_success", message="Twilio signature verified via HMAC-SHA256.")
                return True
            logger.error("twilio_auth_sha256_mismatch", message="HMAC-SHA256 signature mismatch.", url=absolute_url)
        except Exception as e:
            logger.error("twilio_auth_sha256_error", message="HMAC-SHA256 verification raised exception.", error=str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # PATH 2: HMAC-SHA1 via Twilio official RequestValidator (standard)
    # This is the primary verification path for all standard Twilio accounts.
    # ─────────────────────────────────────────────────────────────────────────
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        logger.error("twilio_auth_missing_header", message="Both X-Twilio-Signature and X-Twilio-Signature-256 headers are absent.")
        raise AuthenticationException("Forbidden: Missing Twilio signature.")

    try:
        validator = RequestValidator(token)
        if validator.validate(absolute_url, params, signature):
            logger.info("twilio_auth_sha1_success", message="Twilio signature verified via HMAC-SHA1.")
            return True
    except Exception as e:
        logger.error("twilio_auth_sha1_error", message="HMAC-SHA1 verification raised exception.", error=str(e))

    logger.error("twilio_auth_signature_mismatch", message="All Twilio signature validation paths failed.", url=absolute_url)
    raise AuthenticationException("Forbidden: Invalid Twilio signature.")


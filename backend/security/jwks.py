import time
import httpx
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError, InvalidTokenError
from jwt.algorithms import RSAAlgorithm
from typing import Any, Dict, Optional
from security.config import settings
from security.errors import AuthenticationException
from security.logging import logger

class JWKService:
    """
    Asynchronously manages fetching, parsing, and caching Supabase Auth JWK signatures.
    Implements TTL in-memory caching and auto-refreshes on cache misses to handle key rotation.
    """
    def __init__(self, jwks_url: str, cache_ttl_seconds: int = 3600):
        self.jwks_url = jwks_url
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # In-memory key registry: kid -> cryptography PublicKey
        self.public_keys: Dict[str, Any] = {}
        self.last_fetched: float = 0.0

    async def get_public_key(self, kid: str) -> Any:
        """
        Retrieves public key for a given Key ID.
        Fetches JWKS from endpoint if cache is empty, expired, or on kid cache miss.
        """
        now = time.time()
        
        # Check cache expiration or cache miss
        if not self.public_keys or (now - self.last_fetched > self.cache_ttl_seconds) or (kid not in self.public_keys):
            logger.info("jwks_cache_refresh", message="Refreshing JWKS keys from Supabase...", kid=kid)
            await self._fetch_jwks()
            
        if kid not in self.public_keys:
            # Try once more by forcing reload
            logger.warn("jwks_kid_miss_reload", message="Forcing reload on JWKS key ID miss.", kid=kid)
            await self._fetch_jwks()
            if kid not in self.public_keys:
                raise AuthenticationException("Unknown token signature key identifier (KID).")
                
        return self.public_keys[kid]

    async def _fetch_jwks(self):
        """
        Sends async HTTP request to Supabase JWKS endpoint and parses the public keys.
        """
        if not self.jwks_url:
            # Fallback for local testing or unconfigured Supabase Url
            logger.warn("jwks_url_unconfigured", message="Supabase JWKS URL is unconfigured. Key fetching skipped.")
            return

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                headers = {}
                if getattr(settings, 'supabase_key', None):
                    headers["apikey"] = settings.supabase_key
                    headers["Authorization"] = f"Bearer {settings.supabase_key}"
                
                response = await client.get(self.jwks_url, headers=headers)
                if response.status_code != 200:
                    logger.error("jwks_fetch_http_error", message="Failed to fetch JWKS from Supabase.", status_code=response.status_code)
                    raise AuthenticationException("Internal system authentication failure (JWKS fetch error).")
                
                jwks_payload = response.json()
                keys = jwks_payload.get("keys", [])
                
                new_keys = {}
                for k in keys:
                    kid = k.get("kid")
                    if kid:
                        # Translate standard JWK dictionary directly to PEM/PublicKey format
                        public_key = RSAAlgorithm.from_jwk(k)
                        new_keys[kid] = public_key
                        
                self.public_keys = new_keys
                self.last_fetched = time.time()
                logger.info("jwks_keys_registered", message="Supabase public keys cached successfully.", count=len(new_keys))
        except Exception as e:
            logger.error("jwks_fetch_exception", message="Unhandled exception fetching JWKS.", error=str(e))
            raise AuthenticationException("System authentication layer is temporarily unavailable.")

# Instantiate global JWK registry service
jwk_service = JWKService(jwks_url=settings.supabase_jwks_url)

async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Validates a Supabase-issued Bearer JWT by querying the Gotrue server directly 
    using the Supabase Admin Client. This bypasses the need for a JWKS endpoint 
    which is not exposed in standard Supabase projects.
    """
    # ── Development & Testing Fallback ──────────────────────────────
    if settings.app_env in ("development", "test"):
        try:
            payload = jwt.decode(
                token,
                "mock_secret_key_visoora_auth",
                algorithms=["HS256"],
                audience="authenticated"
            )
            return payload
        except Exception:
            pass

    try:
        from server.storage_manager import supabase_admin_client
        # supabase.auth.get_user(token) securely verifies the token via network request to Gotrue
        user_resp = supabase_admin_client.auth.get_user(token)
        if not user_resp or not user_resp.user:
            raise AuthenticationException("Invalid or expired session.")
            
        user = user_resp.user
        
        # Reconstruct the payload dictionary expected by RBAC
        return {
            "sub": user.id,
            "email": user.email,
            "app_metadata": user.app_metadata or {},
            "user_metadata": user.user_metadata or {},
            "role": user.role
        }

    except Exception as e:
        logger.error("jwt_verification_unknown_error", message="Unhandled exception verifying token via Supabase get_user.", error=str(e))
        raise AuthenticationException("Authentication processing error.")

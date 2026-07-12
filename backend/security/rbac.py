import os
import socket
from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional, Set
from security.config import settings
from security.errors import AuthenticationException, AuthorizationException
from security.jwks import verify_supabase_jwt
from security.logging import logger, tenant_id_var

# Setup standard bearer token and header dependencies
bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name=settings.api_key_header_name, auto_error=False)

class UserPrincipal(BaseModel):
    """
    Data model representing the authenticated entity (either a human User or a machine Client).
    """
    user_id: str = Field(..., description="Unique identification UUID.")
    email: str = Field(..., description="Primary contact address or client identifier.")
    role: str = Field(..., description="Assigned RBAC access privileges: admin, agent, or viewer.")
    tenant_id: str = Field(..., description="Assigned multi-tenant isolation context.")
    is_m2m: bool = Field(default=False, description="Flag indicating if the call is machine-to-machine.")
    raw_token: Optional[str] = Field(default=None, description="The raw JWT token used for authentication.")

async def get_current_user(
    request: Request,
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_scheme)
) -> UserPrincipal:
    """
    Validates credentials (either a Supabase JWT or a system API key) to establish the UserPrincipal.
    Generates dynamic tenant isolation bindings.
    """
    user_principal: Optional[UserPrincipal] = None
    
    # 1. Inspect Machine-to-Machine System API Keys
    if api_key:
        if api_key in settings.system_api_keys:
            # Map standard system client principal (M2M has admin rights)
            user_principal = UserPrincipal(
                user_id="m2m_system_client",
                email="system@visoora.m2m",
                role="admin",
                tenant_id="global_system_tenant",
                is_m2m=True,
                raw_token=None
            )
            logger.info("m2m_auth_success", message="Authenticated via system M2M API Key.", tenant_id=user_principal.tenant_id)
        else:
            logger.warn("m2m_auth_failure", message="Invalid M2M API Key presented.")
            raise AuthenticationException("Invalid or expired API Key.")
            
    # 2. Inspect Bearer JWT Auth Token (from header or query param)
    elif bearer or request.query_params.get("token"):
        token = bearer.credentials if bearer else request.query_params.get("token")
        
        # Verify and parse signature keys from Supabase JWKS
        jwt_payload = await verify_supabase_jwt(token)
        
        # Extract metadata
        user_id = jwt_payload.get("sub", "")
        email = jwt_payload.get("email", "")
        
        # Parse Roles from standard GoTrue JWT configurations
        app_metadata = jwt_payload.get("app_metadata", {})
        user_metadata = jwt_payload.get("user_metadata", {})
        
        # Look across claims for a role
        role = (
            jwt_payload.get("role") or 
            app_metadata.get("role") or 
            user_metadata.get("role") or 
            app_metadata.get("roles", ["viewer"])[0] or 
            "viewer"
        )
        
        # Resolve Tenant ID (extract direct claim only)
        tenant_id = (
            jwt_payload.get("tenant_id") or 
            app_metadata.get("tenant_id") or 
            user_metadata.get("tenant_id")
        )
        if not tenant_id:
            # Enforce strict multi-tenancy: deny access if no explicit tenant UUID is present
            logger.warn("missing_tenant_id", message="Token lacks a valid tenant_id claim.", user_id=user_id)
            raise AuthenticationException("Valid tenant_id claim is required for access.")
                
        user_principal = UserPrincipal(
            user_id=user_id,
            email=email,
            role=role,
            tenant_id=tenant_id,
            is_m2m=False,
            raw_token=token
        )
        
    else:
        # All requests must provide valid credentials, regardless of environment.
        host = request.headers.get("host", "")
        logger.warn(
            "credentials_missing",
            message="No valid authorization token or API key provided.",
            app_env=settings.app_env,
            host=host
        )
        raise AuthenticationException("Authentication required. Please provide a Bearer JWT or API Key.")

    # Bind active Tenant ID to thread context variables dynamically
    tenant_id_var.set(user_principal.tenant_id)
    
    return user_principal

class RoleChecker:
    """
    FastAPI security dependency enforcing RBAC role checks.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserPrincipal = Depends(get_current_user)) -> UserPrincipal:
        """
        Dependency injection entrypoint. Compares user role against allowed list.
        """
        if not user:
            raise AuthenticationException("Credentials are required to access this endpoint.")
            
        if user.role not in self.allowed_roles:
            logger.warn(
                "rbac_access_denied", 
                message="Role unauthorized for endpoint.", 
                user_role=user.role, 
                allowed_roles=self.allowed_roles,
                user_id=user.user_id,
                tenant_id=user.tenant_id
            )
            raise AuthorizationException(f"Forbidden: role '{user.role}' lacks permissions. Required: {self.allowed_roles}")
            
        return user

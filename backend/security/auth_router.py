import os
import json
import uuid
import datetime
import jwt
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from security.rbac import get_current_user, UserPrincipal
from security.config import settings

import structlog
logger = structlog.get_logger("visoora_auth")

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

LOCAL_USERS_FILE = "recordings/local_auth_users.json"
MOCK_JWT_SECRET = "mock_secret_key_visoora_auth"

class AuthPayload(BaseModel):
    email: str
    password: str

class SignupPayload(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: Optional[str] = "admin"  # Default role for new signups

class ResetPasswordPayload(BaseModel):
    email: str

def _load_local_users() -> list:
    if os.path.exists(LOCAL_USERS_FILE):
        try:
            with open(LOCAL_USERS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def _save_local_users(users: list):
    os.makedirs("recordings", exist_ok=True)
    try:
        with open(LOCAL_USERS_FILE, "w") as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error("local_users_save_failed", error=str(e))

def generate_mock_token(user_id: str, email: str, role: str, tenant_id: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "tenant_id": tenant_id,
        "aud": "authenticated",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, MOCK_JWT_SECRET, algorithm="HS256")

# ----------------------------------------------------
# 1. POST /auth/signup
# ----------------------------------------------------
@auth_router.post("/signup")
async def signup_user(payload: SignupPayload):
    """
    Proxies user registration to Supabase Auth.
    Falls back to local user registry in development/testing mode when offline.
    """
    from server.storage_manager import supabase_client
    
    # Check if Supabase client is active
    if supabase_client:
        try:
            # Check if domain-based tenant_id or UUID
            # For real Supabase, tenant_id can be domain-based or a generated UUID
            tenant_id = payload.email.split("@")[1] if "@" in payload.email else "default_shared_tenant"
            # Attempt to register on Supabase Auth
            auth_response = supabase_client.auth.sign_up({
                "email": payload.email,
                "password": payload.password,
                "options": {
                    "data": {
                        "full_name": payload.full_name,
                        "company_name": payload.company_name,
                        "role": payload.role,
                        "tenant_id": tenant_id
                    }
                }
            })
            logger.info("supabase_signup_success", email=payload.email)
            return {
                "success": True,
                "message": "User registered successfully. Please verify your email.",
                "user": {
                    "id": auth_response.user.id if auth_response.user else None,
                    "email": payload.email,
                    "tenant_id": tenant_id,
                    "role": payload.role
                }
            }
        except Exception as e:
            logger.error("supabase_signup_failed", email=payload.email, error=str(e))
            raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

    # ── Dev Fallback (Supabase offline or app_env=development) ─────────────────────────
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is currently offline.")

    users = _load_local_users()
    if any(u["email"] == payload.email for u in users):
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    user_id = str(uuid.uuid4())
    tenant_id = payload.email.split("@")[1] if "@" in payload.email else "default_shared_tenant"
    
    new_user = {
        "id": user_id,
        "email": payload.email,
        "password": payload.password, # Plaintext for simple mock validation in local mode
        "full_name": payload.full_name,
        "company_name": payload.company_name,
        "role": payload.role,
        "tenant_id": tenant_id,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    users.append(new_user)
    _save_local_users(users)
    
    logger.info("local_signup_success", email=payload.email, tenant_id=tenant_id)
    return {
        "success": True,
        "message": "Registration complete (development mock). You can now log in.",
        "user": {
            "id": user_id,
            "email": payload.email,
            "tenant_id": tenant_id,
            "role": payload.role
        }
    }

# ----------------------------------------------------
# 2. POST /auth/login
# ----------------------------------------------------
@auth_router.post("/login")
async def login_user(payload: AuthPayload):
    """
    Validates credentials against Supabase GoTrue Auth.
    Falls back to local user registry in development/testing mode when offline.
    """
    from server.storage_manager import supabase_client
    
    if supabase_client:
        try:
            auth_response = supabase_client.auth.sign_in_with_password({
                "email": payload.email,
                "password": payload.password
            })
            if auth_response.session:
                token = auth_response.session.access_token
                refresh = auth_response.session.refresh_token
                user_data = auth_response.user
                
                # Fetch metadata
                meta = user_data.user_metadata if user_data else {}
                role = meta.get("role", "viewer")
                tenant_id = meta.get("tenant_id") or (payload.email.split("@")[1] if "@" in payload.email else "default_shared_tenant")
                
                logger.info("supabase_login_success", email=payload.email)
                return {
                    "access_token": token,
                    "refresh_token": refresh,
                    "token_type": "bearer",
                    "user": {
                        "id": user_data.id if user_data else None,
                        "email": payload.email,
                        "name": meta.get("full_name", payload.email.split("@")[0].capitalize()),
                        "role": role,
                        "tenant_id": tenant_id
                    }
                }
        except Exception as e:
            logger.error("supabase_login_failed", email=payload.email, error=str(e))
            raise HTTPException(status_code=401, detail="Invalid email or password.")

    # ── Dev Fallback (Supabase offline or app_env=development) ─────────────────────────
    if settings.app_env not in ("development", "test"):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication service is currently offline.")
    # Admin fallback user always allowed
    if payload.email == "admin@visoora.com" and payload.password == "Visoora@2024":
        token = generate_mock_token("local_admin_id", payload.email, "admin", "acme_tenant")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": "local_admin_id",
                "email": payload.email,
                "name": "Admin User",
                "role": "admin",
                "tenant_id": "acme_tenant"
            }
        }

    # Verify against local JSON users
    users = _load_local_users()
    for u in users:
        if u["email"] == payload.email and u["password"] == payload.password:
            token = generate_mock_token(u["id"], u["email"], u["role"], u["tenant_id"])
            logger.info("local_login_success", email=payload.email)
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": u["id"],
                    "email": u["email"],
                    "name": u["full_name"],
                    "role": u["role"],
                    "tenant_id": u["tenant_id"]
                }
            }

    raise HTTPException(status_code=401, detail="Invalid email or password.")

# ----------------------------------------------------
# 3. POST /auth/logout
# ----------------------------------------------------
@auth_router.post("/logout")
async def logout_user(user: UserPrincipal = Depends(get_current_user)):
    """Logs out the active user."""
    from server.storage_manager import supabase_client
    if supabase_client and not user.user_id.startswith("local_"):
        try:
            supabase_client.auth.sign_out()
        except Exception:
            pass
    logger.info("auth_logout_success", user_id=user.user_id)
    return {"success": True, "message": "Logged out successfully."}

# ----------------------------------------------------
# 4. GET /auth/me
# ----------------------------------------------------
@auth_router.get("/me")
async def get_me(user: UserPrincipal = Depends(get_current_user)):
    """Returns the validated UserPrincipal of the caller."""
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id
    }

# ----------------------------------------------------
# 5. POST /auth/reset-password
# ----------------------------------------------------
@auth_router.post("/reset-password")
async def reset_password(payload: ResetPasswordPayload):
    """Triggers password reset flow."""
    from server.storage_manager import supabase_client
    if supabase_client:
        try:
            supabase_client.auth.reset_password_for_email(payload.email)
            return {"success": True, "message": "Password reset link sent to your email."}
        except Exception as e:
            logger.error("supabase_reset_password_failed", email=payload.email, error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
            
    # Mock fallback
    return {"success": True, "message": "Password reset link sent (development mock)."}

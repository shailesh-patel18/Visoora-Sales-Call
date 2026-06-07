from fastapi import Depends
from security.rbac import get_current_user, UserPrincipal

async def verify_jwt(user: UserPrincipal = Depends(get_current_user)) -> dict:
    """
    FastAPI dependency that verifies the JWT using the existing RBAC system
    and returns a dictionary payload to ensure backward compatibility with
    endpoints expecting a parsed token dictionary.
    """
    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "is_m2m": user.is_m2m
    }
